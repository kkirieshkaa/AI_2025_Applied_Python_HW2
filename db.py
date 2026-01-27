from datetime import date

users: dict[int, dict] = {}

def get_user(user_id: int) -> dict:
    today = date.today().isoformat()

    if user_id not in users:
        users[user_id] = {
            "profile": {
                "weight": None,
                "height": None,
                "age": None,
                "sex": None,
                "activity": None,
                "city": None,
                "water_goal": None,
                "calorie_goal": None,
                "calorie_goal_source": None,
            },
            "daily": {
                "date": today,
                "logged_water": 0,
                "logged_calories": 0.0,
                "burned_calories": 0.0,
                "water_bonus": 0
            }
        }
        return users[user_id]

    if users[user_id]["daily"]["date"] != today:
        users[user_id]["daily"]["date"] = today
        users[user_id]["daily"]["logged_water"] = 0
        users[user_id]["daily"]["logged_calories"] = 0.0
        users[user_id]["daily"]["burned_calories"] = 0.0
        users[user_id]["daily"]["water_bonus"] = 0

    return users[user_id]
