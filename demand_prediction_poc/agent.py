import os
import psycopg2
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseIntrospector:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.environ.get("POSTGRES_DB", "demand_db"),
            user=os.environ.get("POSTGRES_USER", "demand_user"),
            password=os.environ.get("POSTGRES_PASSWORD", "demand_password"),
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5433") # updated port
        )

    def get_schema_context(self) -> str:
        """Retrieves schema definitions for relevant tables."""
        tables = ['restaurant_sales', 'labour_attendance', 'table_reservations']
        schema_info = "Database Schema:\n"
        
        with self.conn.cursor() as cur:
            for table in tables:
                cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}';")
                columns = cur.fetchall()
                schema_info += f"Table: {table}\n"
                for col in columns:
                    schema_info += f"  - {col[0]} ({col[1]})\n"
                schema_info += "\n"
                
        return schema_info
        
    def execute_query(self, query: str) -> pd.DataFrame:
        """Executes a generated SQL query securely and returns a DataFrame."""
        try:
            from sqlalchemy import create_engine
            # create sqlalchemy engine using psycopg2
            url = f"postgresql+psycopg2://{os.environ.get('POSTGRES_USER', 'demand_user')}:{os.environ.get('POSTGRES_PASSWORD', 'demand_password')}@{os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5433')}/{os.environ.get('POSTGRES_DB', 'demand_db')}"
            engine = create_engine(url)
            df = pd.read_sql_query(query, engine)
            return df
        except Exception as e:
            print(f"Error executing SQL: {e}")
            return None
            
    def close(self):
        self.conn.close()


class MLAgent:
    def __init__(self):
        # We need a GROQ_API_KEY environment variable defined
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
             print("WARNING: GROQ_API_KEY environment variable not set. Please set it in a .env file or environment.")
        self.client = Groq(api_key=api_key)

    def classify_intent(self, user_prompt: str) -> str:
        """Classifies the intent of the user prompt as either 'PREDICTION' or 'CHAT'."""
        system_prompt = """
        You are an intent classifier for a restaurant AI assistant.
        Determine if the user's input is asking for a data prediction/analysis regarding the restaurant (e.g., predicting demand, forecasting revenue, asking about sales data or staffing needs) 
        OR if it is a general chat/conversational query (e.g., asking how you are, general world facts, sports, unrelated predictions, pleasantries).
        
        Respond ONLY with 'PREDICTION' if it requires analyzing the restaurant's internal data.
        Respond ONLY with 'CHAT' if it is conversational, general knowledge, or an unrelated topic (like IPL, sports, weather, etc).
        Do not include any other text.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
            )
            intent = chat_completion.choices[0].message.content.strip().upper()
            if "PREDICTION" in intent:
                return "PREDICTION"
            return "CHAT"
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return "CHAT" # default to chat on error

    def chat(self, user_prompt: str) -> str:
        """Handles general chat queries."""
        system_prompt = "You are a helpful and friendly AI assistant for a restaurant. You can chat generally or help users with demand prediction and data analysis if they ask."
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating chat response: {e}")
            return "I'm having trouble connecting right now, but I'm a restaurant AI assistant!"

    def generate_sql(self, user_prompt: str, schema_context: str) -> str:
        """Uses Groq to translate a demand prediction request into a SQL query."""
        system_prompt = f"""
        You are an expert AI Data Engineer for a restaurant. 
        Your task is to write ONLY a raw PostgreSQL query to fetch the exact historical data needed by a Machine Learning model 
        to predict future demand based on the user's scenario.

        Rules:
        1. Return ONLY the raw SQL query. Do not include markdown formatting like ```sql...```, no explanations, no chat. JUST THE QUERY text.
        2. Give the ML model just the right amount of data: not unnecessary data, but don't cut important features.
        3. Make sure to aggregate or extract features if it helps the model (like DATE_PART, COUNT, SUM), or join tables if they are related by date/time.
        4. STRICT POSTGRESQL RULE: Any column in the SELECT clause that is not wrapped in an aggregate function MUST be included in the GROUP BY clause.
        5. STRICT POSTGRESQL RULE: If you use an ORDER BY clause with a column, that column must be in the GROUP BY clause if aggregation is used.
        6. STRICT POSTGRESQL RULE: For complex overlapping conditions (e.g. filtering dates based on average total sales, or combining multiple grouped datasets), you MUST use Common Table Expressions (WITH CTE AS ...) instead of deeply nested subqueries in the WHERE clause. Do not place aggregates into a WHERE clause subquery directly.
        7. STRICT POSTGRESQL RULE: When performing Date/Time Math on an aggregate (e.g., `MIN(time_col) - INTERVAL '2 hours'`), do NOT execute this directly within a `BETWEEN` or `WHERE` clause subquery, as Postgres will throw a "record - interval" type error. Instead, perform the interval math *inside* the CTE SELECT statement as its own explicitly typed column, and then select that clean column in your main query.
        8. STRICT POSTGRESQL RULE: When you use `ORDER BY` with a column that is NOT in the `SELECT` block, Postgres will throw a column-not-found error (especially involving CTEs). ONLY `ORDER BY` the exact aliases or columns explicitly written in your final `SELECT` block.
        9. STRICT POSTGRESQL RULE: If you JOIN multiple tables that share a column name (like `sale_date` and `attendance_date`, or simply `id`), you MUST prefix the column name with its table name or alias (e.g., `COUNT(DISTINCT restaurant_sales.id)`) to avoid an AmbiguousColumn error.
        10. STRICT ML TIMESERIES RULE: NEVER query for future dates (e.g., `sale_date = CURRENT_DATE + INTERVAL '1 day'`). The database only contains historical data. To predict the future, you MUST fetch a historical time-series dataset (e.g., `sale_date >= CURRENT_DATE - INTERVAL '90 days'`) and let the ML model forecast the future from it.
        11. STRICT ML TIMESERIES RULE: MUST return a time-series. Do NOT use `AVG()`, `SUM()`, or `MAX()` to aggregate the final result into a single row. The final `SELECT` MUST return a time-series with a date or timestamp column for EACH row.
        12. STRICT ML TIMESERIES RULE: ALWAYS include a date column. The final `SELECT` statement MUST include a date column (e.g., `sale_date`, `attendance_date`, `reservation_date`) so the ML model can use it as a time index.

        {schema_context}
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User Request: {user_prompt}"}
                ],
                model="llama-3.3-70b-versatile", # Groq model
                temperature=0.1,
            )
            
            raw_response = chat_completion.choices[0].message.content.strip()
            # Clean up if the LLM hallucinated markdown anyway
            if raw_response.startswith("```sql"):
                raw_response = raw_response[len("```sql"):].strip()
            if raw_response.endswith("```"):
                raw_response = raw_response[:-len("```")].strip()
                
            return raw_response
        except Exception as e:
            print(f"Error generating SQL with Groq: {e}")
            return ""

    def summarize_prediction(self, user_prompt: str, ml_metrics: str) -> str:
        """Takes the raw ML output and the user's original query to synthesize a conversational summary."""
        system_prompt = f"""
        You are a helpful AI Restaurant Manager Assistant.
        The user asked the following forecasting question: "{user_prompt}"
        
        Our internal Machine Learning model analyzed the database and returned these raw metrics:
        {ml_metrics}
        
        Your job is to read these metrics and write a brief, friendly, natural-language response directly to the user.
        Do not mention SQL, databases, or 'raw metrics'. Just synthesize the findings into actionable, conversational advice.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Please summarize the prediction."}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.4,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return ml_metrics  # fallback to raw metrics if LLM fails

class FeatureBuilder:
    def __init__(self):
        # We try to infer target columns from common aliases the agent might use
        self.target_keywords = ['sales', 'revenue', 'sold', 'bookings', 'reservations', 'customers', 'attendance', 'staff', 'party']
        self.target_columns = []
        
    def build_features(self, df: pd.DataFrame):
        """
        Prepares raw SQL data for the ML model.
        Fills missing values, handles categorical encodings, normalizes if necessary.
        Returns a tuple of (X, y) where X is the feature matrix and y is the target matrix.
        """
        if df is None or df.empty:
            return None, None
            
        print("\n--- Feature Builder ---")
        print(f"Received {len(df)} rows from the agent.")
        
        # 1. Drop NAs for simplicity in this POC
        df_processed = df.dropna().copy()
        if df_processed.empty:
            return None, None
        
        # 2. Extract Datetime features
        date_cols = [col for col in df_processed.columns if 'date' in col.lower() or 'time' in col.lower()]
        for date_col in date_cols:
            try:
                dt_series = pd.to_datetime(df_processed[date_col])
                if 'ds' not in df_processed.columns:
                    df_processed['ds'] = dt_series
                df_processed[f'{date_col}_dayofweek'] = dt_series.dt.dayofweek
                df_processed[f'{date_col}_month'] = dt_series.dt.month
                df_processed[f'{date_col}_day'] = dt_series.dt.day
                df_processed = df_processed.drop(columns=[date_col])
            except Exception as e:
                print(f"Could not parse {date_col} as datetime: {e}")
                
        # 3. Identify and separate targets
        self.target_columns = [col for col in df_processed.columns if any(kw in col.lower() for kw in self.target_keywords)]
        if not self.target_columns:
            # If no target identified, we can't train properly. Pick the last numeric column as a fallback.
            numeric_cols = df_processed.select_dtypes(include=['number']).columns
            if numeric_cols.empty:
                return None, None
            self.target_columns = [numeric_cols[-1]]
            
        y = df_processed[self.target_columns]
        X = df_processed.drop(columns=self.target_columns)
        
        if X.empty:
            return None, None
            
        # 4. Categorical Encoding (One-Hot)
        try:
            X = pd.get_dummies(X, drop_first=True)
        except ValueError:
            # Occurs if X has no columns left to encode
            pass
            
        print(f"Shape after preprocessing: Features X: {X.shape}, Targets y: {y.shape}")
        print(f"Targets identified: {self.target_columns}")
        
        return X, y

class ProductionDemandPredictor:
    def __init__(self):
        # We instantiate locally to avoid top-level import errors
        pass
        
    def predict(self, X: pd.DataFrame, y: pd.DataFrame):
        """Trains a Prophet model on the historical data and predicts the 'next' day implicitly."""
        if X is None or X.empty or y is None or y.empty:
            return "No data to predict on!"
            
        from prophet import Prophet
        import pandas as pd
        import logging
            
        print("\n--- ML Model Training & Prediction (Prophet) ---")
        insight = "Prediction Output for Next Interval:\n"
        
        # We need a 'ds' column. If we don't have one, we generate a synthetic one ending today.
        if 'ds' not in X.columns:
            print("No 'ds' datetime column found. Generating synthetic daily index.")
            X = X.copy()
            X['ds'] = pd.date_range(end=pd.Timestamp.today(), periods=len(X), freq='D')
            
        # Suppress Prophet logs for clean stdout
        logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
        
        # Prophet is univariate, so we train a fresh model for each target
        for col in y.columns:
            print(f"Training Prophet on target: {col} with {len(X)} records...")
            # Prepare df for prophet
            df_prophet = pd.DataFrame({
                'ds': X['ds'].values,
                'y': y[col].values
            })
            
            if len(df_prophet) < 2:
                insight += f"  - Predicted {col}: {df_prophet['y'].iloc[-1]:.2f} (Not enough data for time-series forecasting, using last known value)\n"
                continue
                
            m = Prophet(daily_seasonality=False, yearly_seasonality=False, weekly_seasonality=True)
            try:
                m.fit(df_prophet)
                
                # Predict tomorrow
                future = m.make_future_dataframe(periods=1, freq='D')
                forecast = m.predict(future)
                
                # Get the last row (tomorrow)
                predicted_val = forecast.iloc[-1]['yhat']
                insight += f"  - Predicted {col}: {predicted_val:.2f}\n"
            except Exception as e:
                print(f"Prophet training failed for {col}: {e}")
                insight += f"  - Predicted {col}: {df_prophet['y'].mean():.2f} (Fallback to mean)\n"

        return insight
def main():
    # 1. Initialize components
    db = DatabaseIntrospector()
    ai_agent = MLAgent()
    feature_builder = FeatureBuilder()
    ml_model = ProductionDemandPredictor()
    
    # 2. Define the prediction target
    user_prompt = "I need to predict customer demand and staff needed for tomorrow's dinner service (evening times). The weather is expected to be Rainy and the season is Summer. Provide historical correlation data of sales and staff attendance for similar conditions."
    print("User Action:", user_prompt)
    
    # 3. Agent introspects schema
    schema_context = db.get_schema_context()
    
    # 4. Agent generates SQL
    print("\n--- AI Agent Thinking ---")
    sql_query = ai_agent.generate_sql(user_prompt, schema_context)
    print("Agent Generated SQL:\n" + sql_query)
    
    if sql_query:
        # 5. Agent Executes SQL
        df = db.execute_query(sql_query)
        
        # 6. Feature Builder formats it
        X, y = feature_builder.build_features(df)
        
        # 7. ML Model predicts
        if X is not None and y is not None:
            prediction = ml_model.predict(X, y)
            print(prediction)
        else:
            print("Not enough variables structured for Prediction.")
    else:
        print("Failed to generate SQL.")
        
    db.close()

if __name__ == "__main__":
    main()
