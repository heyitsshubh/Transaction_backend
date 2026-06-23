import os
import json
import time
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def classify_transactions_batch(transactions_batch, retries=3):
    """
    Classify a batch of transactions using Gemini.
    """
    prompt = f"""
    You are a financial transaction classification system.
    Please classify the following batch of transactions into one of these categories:
    Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, Other.

    Return the result ONLY as a valid JSON array of objects, where each object has 'txn_id' and 'category'.
    Do not add any markdown formatting or backticks around the JSON.
    
    Transactions:
    {json.dumps(transactions_batch)}
    """
    
    delay = 2
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                print(f"LLM Classification failed after {retries} attempts: {e}")
                return None

def generate_narrative_summary(summary_data, retries=3):
    """
    Generate a 2-3 sentence spending narrative and assign a risk level (low/medium/high).
    """
    prompt = f"""
    You are an AI financial analyst. Review the following aggregated transaction data and provide:
    1. A 2-3 sentence narrative summarizing the spending behavior.
    2. A risk_level of "low", "medium", or "high" based on the anomaly count and spending patterns.
    
    Data:
    {json.dumps(summary_data)}
    
    Return the result ONLY as a valid JSON object with keys "narrative" and "risk_level".
    Do not add any markdown formatting or backticks around the JSON.
    """
    
    delay = 2
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                print(f"LLM Narrative failed after {retries} attempts: {e}")
                return {"narrative": "Failed to generate narrative.", "risk_level": "unknown"}
