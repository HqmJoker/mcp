import asynico
from mcp import ClientSession
from contextlib import AsyncExitStack

class MCPClient:
    def __init__(self):
      """ 初始化 MCP 客户端 """
      self.session = None
      self.exit_stask = AsyncExitStack()

    async def connect(self):
      """ 连接到 MCP 服务器的连接 """
      print("✅ MCP 客户端已初始化，但未连接到服务器")

    async def chat_loop(self):
      """ 运行交互式聊天循环 """
      print("\nMCP 客户端已启动，输入 /quit 退出")

      while True:
        try :
          query = input("\nQuery: ").strip()
          if query.lower() == 'quit':
            break
          print(f"\n🤖 [Mock Response] 你说的是：{query}")
        except Exception as e:
          print(f"❌ 发生错误：{str(e)}")

    async def cleanup(self):
      """ 清理 MCP 客户端的资源 """
      await self.exit_stask.aclose()
      print("\n✅ MCP 客户端已关闭")    
async def main():
  client = MCPClient()
  try :
    await client.connect()
    await client.chat_loop()
  finally :
    await client.cleanup()

if __name__ == "__main__":
    asynico(main())