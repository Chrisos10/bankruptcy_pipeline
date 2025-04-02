import os
import pickle
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

def load_model(model_path):
    """Loads the trained model from the specified file path."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    if not hasattr(model, "feature_names_in_"):
        raise ValueError("Model missing feature names information")
    
    logging.info(f"Model loaded with features: {model.feature_names_in_}")
    return model

def predict(data, model):
    """
    Makes predictions with proper feature validation and returns both 
    class predictions and probabilities.
    
    Returns:
        dict: {
            'predictions': array of class predictions (0 or 1),
            'probabilities': array of probabilities for class 1
        }
    """
    # Convert input to DataFrame with proper feature names if needed
    if not isinstance(data, pd.DataFrame):
        if isinstance(data, (list, np.ndarray)):
            data = pd.DataFrame(data, columns=model.feature_names_in_)
        else:
            data = pd.DataFrame([data], columns=model.feature_names_in_)
    
    # Validate features
    missing = set(model.feature_names_in_) - set(data.columns)
    if missing:
        raise ValueError(f"Missing features: {missing}")
    
    # Reorder columns to match training
    data = data[model.feature_names_in_]
    
    # Get both predictions and probabilities
    predictions = model.predict(data)
    probabilities = model.predict_proba(data)[:, 1]  # Probability of class 1 (bankruptcy)
    
    return {
        'predictions': predictions,
        'probabilities': probabilities
    }

if __name__ == "__main__":
    model = load_model("models/random_classifier.pkl")
    print(f"Model expects features: {model.feature_names_in_}")