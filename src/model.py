import pickle
import logging
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    classification_report, 
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
    
    Args:
        X_train: Training features (numpy array or pandas DataFrame)
        y_train: Training labels (numpy array or pandas Series)
        tune_hyperparameters: Whether to perform grid search (default: True)
        best_params: Predefined parameters if tuning is skipped (default: None)
        
    Returns:
        Trained Random Forest model
    """
    logging.info("Initializing Random Forest training...")
    model = RandomForestClassifier(
        random_state=42,
        class_weight='balanced'  # Handles imbalanced classes
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
    
    Args:
        model: Trained scikit-learn model
        X_test: Test features
        y_test: True labels for test set
        
    Returns:
        Dictionary containing:
        - Basic metrics (accuracy, F1, precision, recall)
        - Confusion matrix
        - Full classification report
        - Feature importances (if available)
    """
    y_pred = model.predict(X_test)
    
    metrics = {
        'accuracy': round(accuracy_score(y_test, y_pred), 4),
        'f1_score': round(f1_score(y_test, y_pred), 4),
        'precision': round(precision_score(y_test, y_pred), 4),
        'recall': round(recall_score(y_test, y_pred), 4),
        'confusion_matrix': {
            'true_negative': int(confusion_matrix(y_test, y_pred)[0, 0]),
            'false_positive': int(confusion_matrix(y_test, y_pred)[0, 1]),
            'false_negative': int(confusion_matrix(y_test, y_pred)[1, 0]),
            'true_positive': int(confusion_matrix(y_test, y_pred)[1, 1])
        },
        'classification_report': classification_report(y_test, y_pred, output_dict=True)
    }
    
    # Add feature importances if available
    if hasattr(model, 'feature_importances_'):
        metrics['feature_importances'] = dict(zip(
            model.feature_names_in_ if hasattr(model, 'feature_names_in_') 
            else [f"feature_{i}" for i in range(X_test.shape[1])],
            [round(imp, 6) for imp in model.feature_importances_]
        ))
    
    # Log key metrics
    logging.info("\nModel Evaluation:")
    logging.info(f"Accuracy: {metrics['accuracy']}")
    logging.info(f"F1 Score: {metrics['f1_score']}")
    logging.info(f"Precision: {metrics['precision']}")
    logging.info(f"Recall: {metrics['recall']}")
    
    return metrics

def save_model(
    model: RandomForestClassifier, 
    filepath: str,
    metadata: Optional[Dict] = None
) -> None:
    """
    Saves trained model to disk with optional metadata.
    
    Args:
        model: Trained model to save
        filepath: Full path to save the model (.pkl file)
        metadata: Optional dictionary of metadata to save
    """
    save_obj = {
        'model': model,
        'metadata': metadata or {}
    }
    
    logging.info(f"Saving model to {filepath}")
    with open(filepath, "wb") as f:
        pickle.dump(save_obj, f)
    
    logging.info("Model saved successfully")

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
        
        # 4. Save with metadata
        save_model(
            model,
            "models/random_forest_model.pkl",
            metadata={
                'training_date': datetime.now().isoformat(),
                'metrics': metrics
            }
        )
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        raise