import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "").strip()
print("key loaded:", bool(MOONSHOT_API_KEY))

r = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": 39.9075,
        "longitude": 116.39723,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,surface_pressure",
        "timezone": "auto",
    },
    timeout=8,
)
print("weather:", r.json().get("current"))

prompt = "城市：Beijing，当前天气晴朗，温度25°C，湿度40%，风速10 km/h。请用一句话给出轻松幽默、结合当下时事或生活场景的小评价。"
r = requests.post(
    "https://api.moonshot.cn/v1/chat/completions",
    headers={"Authorization": f"Bearer {MOONSHOT_API_KEY}", "Content-Type": "application/json"},
    json={"model": "moonshot-v1-8k", "messages": [{"role": "user", "content": prompt}], "temperature": 0.9},
    timeout=20,
)
print("moonshot status:", r.status_code)
print("comment:", r.json()["choices"][0]["message"]["content"].strip())
