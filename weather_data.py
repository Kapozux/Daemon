import requests
from weather_config import WEATHER_URL


CURRENT_FIELDS = "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,surface_pressure"
DAILY_FIELDS = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"


def fetch_weather(lat: float, lon: float):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": CURRENT_FIELDS,
        "daily": DAILY_FIELDS,
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
        56: "冻毛毛雨",
        57: "强冻毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "冻雨",
        67: "强冻雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "阵雨",
        81: "强阵雨",
        82: "暴雨",
        85: "阵雪",
        86: "强阵雪",
        95: "雷雨",
        96: "雷雨伴冰雹",
        99: "强雷雨伴冰雹",
    }
    return codes.get(code, "未知天气")
