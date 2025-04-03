# Bankruptcy Prediction ML Pipeline

## Project Overview

This project demonstrates a **Machine Learning (ML) pipeline** for bankruptcy prediction. It features model training, evaluation, and retraining triggers based on new data uploads. The application is fully **dockerized** and offers an interactive web interface for predictions, bulk data uploads, and financial data visualizations.

## Features

- **Model Prediction**: Predicts bankruptcy risk for single or multiple data points.
- **Data Visualization**: Provides insights into key financial features.
- **Bulk Data Upload**: Supports CSV/XLS uploads for model retraining.
- **Retraining Trigger**: Allows users to retrain the model with new data.
- **Dockerized Application**: Ensures easy deployment and scalability.

## Project Structure

```plaintext
BANKRUPTCY_PIPELINE/
│── .vscode/
│── data/
│   │── test/
│   │── train/
│── models/
│── notebook/
│   │── Jean_Chrisostome_ML_Pipeline__Summative.ipynb
│── src/
│   │── app/
│   │   │── __init__.py
│   │   │── database.py
│   │   │── main.py
│   │   │── models.py
│   │── Front_end/
│   │   │── css/
│   │   │── images/
│   │   │── js/
│   │   │── templates/
│   │   │── __init__.py
│   │── model.py
│   │── prediction.py
│   │── preprocessing.py
│── venv/
│── .env
│── .gitignore
│── docker-compose.yml
│── dockerfile
│── requirements.txt
```

## Getting Started

### Prerequisites

Ensure you have the following installed:

- **Python 3.8+**
- **Docker & Docker Compose**
- **PostgreSQL** (if running locally)
- **Git**

### Installation Steps

#### 1. Clone the Repository

```bash
git clone <repository_url>
cd bankruptcy_pipeline
```

#### 2. Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate     # Windows
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Set Up Environment Variables

Create a `.env` file in the project root and add:

```env
DATABASE_URL=your_postgresql_url
SECRET_KEY=your_secret_key
```

#### 5. Run the Application Locally

```bash
uvicorn src.app.main:app --reload
```

#### 6. Run the Application with Docker

**Build the Docker Image:**

```bash
docker build . -t bankruptcy-api --no-cache
```

**Run the Docker Container:**

```bash
docker run -p 8000:8000 bankruptcy-api
```

The Application will be live at: [http://0.0.0.0:8000](http://0.0.0.0:8000)

## API Endpoints

| Endpoint          | Method | Description                         |
| ----------------- | ------ | ----------------------------------- |
| `/predict`        | POST   | Make a prediction (single & bulk)   |
| `/upload`         | POST   | Upload bulk data for retraining     |
| `/retrain`        | POST   | Trigger model retraining            |
| `/visualizations` | GET    | View dataset feature visualizations |

## Interacting with the Web Application

### Sample Prediction Input

For single predictions, use the following JSON format:

```json
{
  "retained_earnings_to_total_assets": 0.12,
  "total_debt_per_total_net_worth": 0.45,
  "borrowing_dependency": 0.30,
  "persistent_eps_in_the_last_four_seasons": 2.5,
  "continuous_net_profit_growth_rate": 0.08,
  "net_profit_before_tax_per_paidin_capital": 1.2,
  "equity_to_liability": 0.75,
  "pretax_net_interest_rate": 0.05,
  "degree_of_financial_leverage": 1.8,
  "per_share_net_profit_before_tax": 3.2,
  "liability_to_equity": 0.60,
  "net_income_to_total_assets": 0.09,
  "total_income_per_total_expense": 1.3,
  "interest_expense_ratio": 0.04,
  "interest_coverage_ratio": 2.0
}
```

### Bulk Prediction and Retraining

- **Bulk Prediction**: Upload data from `/data/test/bulk_pred_testing.csv`.
- **Retraining**: Upload data from `/data/train/sample_retrain.csv`.
- Ensure all required features match the ones used in a single prediction if you have your own dataset.

## Technical Stack

- **Backend**: FastAPI
- **Machine Learning**: Scikit-learn
- **Data Processing**: Pandas, Scikit-learn
- **Web Interface**: HTML, CSS, JavaScript
- **Containerization**: Docker
- **API Documentation**: OpenAPI (Swagger UI)

## Video Demo

📽 [Watch the demonstration on YouTube](#)

## URL

🔗 [Live Application (if applicable)](#)

