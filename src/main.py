
import os
import joblib
import pandas as pd
from typing import List
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from . import models, database, auth

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

# Initialize App
app = FastAPI(
    title="ProPredict Enterprise API",
    description="Secure ML API with User History",
    version="2.0.0"
)

# --- Configuration ---
MODELS_DIR = "models"

# --- Load Models ---
try:
    delay_model = joblib.load(os.path.join(MODELS_DIR, 'delay_model.pkl'))
    cost_model = joblib.load(os.path.join(MODELS_DIR, 'cost_model.pkl'))
    suggestion_model = joblib.load(os.path.join(MODELS_DIR, 'suggestion_model.pkl'))
    MODELS_LOADED = True
except FileNotFoundError:
    print("⚠️ Models not found. Run training script.")
    MODELS_LOADED = False

# --- Pydantic Models ---
class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ProjectRequest(BaseModel):
    project_type: str
    project_description: str
    complexity_score: int
    number_of_developers: int
    team_experience_rating: int
    dependency_delay_days: int
    resource_availability_ratio: float
    labour_cost_index: float
    historical_delay_days: int

class PredictionResponse(BaseModel):
    predicted_delay_days: int
    cost_overrun_percent: float
    risk_level: str
    risk_color: str
    confidence_score: float

class SuggestionResponse(BaseModel):
    primary_suggestion: str
    additional_notes: List[str]

class HistoryItem(BaseModel):
    project_description: str
    predicted_delay: float
    cost_overrun: float
    timestamp: str

# --- Helper ---
def determine_risk(delay, cost):
    if delay > 60 or cost > 30: return "Critical", "#FF4B4B"
    elif delay > 30 or cost > 15: return "High", "#FFA500"
    elif delay > 10 or cost > 5: return "Moderate", "#FFD700"
    else: return "Low", "#00C851"

# --- Authentication Endpoints ---

@app.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Secure Endpoints ---

@app.get("/history")
def get_history(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Return last 10 records
    records = db.query(models.PredictionHistory).filter(models.PredictionHistory.user_id == current_user.id).order_by(models.PredictionHistory.timestamp.desc()).limit(10).all()
    return records

@app.post("/predict", response_model=PredictionResponse)
async def predict_outcomes(
    request: ProjectRequest, 
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail="ML Models unavailable.")
    
    input_df = pd.DataFrame([request.dict()])
    
    try:
        # Inference
        pred_delay = delay_model.predict(input_df)[0]
        pred_cost = cost_model.predict(input_df)[0]
        suggestion_label = suggestion_model.predict(input_df)[0]
        
        # Save to DB
        history_entry = models.PredictionHistory(
            user_id=current_user.id,
            project_description=request.project_description[:100] + "...",
            project_type=request.project_type,
            complexity_score=request.complexity_score,
            predicted_delay=float(pred_delay),
            cost_overrun=float(pred_cost),
            primary_suggestion=suggestion_label
        )
        db.add(history_entry)
        db.commit()

        # Response
        risk, color = determine_risk(pred_delay, pred_cost)
        return {
            "predicted_delay_days": int(max(0, pred_delay)),
            "cost_overrun_percent": round(max(0, pred_cost), 2),
            "risk_level": risk,
            "risk_color": color,
            "confidence_score": 0.95
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest", response_model=SuggestionResponse)
async def get_suggestions(request: ProjectRequest, current_user: models.User = Depends(auth.get_current_user)):
    if not MODELS_LOADED: raise HTTPException(status_code=503)
    input_df = pd.DataFrame([request.dict()])
    try:
        suggestion_class = suggestion_model.predict(input_df)[0]
        return {"primary_suggestion": suggestion_class, "additional_notes": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
