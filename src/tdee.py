def calculate_tdee(weight_kg, height_cm, age, gender, activity_level):
    # Harris-Benedict BMR formula
    if gender == 'male':
        bmr = (10 * weight_kg + 
               6.25 * height_cm - 
               5 * age + 5)
    else:
        bmr = (10 * weight_kg + 
               6.25 * height_cm - 
               5 * age - 161)

    # Activity multipliers
    multipliers = {
        'sedentary': 1.2,       # desk job, no exercise
        'light': 1.375,          # light exercise 1-3 days
        'moderate': 1.55,        # moderate 3-5 days
        'active': 1.725,         # hard exercise 6-7 days
        'very_active': 1.9       # athlete, physical job
    }

    tdee = bmr * multipliers.get(activity_level, 1.55)

    return round(tdee)

def calculate_targets(tdee, goal):
    if goal == 'fat_loss':
        calories = tdee - 500      # 500 cal deficit
        protein_g = 2.2            # per kg bodyweight
        fat_percent = 0.25
    elif goal == 'muscle_gain':
        calories = tdee + 300      # 300 cal surplus
        protein_g = 2.0
        fat_percent = 0.25
    else:  # maintain
        calories = tdee
        protein_g = 1.8
        fat_percent = 0.25

    fat_calories = calories * fat_percent
    fat_g = round(fat_calories / 9)

    return {
        'calories': round(calories),
        'protein_g': protein_g,   # multiply by bodyweight
        'fat_g': fat_g,
        'carbs_g': round(
            (calories - (fat_g * 9)) / 4)  # remaining from carbs
    }