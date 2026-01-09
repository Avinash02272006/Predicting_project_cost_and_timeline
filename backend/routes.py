
from flask import Blueprint, request, jsonify, session
from database import db, History
from auth import register_user, authenticate_user
import joblib
import pandas as pd
import os

api_bp = Blueprint('api', __name__)

# Load Models (Robust Path Logic)
try:
    # Attempt to find models relative to backend
    base_path = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_path, '..', 'models') 
    
    # Fallback if needed, but assuming user didn't delete them
    delay_model = joblib.load(os.path.join(model_path, 'delay_model.pkl'))
    cost_model = joblib.load(os.path.join(model_path, 'cost_model.pkl'))
    suggestion_model = joblib.load(os.path.join(model_path, 'suggestion_model.pkl'))
except:
    print("Warning: Models not found in ../models. ML features will fail.")

# Auth Routes
@api_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    if register_user(data['username'], data['email'], data['password']):
        return jsonify({"message": "Success"}), 201
    return jsonify({"message": "User exists"}), 400

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = authenticate_user(data['email'], data['password'])
    if user:
        session['user_id'] = user.id
        return jsonify({"message": "Logged in"}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@api_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out"}), 200

# Logic Routes
@api_bp.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session: return jsonify({"message": "Unauthorized"}), 401
    
    data = request.json
    # Create DataFrame for inference (using defaults for missing fields)
    df = pd.DataFrame([{
        "project_type": data.get('project_type', 'Web App'),
        "project_description": data.get('description', ''),
        "complexity_score": int(data.get('complexity', 5)),
        "number_of_developers": int(data.get('developers', 5)),
        "team_experience_rating": 3,
        "dependency_delay_days": 5,
        "resource_availability_ratio": 0.8,
        "labour_cost_index": 1.5,
        "historical_delay_days": 0
    }])
    
    # Inference
    try:
        cost = cost_model.predict(df)[0]
        delay = delay_model.predict(df)[0]
        sug = suggestion_model.predict(df)[0]
    except:
        cost, delay, sug = 0, 0, "Model Error"

    # Save History
    h = History(
        user_id=session['user_id'],
        project_description=data.get('description', '')[:200],
        project_type=data.get('project_type', 'Web App'),
        predicted_cost=round(cost, 1),
        predicted_timeline=round(delay, 1),
        suggestion=sug
    )
    db.session.add(h)
    db.session.commit()

    return jsonify({
        "cost_overrun": round(cost, 1),
        "predicted_delay": int(delay),
        "suggestion": sug
    })

@api_bp.route('/history', methods=['GET'])
def get_history():
    if 'user_id' not in session: return jsonify({"message": "Unauthorized"}), 401
    
    hist = History.query.filter_by(user_id=session['user_id']).order_by(History.timestamp.desc()).all()
    return jsonify([{
        "id": h.id,
        "project_description": h.project_description,
        "project_type": h.project_type,
        "predicted_cost": h.predicted_cost,
        "predicted_timeline": h.predicted_timeline,
        "suggestion": h.suggestion,
        "timestamp": h.timestamp.isoformat()
    } for h in hist])
