import aiohttp
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Message
from aiogram.fsm.context import FSMContext
import matplotlib.pyplot as plt
from io import BytesIO

from config import OPENWEATHER_API_KEY

async def get_temperature(city: str, api_key: str) -> float | None:
    """
    Возвращает текущую температуру (°C) для города.
    """
    if not api_key:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "ru",
    }

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    main = data.get("main") or {}
    temp = main.get("temp")
    try:
        return float(temp)
    except (TypeError, ValueError):
        return None


def calculate_water_goal(weight_kg: float, activity_min: int, temp_c: float | None) -> int:
    """
    Норма воды по формуле:
    Базовая норма=Вес×30 мл/кг 
    +500 мл  за каждые 30 минут активности.
    +500 мл  за жаркую погоду (> 25°C).
    """
    base = int(round(weight_kg * 30))
    activity_bonus = (activity_min // 30) * 500

    if temp_c is not None and temp_c > 25:
        heat_bonus = 500
    else:
        heat_bonus = 0
    
    return base + activity_bonus + heat_bonus

def calculate_calorie_goal_kcal(
    weight_kg: float,
    height_cm: int,
    age: int,
    activity_min: int,
) -> int:
    """
    Калории=10×Вес (кг)+6.25×Рост (см)−5×Возраст
    + 0-500 ккал в зависимости от уровня активности
    """
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age

    if activity_min < 15:
        activity_bonus = 0
    elif activity_min <= 30:
        activity_bonus = 150
    elif activity_min <= 60:
        activity_bonus = 300
    else:
        activity_bonus = 500

    return int(round(base + activity_bonus))


async def recalc_goals_for_user(user: dict) -> None:
    """
    Пересчитать цели и сохранить в user['profile'].
    """
    p = user["profile"]

    required = ["weight", "height", "age", "activity", "city"]
    if any(p.get(k) in (None, "") for k in required):
        return

    weight = p["weight"]
    height = p["height"]
    age = p["age"]
    activity = p["activity"]
    city = p["city"]

    temp_c = await get_temperature(city, OPENWEATHER_API_KEY)

    p["water_goal"] = calculate_water_goal(
        weight_kg=weight,
        activity_min=activity,
        temp_c=temp_c,
    )

    if p.get("calorie_goal_source") != "manual":
        p["calorie_goal"] = calculate_calorie_goal_kcal(
            weight_kg=weight,
            height_cm=height,
            age=age,
            activity_min=activity
        )
        p["calorie_goal_source"] = "auto"


async def save_profile(message: Message, state: FSMContext, user: dict):
    data = await state.get_data()

    user["profile"].update({
        "weight": data.get("weight"),
        "height": data.get("height"),
        "age": data.get("age"),
        "sex": data.get("sex"),
        "activity": data.get("activity"),
        "city": data.get("city"),
        "calorie_goal": data.get("calorie_goal"),
        "calorie_goal_source": data.get("calorie_goal_source"),
    })

    await recalc_goals_for_user(user)

    await state.clear()
    await message.answer("Профиль сохранён ✅", reply_markup=kb_remove())


async def get_food_info(product_name: str):
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "action": "process",
        "search_terms": product_name,
        "json": 1,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                return None

            data = await response.json()

    products = data.get("products", [])
    if not products:
        return None

    first_product = products[0]
    nutriments = first_product.get("nutriments", {})

    return {
        "name": first_product.get("product_name", "Неизвестно"),
        "calories": nutriments.get("energy-kcal_100g", 0),
    }


def is_profile_ready(p: dict) -> bool:
    return (
        p.get("weight") is not None and
        p.get("height") is not None and
        p.get("age") is not None and
        p.get("activity") is not None and
        p.get("city") and
        p.get("water_goal") is not None and
        p.get("calorie_goal") is not None
    )


def kb_sex() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="М"), KeyboardButton(text="Ж")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def kb_goal_choice() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Рассчитать автоматически")],
            [KeyboardButton(text="Ввести вручную")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def kb_remove() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def parse_int(s: str) -> int | None:
    try:
        return int(s.strip())
    except Exception:
        return None


def parse_float(s: str) -> float | None:
    try:
        return float(s.replace(",", ".").strip())
    except Exception:
        return None
    

def make_daily_progress_plot(
    water_pct: float,
    cal_pct: float,
    water_now_ml: float,
    water_goal_ml: float,
    cal_now: float,
    cal_goal: float,
) -> BytesIO:
    
    water_pct = max(0.0, min(1.0, water_pct))
    cal_pct   = max(0.0, min(1.0, cal_pct))

    water_goal_ml = max(0.0, water_goal_ml)
    cal_goal      = max(0.0, cal_goal)

    water_now_ml = max(0.0, water_now_ml)
    cal_now      = max(0.0, cal_now)

    fig, ax = plt.subplots(figsize=(4.5, 4.5))

    cal_color = "#FF7043"
    water_color = "#4FC3F7"
    bg_color = "#E0E0E0"

    ax.pie(
        [cal_pct, 1 - cal_pct],
        radius=1.0,
        startangle=90,
        colors=[cal_color, bg_color],
        wedgeprops=dict(width=0.25),
    )

    ax.pie(
        [water_pct, 1 - water_pct],
        radius=0.7,
        startangle=90,
        colors=[water_color, bg_color],
        wedgeprops=dict(width=0.25),
    )

    ax.set_title("Дневной прогресс", fontsize=13, pad=12)

    y1 = -1.10
    y2 = -1.28

    ax.text(-0.55, y1, "●", color=cal_color, fontsize=16, ha="right", va="center")
    ax.text(-0.52, y1, "Калории", fontsize=11, ha="left", va="center")

    ax.text(0.25, y1, "●", color=water_color, fontsize=16, ha="right", va="center")
    ax.text(0.28, y1, "Вода", fontsize=11, ha="left", va="center")

    ax.text(-0.45, y2, f"{int(cal_now)}/{int(cal_goal)} ккал",
            fontsize=11, ha="center", va="center")

    ax.text(0.45, y2, f"{water_now_ml/1000:.1f}/{water_goal_ml/1000:.1f} л",
            fontsize=11, ha="center", va="center")

    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
