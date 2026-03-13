import os
from dotenv import load_dotenv
from agent import MLAgent, DatabaseIntrospector, FeatureBuilder, ProductionDemandPredictor

load_dotenv()

test_cases = [
    # Basic Time-Series Interpolations
    "Predict total sales for tomorrow based on the last 30 days.",
    "Predict the number of customers and required staff for next Monday using data from the past two months.",
    "Forecast our expected revenue for this upcoming weekend (Saturday and Sunday).",
    
    # Categorical/Segmented Prophecy
    "Predict the total items sold on the next 'Rainy' day based on historical rainy days.",
    "Forecast demand and staff needed for tomorrow if we assume the Season is 'Summer'.",
    
    # Granular Grouping
    "Based on historical data, predict how many parties of size 4 or more will reserve a table next Friday.",
    "Forecast the total revenue generated specifically during dinner hours tomorrow.",
    
    # Edge Cases & Ambiguities
    "Predict sales for the next 3 days.",
    "What will be our peak staff requirement next week?",
    "Forecast the number of unique customers we will serve tomorrow.",
    
    # Chatbot Routing Fallbacks
    "What is the best item on the menu?",
    "Can you predict the weather for tomorrow?",
    
    # Multi-Variable Interdependence
    "Predict the total sales amount tomorrow if the weather is 'Sunny' and the season is 'Winter'."
]

def run_prophet_tests():
    db = DatabaseIntrospector()
    agent = MLAgent()
    feature_builder = FeatureBuilder()
    predictor = ProductionDemandPredictor()
    
    output_markdown = "# Prophet ML Pipeline Test Results\n\n"
    output_markdown += "This document tracks the execution of 12+ complex test cases against the **Facebook Prophet** machine learning pipeline to ensure robust SQL generation, Feature Building ('ds' enforcement), and dynamic algorithm training.\n\n"
    
    for i, test in enumerate(test_cases, 1):
        print(f"Running Test {i}/{len(test_cases)}...")
        output_markdown += f"## Test Case {i}: {test}\n"
        
        try:
            intent = agent.classify_intent(test)
            output_markdown += f"**Intent:** `{intent}`\n\n"
            
            if intent == "CHAT":
                response = agent.chat(test)
                output_markdown += f"**LLM Chatbot Response:**\n> {response}\n\n"
            else:
                schema_context = db.get_schema_context()
                sql = agent.generate_sql(test, schema_context)
                
                output_markdown += f"**Generated SQL:**\n```sql\n{sql}\n```\n\n"
                
                if not sql:
                    output_markdown += "> ❌ **Failed to generate SQL.**\n\n"
                    continue
                    
                data = db.execute_query(sql)
                
                if data is not None and not data.empty:
                    output_markdown += f"**SQL Execution:** Retrieved {len(data)} rows.\n\n"
                    X, y = feature_builder.build_features(data)
                    
                    if X is not None and y is not None:
                        output_markdown += f"**Feature Builder:** Extracted {X.shape[1]} features and {y.shape[1]} targets.\n\n"
                        prediction = predictor.predict(X, y)
                        output_markdown += f"**Prophet Output:**\n```text\n{prediction}\n```\n\n"
                        
                        final_summary = agent.summarize_prediction(test, str(prediction))
                        output_markdown += f"**Final LLM Synthesis:**\n> {final_summary}\n\n"
                    else:
                        output_markdown += "> ⚠️ **Feature Builder:** Not enough valid data or recognizable targets to spin up Prophet.\n\n"
                        
                        # Test edge-case fallback summarizer
                        final_summary = agent.summarize_prediction(test, "Not enough data to predict on.")
                        output_markdown += f"**LLM Fallback Synthesis:**\n> {final_summary}\n\n"
                else:
                    output_markdown += "> ⚠️ **SQL Execution:** No data retrieved for this query.\n\n"
                    
        except Exception as e:
            output_markdown += f"> ❌ **Fatal Error:** {e}\n\n"
            
        output_markdown += "---\n\n"
        
    db.close()
    
    with open("PROPHET_TEST_RESULTS.md", "w") as f:
        f.write(output_markdown)
        
    print("Test suite complete. Output written to PROPHET_TEST_RESULTS.md")

if __name__ == "__main__":
    run_prophet_tests()
