import os
from agent import MLAgent, DatabaseIntrospector, FeatureBuilder, ProductionDemandPredictor

def run_custom_query():
    # Initialize components
    db = DatabaseIntrospector()
    agent = MLAgent()
    feature_builder = FeatureBuilder()
    predictor = ProductionDemandPredictor()

    print("\n--- AI Demand Prediction Interface ---")
    print("Type your natural language query (or 'exit' to quit):")
    
    while True:
        try:
            user_query = input("\nQuery: ")
        except (KeyboardInterrupt, EOFError):
            break
            
        if user_query.lower() in ['exit', 'quit']:
            break
            
        try:
            # 1. Classify Intent
            intent = agent.classify_intent(user_query)
            
            if intent == "CHAT":
                print("Thinking...")
                response = agent.chat(user_query)
                print(f"\nAI: {response}")
            else:
                print("Thinking about predictions...")
                # 2. Generate SQL
                schema_context = db.get_schema_context()
                sql = agent.generate_sql(user_query, schema_context)
                print(f"\nGenerated SQL:\n{sql}")
                
                # 3. Execute SQL
                data = db.execute_query(sql)
                
                if data is not None and not data.empty:
                    print(f"\nRetrieved {len(data)} rows.")
                    
                    # 4. Build Features
                    X, y = feature_builder.build_features(data)
                    
                    if X is not None and y is not None:
                        # 5. Predict
                        prediction = predictor.predict(X, y)
                        
                        # 6. Summarize Prediction
                        print("Synthesizing final report...")
                        final_summary = agent.summarize_prediction(user_query, str(prediction))
                        print(f"\nAI: {final_summary}")
                    else:
                        print("\nNot enough valid data or recognizable targets to train on.")
                else:
                    print("\nNo data found for this query to predict on.")
                    
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    run_custom_query()
