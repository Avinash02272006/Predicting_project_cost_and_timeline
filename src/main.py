
import os
import joblib
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from . import models, database, auth
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

# Initialize App
app = FastAPI(
    title="ProPredict Enterprise API",
    description="Secure ML API with User History",
    version="2.0.0"
)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Mounts ---
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/pages", StaticFiles(directory="frontend/pages"), name="pages")
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets") # If exists

# --- HTML Routes ---
@app.get("/")
async def serve_index(): return FileResponse("frontend/pages/index.html")

@app.get("/login")
async def serve_login(): return FileResponse("frontend/pages/login.html")

@app.get("/register")
async def serve_register(): return FileResponse("frontend/pages/register.html")

@app.get("/dashboard")
async def serve_dashboard(): return FileResponse("frontend/pages/home.html")

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

class LoginRequest(BaseModel):
    email: str
    password: str

class ProjectRequest(BaseModel):
    project_description: str
    project_type: str = "Web App"
    complexity_score: int = 5
    number_of_developers: int = 5
    team_experience_rating: int = 3
    dependency_delay_days: int = 5
    resource_availability_ratio: float = 0.8
    labour_cost_index: float = 1.5
    historical_delay_days: int = 0

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

@app.post("/login")
async def login_json(creds: LoginRequest, db: Session = Depends(database.get_db)):
    # Allow login by email or username (frontend sends email field but might be username)
    user = db.query(models.User).filter((models.User.email == creds.email) | (models.User.username == creds.email)).first()
    if not user or not auth.verify_password(creds.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "message": "Login successful"}

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
    # 1. Try OpenAI if Key exists
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "your_key_here":
        try:
            client = OpenAI(api_key=api_key)
            prompt = (
                f"Project Analysis Request:\n"
                f"Type: {request.project_type}\n"
                f"Description: {request.project_description}\n"
                f"Complexity: {request.complexity_score}/10\n"
                f"Team Size: {request.number_of_developers}\n\n"
                f"Provide a single, impactful strategic recommendation (1 sentence) followed by 3 brief, actionable bullet points."
            )
            
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert IT Project Manager consultant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            
            full_text = completion.choices[0].message.content.strip()
            
            # Simple parsing: First line is primary, rest are notes
            parts = full_text.split('\n')
            primary = parts[0]
            notes = [p.strip('- ') for p in parts[1:] if p.strip()]
            
            return {"primary_suggestion": primary, "additional_notes": notes}
            
        except Exception as e:
            print(f"⚠️ OpenAI Error: {e}")
            # Fallback to local model on error
            pass

    # 2. Fallback to Local Model
    if not MODELS_LOADED: raise HTTPException(status_code=503)
    input_df = pd.DataFrame([request.dict()])
    try:
        suggestion_class = suggestion_model.predict(input_df)[0]
        return {"primary_suggestion": f"{suggestion_class} (Local Model)", "additional_notes": ["Add valid OpenAI Key for detailed AI advice."]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
