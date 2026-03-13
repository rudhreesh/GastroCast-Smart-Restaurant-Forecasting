# AI-ROS: Conversational Demand Prediction Agent

An intelligent, production-ready AI agent that translates natural language into PostgreSQL queries, trains dynamic Facebook Prophet time-series models on-the-fly, and delivers conversational demand forecasts for restaurants.

## 🚀 Key Features

*   **Natural Language to SQL**: Powered by Groq (Llama 3.3), allowing users to ask complex forecasting and analytical questions in plain English.
*   **Dynamic Time-Series ML**: Automatically extracts historical datasets from PostgreSQL and spins up univariate **Facebook Prophet** machine learning models for any targeted metric.
*   **Automated Feature Engineering**: Intelligently isolates predictive targets, strict `ds` chronological indexes, and dynamically handles multi-target query outputs.
*   **Conversational LLM Synthesis**: Translates raw mathematical prediction arrays back into actionable, highly contextual, and friendly insights.
*   **Robust & Scalable**: Natively handles multi-variable SQL aggregations, complex overlapping date filters, and gracefully falls back on conversational loops when data is sparse.

## 🛠️ Tech Stack

*   **Language:** Python 3
*   **Database:** PostgreSQL (Dockerized)
*   **Machine Learning:** Facebook Prophet, Pandas
*   **LLM Inference:** Groq API (Llama-3.3-70b-versatile)

## ⚙️ Getting Started

### Prerequisites
*   Docker & Docker Compose
*   Python 3.10+
*   Groq API Key

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd AI-ROS/demand_prediction_poc
   ```

2. **Set up the virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install prophet pandas python-dotenv psycopg2-binary sqlalchemy groq
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the `demand_prediction_poc` directory and add your credentials:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   POSTGRES_DB=demand_db
   POSTGRES_USER=demand_user
   POSTGRES_PASSWORD=demand_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5433
   ```

4. **Boot the Database:**
   Start the PostgreSQL container:
   ```bash
   docker-compose up -d
   ```

5. **Seed Historical Data:**
   Generate 2 years of simulated, seasonally-adjusted restaurant data to train the bounds:
   ```bash
   python generate_dummy_data.py
   ```

## 💬 Usage

Run the interactive AI CLI agent to chat and forecast dynamically:
```bash
python run_custom.py
```

**Example Queries:**
*   *"Predict total sales for tomorrow based on the last 30 days."*
*   *"Forecast our expected revenue for this upcoming weekend."*
*   *"Predict the number of unique customers and required staff for next Monday."*

## 🧪 Testing the Pipeline

A rigorous test suite is included to run the Prophet time-series logic across **13 complex stress-test scenarios**, ranging from categorical grouping queries to fallback error-handling.

To execute the test suite:
```bash
python run_tests.py
```
*The full execution logs, ML matrix footprints, and generated LLM responses will be written locally to `PROPHET_TEST_RESULTS.md`.*

---
*Built as a Proof-of-Concept to demonstrate end-to-end Chat -> SQL -> Auto-ML Pipeline generation inside modern Restaurant Operating Systems.*
