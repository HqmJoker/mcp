import asyncio
from contextlib import AsyncExitStack
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
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

    async def process_query(self, query: str) -> str:
      """ 调用OpenAI 处理用户查询"""
      messages = [
        {"role": "system", "content": "你是一个智能助手，帮助用户回答问题。"},
        {"role": "user", "content": query}
      ]
      try:
        # 调用OpenAI API
        response = await asyncio.get_event_loop().run_in_executor(
          None,
          lambda: self.client.chat.completions.create(
            model=self.openai_model,
            messages=messages
          )
        )
        return response.choices[0].message.content
      except Exception as e:
        return f"❌ 调用 OpenAI API 出错：{str(e)}"
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
  client = MCPClient()
  try :
    await client.chat_loop()
  finally :
    await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())