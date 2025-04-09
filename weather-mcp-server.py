from mcp.server.fastmcp import FastMCP
import httpx
import json
from typing import Any

# 初始化 MCP 服务器
mcp = FastMCP("WeatherServer")

# OpenWeather API 配置
OPEN_WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = "YOUR_API_KEY"  # 请替换为你自己的 OpenWeather API Key
USER_AGENT = "weather-app/1.0"

async def get_weather(city: str) -> dict[str, Any] | None:
    """
    从 OpenWeather API 获取天气信息。
    :param city: 城市名称（需要用英文，如Beijing）
    :return: 天气信息字典； 若出错返回包含 error 信息的字典。
    """
    params = {"q": city, "appid": API_KEY, "units": "metric", "lang": "zh_cn"}
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
      try:
        response = await client.get(OPEN_WEATHER_BASE_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
      except httpx.HTTPStatusError as e:
        return {"error": f"❌ HTTP 错误：{e.response.status_code} - {e.response.text}"}
      except Exception as e:
        return {"error": f"❌ 请求错误：{str(e)}"}

def format_weather(data: dict[str, Any] | str) -> str:
    """
    格式化天气信息为已读文本。
    :param data: 天气数据（可以是字典或 json 字符串）
    :return: 格式化后的天气信息字符串
    """
    # 如果 data 是字符串，尝试解析为 JSON
    if isinstance(data, str):
      try:
        data = json.loads(data)
      except json.JSONDecodeError:
        return "❌ 无法解析的天气数据:{e}"

    # 如果数据中包含错误信息，直接返回错误信息
    if "error" in data:
      return f"⚠️ {data['error']}"

    # 提取数据时做兼容处理
    city = data.get("name", "未知")
    country = data.get("sys", {}).get("country", "未知")
    temperature = data.get("main", {}).get("temp", "N/A")
    humidity = data.get("main", {}).get("humidity", "N/A")
    wind_speed = data.get("wind", {}).get("speed", "N/A")
    # weather 可能为空列表，设置默认字典
    weather_list = data.get("weather", [{}])
    desc = weather_list[0].get("description", "未知")

    # 格式化天气信息
    formatted_weather = f"🌍 城市：{city}, {country}\n" \
                        f"🌡️ 温度：{temperature}°C\n" \
                        f"💧 湿度：{humidity}%\n" \
                        f"💨 风速：{wind_speed} m/s\n" \
                        f"🌤 天气: {desc}\n"

    return formatted_weather

@mcp.tool()
async def query_weather(city: str) -> str:
    """
    输入指定城市的英文名称，查询该地区今日天气信息。
    :param city: 城市名称（需要用英文，如Beijing）
    :return: 格式化后的天气信息
    """
    weather_data = await get_weather(city)
    if weather_data is None:
      return "❌ 无法获取天气信息"

    return format_weather(weather_data)

if __name__ == "__main__":
  # 以标准 I/O 方式运行 MCP 服务器
  mcp.run(transport="stdio")