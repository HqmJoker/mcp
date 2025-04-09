import asyncio
import os
import json
from typing import Optional
from contextlib import AsyncExitStack

from openai import OpenAI
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

class MCPClient:
  # 初始化信息
  def __init__(self):
    """ 初始化 MCP 客户端 """
    self.exit_stask = AsyncExitStack()
    self.openai_api_key = os.getenv("OPENAI_API_KEY")
    self.openai_base_url = os.getenv("BASE_URL")
    self.openai_model = os.getenv("MODEL")

    if not self.openai_api_key:
      raise ValueError("❌ 未找到 OpenAI API Key，请在 .env 文件中设置 OPENAI_API_KEY")

    self.client = OpenAI(api_key=self.openai_api_key, base_url=self.openai_base_url)

    if not self.client:
      raise ValueError("❌ 无法初始化 OpenAI 客户端，请检查配置")
  # 连接可用mcp工具
  async def connect_mcp_server(self, server_script_path: str):
    """ 连接到 MCP 服务器并列出可用的mcp工具 """
    is_python = server_script_path.endswith(".py")
    is_js = server_script_path.endswith(".js")
    if not is_python and not is_js:
      raise ValueError("❌ 不支持的服务器脚本格式，请使用 .py 或 .js 格式的文件")
    command = "python" if is_python else "node"
    server_params = StdioServerParameters(
      command=command,
      args=[server_script_path],
      env=None
    )

    # 启动 MCP 服务器并建立通信
    stdio_transport = await self.exit_stask.enter_async_context(
      stdio_client(server_params)
    )
    self.stdio, self.write = stdio_transport
    self.session = await self.exit_stask.enter_async_context(
      ClientSession(self.stdio, self.write)
    )

    await self.session.initialize()
    print("\n✅ 已连接到 MCP 服务器")

    # 列出可用的mcp工具
    tools = await self.session.list_tools()
    print("\n可用的mcp工具：", [tool.name for tool in tools])

  # 处理用户请求
  async def process_query(self, query: str) -> str:
    """ 使用大模型处理查询并调用可用的 MCP 工具 (Function Calling) """
    messages = [
      {"role": "user", "content": query}
    ]

    response = await self.session.list_tools()

    # 格式化为 OpenAI 可读工具列表
    available_tools = [{
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        }
    } for tool in response.tools]

    response = self.client.chat.completions.create(
        model=self.openai_model,            
        messages=messages,
        tools=available_tools     
    )

    # 处理返回的内容
    content = response.choices[0]
    # 如果返回的内容是函数调用，则调用函数
    if content.finish_reason == "tool_calls":
      tool_call = content.message.tool_calls[0]
      function_name = tool_call.function.name
      function_args = json.loads(tool_call.function.arguments)

      # 调用 MCP 工具
      tool_response = await self.session.call_tool(function_name, function_args)
      print(f"\n\n[Calling tool {tool_name} with args {tool_args}]\n\n")

      # 将模型返回的调用哪个工具数据和工具执行完成后的数据都存入messages中
      messages.append(content.message.model_dump())
      messages.append({
          "role": "tool",
          "content": tool_response.content[0].text,
          "tool_call_id": tool_call.id,
      })
      # 将上面的结果再返回给大模型用于生产最终的结果
      response = self.client.chat.completions.create(
          model=self.openai_model,
          messages=messages,
      )
      return response.choices[0].message.content
    
    return content.message.content

  async def chat_loop(self):
    """ 运行交互式聊天循环 """
    print("\nMCP 客户端已启动，输入 /quit 退出")

    while True:
      try :
        query = input("\n你: ").strip()
        if query.lower() == 'quit':
          break

        response = await self.process_query(query) # 用户发送消息到OpenAI
        print(f"\n🤖 OpenAI：{response}")

      except Exception as e:
        print(f"❌ 发生错误：{str(e)}")
  async def cleanup(self):
    """ 清理 MCP 客户端的资源 """
    await self.exit_stask.aclose()
    print("\n✅ MCP 客户端已关闭")    
async def main():
  if len(sys.argv) < 2:
    print("Usage: python client.py <path_to_server_script>")
    sys.exit(1)
  client = MCPClient()
  try :
    await client.connect_mcp_server(sys.argv[1])
    await client.chat_loop()
  finally :
    await client.cleanup()

if __name__ == "__main__":
  import sys
  asyncio.run(main())