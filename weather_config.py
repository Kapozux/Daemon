import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "").strip()
MOONSHOT_URL = "https://api.moonshot.cn/v1/chat/completions"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
MODEL_NAME = "kimi-k2.7-code-highspeed"
