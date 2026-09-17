import requests
from weather_config import GEO_URL


def get_city_coordinates(city: str):
    try:
        r = requests.get(GEO_URL, params={"name": city, "count": 1}, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        if not results:
            return None
        return results[0]
    except Exception as e:
        print(f"获取城市坐标失败: {e}")
        return None
