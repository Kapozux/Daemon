import json
import requests
from weather_config import MOONSHOT_API_KEY, MOONSHOT_URL, MODEL_NAME


def fetch_ai_comment(city: str, temp, humidity, desc: str, wind) -> dict:
    if not MOONSHOT_API_KEY:
        return {"summary": "未配置 MOONSHOT_API_KEY，无法生成 AI 点评", "clothing": "", "activity": "", "quote": ""}

    prompt = (
        f"城市：{city}，当前天气：{desc}，温度 {temp}°C，湿度 {humidity}%，风速 {wind} km/h。\n"
        "请用中文生成一段结构化的天气点评，包含四个字段，严格以 JSON 格式输出，不要有多余说明：\n"
        "summary: 一句话概括今天天气给人的整体感受；\n"
        "clothing: 根据天气给出穿衣建议；\n"
        "activity: 根据天气给出出行/活动建议；\n"
        "quote: 一句轻松幽默、结合生活场景的金句，风格类似 Kimi 的机智短评。\n"
        "输出示例：{\"summary\":\"...\",\"clothing\":\"...\",\"activity\":\"...\",\"quote\":\"...\"}"
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
        content = r.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```json"):
            content = content.removeprefix("```json").removesuffix("```").strip()
        elif content.startswith("```"):
            content = content.removeprefix("```").removesuffix("```").strip()
        return json.loads(content)
    except Exception as e:
        return {"summary": f"AI 点评生成失败：{e}", "clothing": "", "activity": "", "quote": ""}
