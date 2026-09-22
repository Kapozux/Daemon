import sys
import os
import urllib.request
import urllib.parse
import json


def get_weather(city: str):
    # 使用 Open-Meteo 免费 API，无需 key
    # 先用 geocoding API 把城市名转为经纬度
    geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode({
        "name": city,
        "count": 1,
        "language": "zh",
        "format": "json",
    })
    with urllib.request.urlopen(geo_url, timeout=10) as resp:
        geo_data = json.loads(resp.read().decode("utf-8"))

    if "results" not in geo_data or not geo_data["results"]:
        return None, f"找不到城市: {city}"

    loc = geo_data["results"][0]
    lat, lon = loc["latitude"], loc["longitude"]
    name = loc.get("name", city)
    country = loc.get("country", "")

    weather_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "timezone": "auto",
    })
    with urllib.request.urlopen(weather_url, timeout=10) as resp:
        w = json.loads(resp.read().decode("utf-8"))

    cur = w.get("current", {})
    return {
        "location": f"{name}, {country}".strip(", "),
        "temperature": cur.get("temperature_2m"),
        "humidity": cur.get("relative_humidity_2m"),
        "wind": cur.get("wind_speed_10m"),
        "code": cur.get("weather_code"),
        "time": cur.get("time"),
    }, None


WEATHER_CODES = {
    0: "晴", 1: "多云", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "小阵雨", 81: "阵雨", 82: "强阵雨",
    95: "雷暴", 96: "雷暴伴冰雹", 99: "强雷暴伴冰雹",
}


def format_weather(info):
    code = info.get("code")
    desc = WEATHER_CODES.get(code, f"未知({code})")
    return (
        f"📍 {info['location']}\n"
        f"🕐 时间: {info['time']}\n"
        f"🌡️ 温度: {info['temperature']}°C\n"
        f"💧 湿度: {info['humidity']}%\n"
        f"💨 风速: {info['wind']} km/h\n"
        f"☁️ 天气: {desc}\n"
    )


def main():
    if len(sys.argv) < 2:
        print("用法: python weather.py <城市名>")
        sys.exit(1)
    city = " ".join(sys.argv[1:])
    info, err = get_weather(city)
    if err:
        print(f"错误: {err}")
        sys.exit(2)
    print(format_weather(info))


if __name__ == "__main__":
    main()
