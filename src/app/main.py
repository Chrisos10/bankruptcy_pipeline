from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uvicorn
import os
import sys
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import io

# Local imports
from .database import get_db
from . import models
from ..preprocessing import load_data, preprocess_data, load_prediction_data, fetch_training_data
from ..model import train_model, save_model, evaluate_model
from ..prediction import load_model, predict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
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
trained_models_cache = {}

class ConfusionMatrix(BaseModel):
    true_negative: int
    false_positive: int
    false_negative: int
    true_positive: int

class MetricDetail(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float  # Note: This must match the key in your metrics dictionary
    confusion_matrix: ConfusionMatrix

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
    metrics: MetricDetail
    model_id: str
    message: str
    training_samples: int
    test_samples: int

class SaveResponse(BaseModel):
    success: bool
    message: str

class BulkUploadResponse(BaseModel):
    success: bool
    message: str
    records_added: int
    invalid_records: int

# Helper Functions
def cleanup_expired_models():
    now = datetime.now()
    expired_ids = [
        model_id for model_id, data in trained_models_cache.items()
        if data['expires'] < now
    ]
    for model_id in expired_ids:
        del trained_models_cache[model_id]

# API Endpoints
@app.post("/upload-training-data/", response_model=BulkUploadResponse)
async def upload_training_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload training data to database"""
    try:
        # Read file
        file_content = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise HTTPException(400, "Unsupported file format")

        # Validate columns
        required_columns = EXPECTED_COLUMNS + ['bankrupt']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise HTTPException(400, f"Missing columns: {missing_cols}")

        # Insert records
        records_added = 0
        invalid_records = 0
        
        for _, row in df.iterrows():
            try:
                record = models.BankruptcyData(
                    bankrupt=int(row['bankrupt']),
                    retained_earnings_to_total_assets=float(row['retained_earnings_to_total_assets']),
                    total_debt_per_total_net_worth=float(row['total_debt_per_total_net_worth']),
                    borrowing_dependency=float(row['borrowing_dependency']),
                    persistent_eps_in_the_last_four_seasons=float(row['persistent_eps_in_the_last_four_seasons']),
                    continuous_net_profit_growth_rate=float(row['continuous_net_profit_growth_rate']),
                    net_profit_before_tax_per_paidin_capital=float(row['net_profit_before_tax_per_paidin_capital']),
                    equity_to_liability=float(row['equity_to_liability']),
                    pretax_net_interest_rate=float(row['pretax_net_interest_rate']),
                    degree_of_financial_leverage=float(row['degree_of_financial_leverage']),
                    per_share_net_profit_before_tax=float(row['per_share_net_profit_before_tax']),
                    liability_to_equity=float(row['liability_to_equity']),
                    net_income_to_total_assets=float(row['net_income_to_total_assets']),
                    total_income_per_total_expense=float(row['total_income_per_total_expense']),
                    interest_expense_ratio=float(row['interest_expense_ratio']),
                    interest_coverage_ratio=float(row['interest_coverage_ratio'])
                )
                db.add(record)
                records_added += 1
            except (ValueError, TypeError):
                invalid_records += 1
                continue

        db.commit()
        return BulkUploadResponse(
            success=True,
            message=f"Added {records_added} records",
            records_added=records_added,
            invalid_records=invalid_records
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@app.post("/predict-single/")
async def predict_single(input_data: BankruptcyInput):
    try:
        input_df = pd.DataFrame([input_data.dict()], columns=EXPECTED_COLUMNS)
        model = load_model(MODEL_PATH)
        results = predict(input_df, model)  # Using the updated predict() function
        
        return {
            "prediction": int(results['predictions'][0]),
            "probability": float(results['probabilities'][0])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-bulk/")
async def predict_bulk(file: UploadFile = File(...)):
    try:
        df = load_prediction_data(file)
        model = load_model(MODEL_PATH)
        results = predict(df, model)
        
        # Combine predictions and probabilities into a single array of objects
        combined_results = [
            {"prediction": int(pred), "probability": float(prob)}
            for pred, prob in zip(results['predictions'], results['probabilities'])
        ]
        
        return {
            "results": combined_results,
            "count": len(combined_results)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/retrain/", response_model=RetrainResponse)
async def retrain_model(db: Session = Depends(get_db)):
    """Train new model and return detailed metrics"""
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
        
        # Debugging: Print the exact metrics structure
        print("Metrics received from evaluate_model:", metrics)
        
        # 3. Validate metrics structure before use
        required_metrics = ['accuracy', 'precision', 'recall', 'f1', 'confusion_matrix']
        if not all(key in metrics for key in required_metrics):
            raise ValueError("Missing required metrics in evaluation results")
            
        required_cm_keys = ['true_negative', 'false_positive', 'false_negative', 'true_positive']
        if not all(key in metrics['confusion_matrix'] for key in required_cm_keys):
            raise ValueError("Malformed confusion matrix")
        
        # 4. Cache model with expiration (1 hour)
        model_id = str(uuid.uuid4())
        trained_models_cache[model_id] = {
            'model': model,
            'expires': datetime.now() + timedelta(hours=1)
        }
        
        # 5. Clean up expired models
        cleanup_expired_models()
        
        # 6. Build response with validated metrics
        return RetrainResponse(
            metrics=MetricDetail(
                accuracy=metrics['accuracy'],
                precision=metrics['precision'],
                recall=metrics['recall'],
                f1=metrics['f1'],  # Must match the key in your metrics dict
                confusion_matrix=ConfusionMatrix(
                    true_negative=metrics['confusion_matrix']['true_negative'],
                    false_positive=metrics['confusion_matrix']['false_positive'],
                    false_negative=metrics['confusion_matrix']['false_negative'],
                    true_positive=metrics['confusion_matrix']['true_positive']
                )
            ),
            model_id=model_id,
            message="Model trained successfully. Use /save-model to persist it.",
            training_samples=len(X_train),
            test_samples=len(X_test)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model training failed: {str(e)}"
        )

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

if __name__ == "__main__":
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)