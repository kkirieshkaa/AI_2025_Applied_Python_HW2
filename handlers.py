from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext

from states import ProfileForm, FoodForm

from utils import (
    save_profile,
    get_food_info,
    is_profile_ready,
    kb_sex,
    kb_goal_choice,
    kb_remove,
    parse_int,
    parse_float,
    make_daily_progress_plot
)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать! Я ваш бот.\n"
        "Команды:\n"
        "/start — начало работы\n"
        "/help — список команд\n"
        "/set_profile — настроить профиль\n"
        "/log_water — записать выпитую воду\n"
        "/log_food — записать прием пищи\n"
        "/log_workout — записать тренировку\n"
        "/check_progress — текущий прогресс по воде и калориям\n"
        "/profile — посмотреть профиль\n"
        "/plot — показать график прогресса"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — начало работы\n"
        "/help — список команд\n"
        "/set_profile — настроить профиль\n"
        "/log_water — записать выпитую воду\n"
        "/log_food — записать прием пищи\n"
        "/log_workout — записать тренировку\n"
        "/check_progress — текущий прогресс по воде и калориям\n"
        "/profile — посмотреть профиль\n"
        "/plot — показать график прогресса"
    )


@router.message(Command("set_profile"))
async def cmd_set_profile(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ProfileForm.weight)
    await message.answer("Введите ваш вес (в кг):", reply_markup=kb_remove())


@router.message(ProfileForm.weight)
async def step_weight(message: Message, state: FSMContext):
    w = parse_float(message.text or "")
    if w is None or not (30 <= w <= 250):
        await message.answer("Введите корректный вес (30–250).")
        return
    await state.update_data(weight=w)
    await state.set_state(ProfileForm.height)
    await message.answer("Введите ваш рост (в см):")


@router.message(ProfileForm.height)
async def step_height(message: Message, state: FSMContext):
    h = parse_int(message.text or "")
    if h is None or not (120 <= h <= 230):
        await message.answer("Введите корректный рост (120–230).")
        return
    await state.update_data(height=h)
    await state.set_state(ProfileForm.age)
    await message.answer("Введите ваш возраст:")


@router.message(ProfileForm.age)
async def step_age(message: Message, state: FSMContext):
    a = parse_int(message.text or "")
    if a is None or not (10 <= a <= 100):
        await message.answer("Введите корректный возраст (10–100).")
        return
    await state.update_data(age=a)
    await state.set_state(ProfileForm.sex)
    await message.answer("Выберите пол:", reply_markup=kb_sex())


@router.message(ProfileForm.sex)
async def step_sex(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    if txt == "М":
        sex = "M"
    elif txt == "Ж":
        sex = "F"
    else:
        await message.answer("Выберите пол кнопкой: М / Ж", reply_markup=kb_sex())
        return

    await state.update_data(sex=sex)
    await state.set_state(ProfileForm.activity)
    await message.answer("Сколько минут активности у вас в день?", reply_markup=kb_remove())


@router.message(ProfileForm.activity)
async def step_activity(message: Message, state: FSMContext):
    mins = parse_int(message.text or "")
    if mins is None or not (0 <= mins <= 600):
        await message.answer("Введите корректное количество минут (0–600).")
        return
    await state.update_data(activity=mins)
    await state.set_state(ProfileForm.city)
    await message.answer("В каком городе вы находитесь?")


@router.message(ProfileForm.city)
async def step_city(message: Message, state: FSMContext):
    city = (message.text or "").strip()

    await state.update_data(city=city)
    await state.set_state(ProfileForm.goal_choice)
    await message.answer(
        "Цель калорий: рассчитать автоматически или ввести вручную?",
        reply_markup=kb_goal_choice(),
    )


@router.message(ProfileForm.goal_choice)
async def step_goal_choice(message: Message, state: FSMContext, user: dict):
    choice = (message.text or "").strip()
    if choice == "Рассчитать автоматически":
        await state.update_data(calorie_goal=None, calorie_goal_source="auto")
        await save_profile(message, state, user)
        return

    if choice == "Ввести вручную":
        await state.set_state(ProfileForm.goal_manual)
        await message.answer("Введите цель калорий (ккал):", reply_markup=kb_remove())
        return

    await message.answer("Выберите вариант кнопкой.", reply_markup=kb_goal_choice())


@router.message(ProfileForm.goal_manual)
async def step_goal_manual(message: Message, state: FSMContext, user: dict):
    goal = parse_int(message.text or "")
    if goal is None or not (800 <= goal <= 6000):
        await message.answer("Введите корректное число (800–6000).")
        return
    await state.update_data(calorie_goal=goal, calorie_goal_source="manual")
    await save_profile(message, state, user)


@router.message(Command("profile"))
async def cmd_profile(message: Message, p: dict):
    if not is_profile_ready(p):
        await message.answer("Сначала настройте профиль командой /set_profile")
        return
    
    sex = p.get("sex")
    sex_text = "М" if sex == "M" else "Ж"

    await message.answer(
        "👤 Профиль:\n"
        f"Вес: {p.get('weight')} кг\n"
        f"Рост: {p.get('height')} см\n"
        f"Возраст: {p.get('age')}\n"
        f"Пол: {sex_text}\n"
        f"Активность: {p.get('activity')} минут в день\n"
        f"Город: {p.get('city')}\n"
        f"Цель по воде: {p.get('water_goal')} мл\n"
        f"Цель по калориям: {p.get('calorie_goal')} ккал\n"
    )


@router.message(Command("log_water"))
async def cmd_log_water(message: Message, command: CommandObject, user: dict, p: dict, d: dict):
    if not is_profile_ready(p):
        await message.answer("Сначала настройте профиль командой /set_profile")
        return

    if command.args is None:
        await message.answer("Использование: /log_water <мл>\nПример: /log_water 300")
        return
    
    try:
        amount_ml = int(command.args.strip())
    except ValueError:
        await message.answer("Введите число в мл после команды.\nПример: /log_water 300")
        return

    if amount_ml <=0 or amount_ml > 5000:
        await message.answer("Введите корректное число мл (до 5000 мл)")
        return
    
    d["logged_water"] += amount_ml

    water_goal = p.get("water_goal")
    left = max(0, water_goal - d["logged_water"])
    await message.answer(
        "💧 Вода записана!\n"
        f"Выпито: {d['logged_water']} мл из {water_goal} мл.\n"
        f"Осталось: {left} мл."
    )


@router.message(Command("log_workout"))
async def cmd_log_workout(message: Message, command: CommandObject, p: dict, d: dict):
    if not is_profile_ready(p):
        await message.answer("Сначала настройте профиль командой /set_profile")
        return

    if command.args is None:
        await message.answer(
            "Использование: /log_workout <тип> <минуты>\n"
            "Пример: /log_workout бег 30"
        )
        return

    try:
        workout_type, minutes_str = command.args.split(maxsplit=1)
        minutes = int(minutes_str)
    except ValueError:
        await message.answer(
            "Неверный формат.\n"
            "Пример: /log_workout бег 30"
        )
        return
    
    if minutes <= 0 or minutes > 300:
        await message.answer("Введите корректное время (1–300 минут).")
        return
    
    kcal_per_min = {
        "бег": 10,
        "ходьба": 4,
        "велосипед": 8,
        "силовая": 6,
    }.get(workout_type.lower(), 6)

    burned = minutes * kcal_per_min
    d["burned_calories"] += burned

    extra_water = (minutes // 30) * 200
    d["water_bonus"] += extra_water

    await message.answer(
        f"🏃 Тренировка записана!\n"
        f"Тип: {workout_type}\n"
        f"Время: {minutes} мин\n"
        f"Сожжено: {burned} ккал\n"
        f"Дополнительно: выпейте {extra_water} мл воды."
    )
    

@router.message(Command("log_food"))
async def cmd_log_food(message: Message, command: CommandObject, state: FSMContext, p: dict):
    if not is_profile_ready(p):
        await message.answer("Сначала настройте профиль командой /set_profile")
        return

    if command.args is None:
        await message.answer("Использование: /log_food <продукт>\nПример: /log_food банан")
        return

    query = command.args.strip()
    await message.answer("Ищу продукт в базе… 🍽️")

    result = await get_food_info(query)
    if result is None:
        await message.answer("Не удалось найти продукт")
        return
    name, kcal_per_100g = result["name"], result["calories"]
    
    await state.clear()
    await state.update_data(name=name, kcal_per_100g=kcal_per_100g)
    await state.set_state(FoodForm.grams)

    await message.answer(
    f"{name} — {kcal_per_100g:.1f} ккал на 100 г.\n""Сколько грамм вы съели?")


@router.message(FoodForm.grams)
async def step_food_grams(message: Message, state: FSMContext, d: dict):
    txt = (message.text or "").replace(",", ".").strip()
    try:
        grams = float(txt)
    except ValueError:
        await message.answer("Введите число граммов. Пример: 150")
        return

    if grams <= 0 or grams > 3000:
        await message.answer("Введите корректное количество граммов (до 3000).")
        return

    data = await state.get_data()
    kcal_per_100g = float(data["kcal_per_100g"])

    eaten_kcal = grams * kcal_per_100g / 100.0
    d["logged_calories"] += eaten_kcal

    await state.clear()

    await message.answer(
        f"Записано: {eaten_kcal:.1f} ккал ✅\n"
        f"Итого потреблено сегодня: {d['logged_calories']:.1f} ккал"
    )


@router.message(Command("check_progress"))
async def cmd_check_progress(message: Message, p: dict, d: dict):
    if not is_profile_ready(p):
        await message.answer("Сначала настройте профиль командой /set_profile")
        return
    
    water_goal = p.get("water_goal") +  d.get("water_bonus", 0)
    cal_goal = p.get("calorie_goal")

    logged_water = d.get("logged_water", 0)
    logged_cal = d.get("logged_calories", 0)
    burned_cal = d.get("burned_calories", 0)

    water_left = None
    if isinstance(water_goal, int):
        water_left = max(0, water_goal - logged_water)

    cal_left = None
    if isinstance(cal_goal, int):
        cal_left = max(0, cal_goal - logged_cal)
    
    balance = max(0, logged_cal - burned_cal)
    await message.answer(
        "📊 Прогресс:\n"
        "Вода:\n"
        f"- Выпито: {logged_water} мл из {water_goal} мл.\n"
        f"- Осталось: {water_left} мл.\n\n"
        "Калории:\n"
        f"- Потреблено: {logged_cal:.1f} ккал из {cal_goal} ккал.\n"
        f"- Сожжено: {burned_cal:.1f} ккал.\n"
        f"- Баланс: {balance:.1f} ккал.\n"
        f"- Осталось до цели: {cal_left:.1f} ккал.\n"
    )


@router.message(Command("plot"))
async def cmd_plot(message: Message, p: dict, d: dict):
    if not is_profile_ready(p):
        await message.answer("Сначала настройте профиль командой /set_profile")
        return

    water_goal = p["water_goal"] + d.get("water_bonus", 0)
    cal_goal = p["calorie_goal"]

    logged_water = d["logged_water"]
    balance_cal = max(0, d["logged_calories"] - d["burned_calories"])

    water_pct = min(1.0, logged_water / water_goal)
    cal_pct= min(1.0, balance_cal / cal_goal)

    img = make_daily_progress_plot(
    water_pct,
    cal_pct,
    logged_water,
    water_goal,
    balance_cal,
    cal_goal
    )

    await message.answer_photo(
        BufferedInputFile(img.read(), filename="progress.png"),
        caption="📊 Дневной прогресс"
    )


def setup_handlers(dp):
    dp.include_router(router)
