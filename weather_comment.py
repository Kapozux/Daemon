import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "").strip()
MOONSHOT_URL = "https://api.moonshot.cn/v1/chat/completions"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
MODEL_NAME = "kimi-k2.7-code-highspeed"


def get_city_coordinates(city: str):
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        r = requests.get(geo_url, params={"name": city, "count": 1}, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        if not results:
            return None
        return results[0]
    except Exception as e:
        print(f"获取城市坐标失败: {e}")
        return None


def get_weather(lat: float, lon: float):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,surface_pressure",
        "timezone": "auto",
    }
    try:
        r = requests.get(WEATHER_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"获取天气失败: {e}")
        return None


def weather_code_to_desc(code: int) -> str:
    codes = {
        0: "晴朗",
        1: " mostly clear",
        2: "部分多云",
        3: "阴天",
        45: "雾",
        48: "雾凇",
        51: "毛毛雨",
        53: "小雨",
        55: "中雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        80: "阵雨",
        81: "强阵雨",
        82: "暴雨",
        95: "雷雨",
        96: "雷雨伴冰雹",
        99: "强雷雨伴冰雹",
    }
    return codes.get(code, "未知天气")


def fetch_ai_comment(city: str, temp, humidity, desc: str, wind) -> str:
    if not MOONSHOT_API_KEY:
        return "（未配置 MOONSHOT_API_KEY，无法生成趣味点评）"
    prompt = (
        f"城市：{city}，当前天气：{desc}，温度 {temp}°C，湿度 {humidity}%，风速 {wind} km/h。\n"
        "请你用一句话给出一个轻松幽默、结合当下时事热点或生活场景的小评价，风格类似 Kimi 的机智短评。"
    )
    try:
        r = requests.post(
            MOONSHOT_URL,
            headers={
                "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 1,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"（AI 点评生成失败：{e}）"


def main():
    if len(sys.argv) > 1:
        city = " ".join(sys.argv[1:])
    else:
        city = input("请输入城市名（如 Beijing / Shanghai）：").strip()

    if not city:
        print("城市名不能为空")
        return

    geo = get_city_coordinates(city)
    if not geo:
        print(f"找不到城市：{city}，请检查拼写或换个城市试试。")
        return

    lat = geo["latitude"]
    lon = geo["longitude"]
    real_name = geo.get("name", city)
    country = geo.get("country", "")

    weather_data = get_weather(lat, lon)
    if not weather_data:
        print("天气数据获取失败，请稍后重试。")
        return

    current = weather_data.get("current", {})
    temp = current.get("temperature_2m", "N/A")
    humidity = current.get("relative_humidity_2m", "N/A")
    wind = current.get("wind_speed_10m", "N/A")
    pressure = current.get("surface_pressure", "N/A")
    code = current.get("weather_code", -1)
    desc = weather_code_to_desc(code)

    print("\n===== 天气结果 =====")
    print(f"城市：{real_name}" + (f"，{country}" if country else ""))
    print(f"天气：{desc}")
    print(f"温度：{temp}°C")
    print(f"湿度：{humidity}%")
    print(f"风速：{wind} km/h")
    print(f"气压：{pressure} hPa")

    print("\n===== AI 点评 =====")
    comment = fetch_ai_comment(real_name, temp, humidity, desc, wind)
    print(comment)


if __name__ == "__main__":
    main()
