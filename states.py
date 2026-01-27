from aiogram.fsm.state import State, StatesGroup

class ProfileForm(StatesGroup):
    weight = State()
    height = State()
    age = State()
    sex = State()
    activity = State()
    city = State()
    goal_choice = State()
    goal_manual = State()


class FoodForm(StatesGroup):
    grams = State()
