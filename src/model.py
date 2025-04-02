import pickle
import logging
import os
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    accuracy_score, 
    f1_score, 
    precision_score,
    recall_score,
    confusion_matrix
)
from typing import Dict, Any, Optional
import numpy as np

logging.basicConfig(level=logging.INFO)

def train_model(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    tune_hyperparameters: bool = True, 
    best_params: Optional[Dict[str, Any]] = None
) -> RandomForestClassifier:
    """
    Trains a Random Forest classifier with optional hyperparameter tuning.
    """
    logging.info("Initializing Random Forest training...")
    model = RandomForestClassifier(
        random_state=42,
        class_weight='balanced'
    )

    if tune_hyperparameters and best_params is None:
        logging.info("Performing hyperparameter tuning...")
        param_grid = {
            "n_estimators": [50, 100, 150],
            "max_depth": [10, 30, None],
            "min_samples_leaf": [1, 2, 4]
        }
        grid_search = GridSearchCV(
            model, 
            param_grid, 
            cv=5,
            n_jobs=-1,
            scoring='f1',
            verbose=1
        )
        grid_search.fit(X_train, y_train)
        model = grid_search.best_estimator_
        logging.info(f"Best parameters found: {grid_search.best_params_}")
    elif best_params:
        logging.info(f"Using provided parameters: {best_params}")
        model.set_params(**best_params)
        model.fit(X_train, y_train)
    else:
        logging.info("Training with default parameters...")
        model.fit(X_train, y_train)

    logging.info("Training completed successfully")
    return model

def evaluate_model(
    model: RandomForestClassifier, 
    X_test: np.ndarray, 
    y_test: np.ndarray
) -> Dict[str, Any]:
    """
    Evaluates model performance and returns comprehensive metrics.
    """
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    
    metrics = {
        'accuracy': round(accuracy_score(y_test, y_pred), 4),
        'precision': round(precision_score(y_test, y_pred), 4),
        'recall': round(recall_score(y_test, y_pred), 4),
        'f1': round(f1_score(y_test, y_pred), 4),
        'confusion_matrix': {
            'true_negative': int(cm[0, 0]),
            'false_positive': int(cm[0, 1]),
            'false_negative': int(cm[1, 0]),
            'true_positive': int(cm[1, 1])
        }
    }
    
    logging.info("\nModel Evaluation:")
    logging.info(f"Accuracy: {metrics['accuracy']}")
    logging.info(f"Precision: {metrics['precision']}")
    logging.info(f"Recall: {metrics['recall']}")
    logging.info(f"F1 Score: {metrics['f1']}")
    logging.info(f"Confusion Matrix:\n{cm}")
    
    return metrics

def save_model(
    model: RandomForestClassifier, 
    filepath: str,
    metadata: Optional[Dict] = None
) -> None:
    """
    Saves trained model to disk with optional metadata.
    Now simplified to just save the model without metrics.
    """
    save_obj = {
        'model': model,
        'metadata': metadata or {
            'saved_at': datetime.now().isoformat()
        }
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    logging.info(f"Saving model to {filepath}")
    with open(filepath, "wb") as f:
        pickle.dump(save_obj, f)
    
    logging.info("Model saved successfully")

def load_model(filepath: str) -> RandomForestClassifier:
    """
    Loads a saved model from disk.
    Returns just the model object without metrics.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No model found at {filepath}")
    
    logging.info(f"Loading model from {filepath}")
    with open(filepath, "rb") as f:
        model_data = pickle.load(f)
    
    if 'model' not in model_data:
        raise ValueError("Invalid model file format")
    
    return model_data['model']

if __name__ == "__main__":
    # Example usage
    from preprocessing import load_data, preprocess_data
    
    try:
        logging.info("Starting model training pipeline...")
        
        # 1. Load and preprocess data
        df = load_data("data/bankruptcy_dataset.csv")
        X_train, X_test, y_train, y_test = preprocess_data(df)
        
        # 2. Train model
        model = train_model(X_train, y_train)
        
        # 3. Evaluate
        metrics = evaluate_model(model, X_test, y_test)
        
        # 4. Save model (without metrics)
        save_model(
            model=model,
            filepath="models/random_forest_model.pkl"
        )
        
        # 5. Example of loading
        loaded_model = load_model("models/random_forest_model.pkl")
        logging.info("Model loaded successfully")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        raise