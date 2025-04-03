from fastapi import UploadFile
import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import RandomOverSampler
from collections import Counter
import logging
import argparse
from io import StringIO
from typing import Union


from sqlalchemy.orm import Session
from src.app import models
from src.app.database import get_db


logging.basicConfig(level=logging.INFO)

# Define expected columns globally
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
    "interest_coverage_ratio",
    "bankrupt"
]

def load_data(file_path, clean_columns=True, require_bankrupt=True):
    """Loads dataset and ensures required columns are present"""
    logging.info(f"Loading dataset from {file_path}...")
    try:
        df = pd.read_csv(file_path, encoding="utf-8", low_memory=False)
        
        if clean_columns:
            logging.info("Cleaning column names...")
            df.columns = (
                df.columns
                .str.strip()
                .str.replace(' ', '_')
                .str.replace(r'[^\w\s]', '')
                .str.replace(r'\(.*\)', ' ', regex=True)
                .str.replace(' ', '_')
                .str.replace('?', '')
                .str.replace('%', '')
                .str.rstrip('__')
                .str.replace('--', '-')
                .str.replace("'", "")
                .str.replace("-", "")
                .str.replace("aftertax", "AfterTax")
                .str.replace("/", "_per_")
                .str.lower()
            )
            df = df.loc[:, ~df.columns.duplicated()]

        required_cols = EXPECTED_COLUMNS if require_bankrupt else EXPECTED_COLUMNS[:-1]
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            raise ValueError(f"Missing columns: {missing}")
            
        return df[required_cols]
        
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        raise

def preprocess_data(df, handle_imbalance=True, imbalance_threshold=0.3):
    """Preprocesses data including train-test split and imbalance handling"""
    logging.info("Preprocessing data...")
    try:
        X = df.drop(columns=['bankrupt'])
        y = df['bankrupt']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        class_counts = Counter(y_train)
        imbalance_ratio = min(class_counts.values()) / max(class_counts.values())
        logging.info(f"Before Oversampling - Class Distribution: {class_counts}")
        
        if handle_imbalance and imbalance_ratio < imbalance_threshold:
            logging.info("Applying Random Over-Sampling")
            ros = RandomOverSampler(random_state=42)
            X_train, y_train = ros.fit_resample(X_train, y_train)
            logging.info(f"After Oversampling: {Counter(y_train)}")
            
        return X_train, X_test, y_train, y_test
        
    except Exception as e:
        logging.error(f"Preprocessing failed: {str(e)}")
        raise

def load_prediction_data(upload_file: UploadFile):
    """Simplified loader for pre-cleaned data that matches EXPECTED_COLUMNS exactly"""
    try:
        # Read the file content
        content = upload_file.file.read().decode('utf-8')
        upload_file.file.seek(0)
        
        # Read CSV
        df = pd.read_csv(StringIO(content))
        
        # Verify we have exactly the expected columns (excluding 'bankrupt')
        required_columns = EXPECTED_COLUMNS[:-1]
        
        # Check for missing or extra columns
        missing = set(required_columns) - set(df.columns)
        extra = set(df.columns) - set(required_columns)
        
        if missing:
            raise ValueError(
                f"Missing required columns: {missing}\n"
                f"Expected columns: {required_columns}\n"
                f"Found columns: {df.columns.tolist()}"
            )
            
        if extra:
            logging.warning(f"Extra columns will be ignored: {extra}")
        
        # Return data with columns in correct order
        return df[required_columns]
        
    except Exception as e:
        raise ValueError(f"Failed to process file: {str(e)}")
    finally:
        upload_file.file.seek(0)


def fetch_training_data(db: Session):
    """Fetch training data from database and convert to DataFrame"""
    try:
        # Query all records from the database
        records = db.query(models.BankruptcyData).all()
        
        # Convert to list of dictionaries
        data = [{
            'retained_earnings_to_total_assets': r.retained_earnings_to_total_assets,
            'total_debt_per_total_net_worth': r.total_debt_per_total_net_worth,
            'borrowing_dependency': r.borrowing_dependency,
            'persistent_eps_in_the_last_four_seasons': r.persistent_eps_in_the_last_four_seasons,
            'continuous_net_profit_growth_rate': r.continuous_net_profit_growth_rate,
            'net_profit_before_tax_per_paidin_capital': r.net_profit_before_tax_per_paidin_capital,
            'equity_to_liability': r.equity_to_liability,
            'pretax_net_interest_rate': r.pretax_net_interest_rate,
            'degree_of_financial_leverage': r.degree_of_financial_leverage,
            'per_share_net_profit_before_tax': r.per_share_net_profit_before_tax,
            'liability_to_equity': r.liability_to_equity,
            'net_income_to_total_assets': r.net_income_to_total_assets,
            'total_income_per_total_expense': r.total_income_per_total_expense,
            'interest_expense_ratio': r.interest_expense_ratio,
            'interest_coverage_ratio': r.interest_coverage_ratio,
            'bankrupt': r.bankrupt
        } for r in records]
        
        # Convert to DataFrame and ensure correct column order
        return pd.DataFrame(data)[EXPECTED_COLUMNS]
        
    except Exception as e:
        logging.error(f"Error fetching training data: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_path", type=str, required=True, help="Path to dataset")
    args = parser.parse_args()

    try:
        df = load_data(args.file_path)
        X_train, X_test, y_train, y_test = preprocess_data(df)
        logging.info("Preprocessing completed successfully")
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")