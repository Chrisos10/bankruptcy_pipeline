from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import uvicorn
import os
import sys
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta

# Import modules
from src.preprocessing import load_data, preprocess_data, load_prediction_data, fetch_training_data
from src.model import train_model, save_model, evaluate_model
from src.prediction import load_model, predict
from src.app.database import get_db
import src.app.models as models

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

app = FastAPI()

# Define expected feature columns globally
EXPECTED_COLUMNS = [
    "retained_earnings_to_total_assets",
    "total_debt_per_total_net_worth",
    "borrowing_dependency",
    "persistent_eps_in_the_last_four_seasons",
    "continuous_net_profit_growth_rate",
    "net_profit_before_tax_per_paidin_capital",
    "equity_to_liability",
    "pretax_net_interest_rate",
    "degree_of_financial_leverage",
    "per_share_net_profit_before_tax",
    "liability_to_equity",
    "net_income_to_total_assets",
    "total_income_per_total_expense",
    "interest_expense_ratio",
    "interest_coverage_ratio"
]

MODEL_PATH = Path("models/random_classifier.pkl").absolute()
os.makedirs(MODEL_PATH.parent, exist_ok=True)

# In-memory cache for trained models (in production use Redis)
trained_models_cache = {}

class BankruptcyInput(BaseModel):
    retained_earnings_to_total_assets: float
    total_debt_per_total_net_worth: float
    borrowing_dependency: float
    persistent_eps_in_the_last_four_seasons: float
    continuous_net_profit_growth_rate: float
    net_profit_before_tax_per_paidin_capital: float
    equity_to_liability: float
    pretax_net_interest_rate: float
    degree_of_financial_leverage: float
    per_share_net_profit_before_tax: float
    liability_to_equity: float
    net_income_to_total_assets: float
    total_income_per_total_expense: float
    interest_expense_ratio: float
    interest_coverage_ratio: float

class RetrainResponse(BaseModel):
    metrics: Dict
    model_id: str
    message: str

class SaveResponse(BaseModel):
    success: bool
    message: str

@app.post("/predict-single/")
async def predict_single(input_data: BankruptcyInput):
    try:
        input_df = pd.DataFrame([input_data.dict()], columns=EXPECTED_COLUMNS)
        model = load_model(MODEL_PATH)
        prediction = predict(input_df, model)
        return {"prediction": int(prediction[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-bulk/")
async def predict_bulk(file: UploadFile = File(...)):
    try:
        df = load_prediction_data(file)
        model = load_model(MODEL_PATH)
        predictions = predict(df, model)
        return {"predictions": predictions.tolist()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/retrain/", response_model=RetrainResponse)
async def retrain_model(db: Session = Depends(get_db)):
    """Train new model and return metrics without saving"""
    try:
        # 1. Fetch and validate data
        df = fetch_training_data(db)
        if len(df) < 100:
            raise HTTPException(
                status_code=400,
                detail="Insufficient training data (minimum 100 records required)"
            )
        
        # 2. Preprocess and train
        X_train, X_test, y_train, y_test = preprocess_data(df)
        model = train_model(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        
        # 3. Cache model with expiration (1 hour)
        model_id = str(uuid.uuid4())
        trained_models_cache[model_id] = {
            'model': model,
            'expires': datetime.now() + timedelta(hours=1)
        }
        
        # 4. Clean up expired models
        cleanup_expired_models()
        
        return RetrainResponse(
            metrics=metrics,
            model_id=model_id,
            message="Model trained successfully. Use /save-model to persist it."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-model/{model_id}", response_model=SaveResponse)
async def save_model_endpoint(model_id: str):
    """Save a previously trained model to disk"""
    try:
        # 1. Check if model exists and is valid
        model_data = trained_models_cache.get(model_id)
        if not model_data:
            raise HTTPException(
                status_code=404,
                detail="Model not found or expired. Please retrain."
            )
        
        # 2. Save to disk
        save_model(model_data['model'], MODEL_PATH)
        
        # 3. Remove from cache
        del trained_models_cache[model_id]
        
        return SaveResponse(
            success=True,
            message="Model saved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def cleanup_expired_models():
    """Remove expired models from cache"""
    now = datetime.now()
    expired_ids = [
        model_id for model_id, data in trained_models_cache.items()
        if data['expires'] < now
    ]
    for model_id in expired_ids:
        del trained_models_cache[model_id]

@app.get("/")
async def root():
    return {"message": "Welcome to the Bankruptcy Prediction API!"}

@app.get("/data/")
def get_all_data(db: Session = Depends(get_db)):
    try:
        data = db.query(models.BankruptcyData).all()
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)