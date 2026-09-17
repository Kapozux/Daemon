import sys
from datetime import datetime

from weather_config import MODEL_NAME
from weather_geo import get_city_coordinates
from weather_data import fetch_weather, weather_code_to_desc
from weather_ai import fetch_ai_comment
from weather_cache import get_cache_key, get_from_cache, save_to_cache


def format_daily(daily: dict):
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    rain_probs = daily.get("precipitation_probability_max", [])

    lines = []
    for i in range(min(3, len(dates))):
        date_str = datetime.fromisoformat(dates[i]).strftime("%m月%d日")
        desc = weather_code_to_desc(codes[i])
        lines.append(
            f"  {date_str}: {desc}，{min_temps[i]}°C ~ {max_temps[i]}°C，降雨概率 {rain_probs[i]}%"
        )
    return lines


def main():
    if len(sys.argv) > 1:
        city = " ".join(sys.argv[1:])
    else:
        city = input("请输入城市名（如 Beijing / Shanghai）：").strip()

    if not city:
        print("城市名不能为空")
        return

    cache_key = get_cache_key("weather", city.lower())
    cached = get_from_cache(cache_key, ttl_seconds=600)
    if cached:
        print("\n（命中缓存）")
        print(cached)
        return

    geo = get_city_coordinates(city)
    if not geo:
        print(f"找不到城市：{city}，请检查拼写或换个城市试试。")
        return

    lat = geo["latitude"]
    lon = geo["longitude"]
    real_name = geo.get("name", city)
    country = geo.get("country", "")

    weather_data = fetch_weather(lat, lon)
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

    location = real_name + (f"，{country}" if country else "")
    output_lines = [
        "\n===== 天气结果 =====",
        f"城市：{location}",
        f"天气：{desc}",
        f"温度：{temp}°C",
        f"湿度：{humidity}%",
        f"风速：{wind} km/h",
        f"气压：{pressure} hPa",
        "\n===== 未来 3 天预报 =====",
    ]
    output_lines.extend(format_daily(weather_data.get("daily", {})))

    output_lines.append("\n===== AI 点评 =====")
    comment = fetch_ai_comment(real_name, temp, humidity, desc, wind)
    output_lines.append(f"整体感受：{comment.get('summary', '')}")
    output_lines.append(f"穿衣建议：{comment.get('clothing', '')}")
    output_lines.append(f"出行建议：{comment.get('activity', '')}")
    output_lines.append(f"今日金句：{comment.get('quote', '')}")

    output = "\n".join(output_lines)
    print(output)
    save_to_cache(cache_key, output)
    print(f"\n（当前使用模型：{MODEL_NAME}）")


if __name__ == "__main__":
    main()
