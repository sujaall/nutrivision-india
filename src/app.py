from flask import Flask, render_template, request, jsonify
from predict import load_model, predict_food
from werkzeug.utils import secure_filename
import json, os

app = Flask(__name__,
    template_folder='../templates',
    static_folder='../static')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("Loading model...")
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'nutrivision_model.pth')
model, class_names = load_model(MODEL_PATH)

DATA_PATH = os.path.join(BASE_DIR, 'data', 'indian_nutrition.json')
with open(DATA_PATH) as f:
    nutrition_db = json.load(f)
print("Ready!")

def get_feedback(food, nutrition):
    feedback = []
    protein = nutrition.get('protein', 0)
    calories = nutrition.get('calories_per_100g', 0)
    score = nutrition.get('health_score', 5)
    if protein > 7:
        feedback.append("💪 Great protein source for muscle building!")
    if calories > 300:
        feedback.append("⚠️ High calorie — watch your portion size.")
    if calories < 150:
        feedback.append("✅ Low calorie — excellent for fat loss!")
    if score >= 8:
        feedback.append("🌿 Very healthy choice — eat freely!")
    if score <= 3:
        feedback.append("🔶 Treat food — enjoy occasionally only.")
    notes = nutrition.get('notes', '')
    if notes:
        feedback.append(f"📋 {notes}")
    return feedback

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    predictions = predict_food(filepath, model, class_names)
    top_food = predictions[0]['food']
    nutrition = nutrition_db.get(top_food, {
        'calories_per_100g': 200,
        'protein': 5, 'carbs': 25, 'fat': 5,
        'health_score': 5,
        'notes': 'Detailed nutrition data coming soon.'
    })
    return jsonify({
        'predictions': predictions,
        'nutrition': nutrition,
        'feedback': get_feedback(top_food, nutrition)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)