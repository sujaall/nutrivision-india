from flask import Flask, render_template, request, jsonify, session
from predict import load_model, predict_food
from tdee import calculate_tdee, calculate_targets
from werkzeug.utils import secure_filename
import json, os
from datetime import datetime, date

app = Flask(__name__,
    template_folder='../templates',
    static_folder='../static')
app.secret_key = 'nutrivision2025secretkey'

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("Loading model...")
MODEL_PATH = os.path.join(
    BASE_DIR, 'models', 'nutrivision_model.pth')
model, class_names = load_model(MODEL_PATH)

DATA_PATH = os.path.join(
    BASE_DIR, 'data', 'indian_nutrition.json')
with open(DATA_PATH) as f:
    nutrition_db = json.load(f)

DIARY_PATH = os.path.join(BASE_DIR, 'data', 'food_diary.json')
PROFILE_PATH = os.path.join(
    BASE_DIR, 'data', 'user_profiles.json')

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/save_profile', methods=['POST'])
def save_profile():
    data = request.json
    user_id = data.get('user_id', 'default_user')
    profiles = load_json(PROFILE_PATH)

    tdee = calculate_tdee(
        data['weight'], data['height'],
        data['age'], data['gender'],
        data['activity'])

    targets = calculate_targets(tdee, data['goal'])
    targets['protein_g'] = round(
        targets['protein_g'] * data['weight'])

    profiles[user_id] = {
        'name': data['name'],
        'weight': data['weight'],
        'height': data['height'],
        'age': data['age'],
        'gender': data['gender'],
        'activity': data['activity'],
        'goal': data['goal'],
        'tdee': tdee,
        'targets': targets
    }
    save_json(PROFILE_PATH, profiles)
    return jsonify({
        'success': True,
        'tdee': tdee,
        'targets': targets
    })

@app.route('/api/get_profile/<user_id>')
def get_profile(user_id):
    profiles = load_json(PROFILE_PATH)
    profile = profiles.get(user_id, {})
    return jsonify(profile)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    predictions = predict_food(filepath, model, class_names)
    top_food = predictions[0]['food']
    nutrition = nutrition_db.get(top_food, {
        'calories_per_100g': 200,
        'protein': 5, 'carbs': 25, 'fat': 5,
        'health_score': 5,
        'notes': 'Nutrition data coming soon.'
    })
    return jsonify({
        'predictions': predictions,
        'nutrition': nutrition,
        'food_name': top_food
    })

@app.route('/api/log_meal', methods=['POST'])
def log_meal():
    data = request.json
    user_id = data.get('user_id', 'default_user')
    today = str(date.today())

    diary = load_json(DIARY_PATH)
    if user_id not in diary:
        diary[user_id] = {}
    if today not in diary[user_id]:
        diary[user_id][today] = []

    diary[user_id][today].append({
        'food': data['food'],
        'portion': data['portion'],
        'calories': data['calories'],
        'protein': data['protein'],
        'carbs': data['carbs'],
        'fat': data['fat'],
        'meal_type': data['meal_type'],
        'time': datetime.now().strftime('%H:%M')
    })
    save_json(DIARY_PATH, diary)

    # Calculate today totals
    totals = {'calories': 0, 'protein': 0,
               'carbs': 0, 'fat': 0}
    for entry in diary[user_id][today]:
        totals['calories'] += entry['calories']
        totals['protein'] += entry['protein']
        totals['carbs'] += entry['carbs']
        totals['fat'] += entry['fat']

    return jsonify({
        'success': True,
        'today_totals': totals
    })

@app.route('/api/get_diary/<user_id>')
def get_diary(user_id):
    diary = load_json(DIARY_PATH)
    today = str(date.today())
    today_entries = diary.get(
        user_id, {}).get(today, [])

    totals = {'calories': 0, 'protein': 0,
               'carbs': 0, 'fat': 0}
    for entry in today_entries:
        totals['calories'] += entry['calories']
        totals['protein'] += entry['protein']
        totals['carbs'] += entry['carbs']
        totals['fat'] += entry['fat']

    return jsonify({
        'entries': today_entries,
        'totals': totals,
        'date': today
    })
@app.route('/api/search_food')
def search_food():
    query = request.args.get('q','').lower().strip()
    results = []
    for food_key, nutrition in nutrition_db.items():
        if query in food_key.lower().replace('_',' '):
            results.append({
                'name': food_key,
                'calories_per_100g': nutrition.get('calories_per_100g',0),
                'protein': nutrition.get('protein',0),
                'carbs': nutrition.get('carbs',0),
                'fat': nutrition.get('fat',0),
                'health_score': nutrition.get('health_score',5)
            })
    return jsonify({'results': results[:10]})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)