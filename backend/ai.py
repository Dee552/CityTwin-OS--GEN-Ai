import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("OPENROUTER_API_KEY")

def get_keyword_fallback(query):
    """Local safety layer for disasters and emergencies"""
    query = query.lower()
    if any(w in query for w in ["fire", "smoke", "burn", "gas leak"]):
        return "SERVICE: Fire Station | ADVICE: Evacuate immediately. Stay low to avoid smoke inhalation."
    if any(w in query for w in ["robbery", "thief", "crime", "police", "fight"]):
        return "SERVICE: Police Station | ADVICE: Lock all doors and call 100. Do not confront suspects."
    if any(w in query for w in ["hospital", "ambulance", "heart", "unconscious", "bleeding"]):
        return "SERVICE: Hospital | ADVICE: Keep the person warm. Apply pressure to wounds. Stay on the line for 108."
    if any(w in query for w in ["flood", "rain", "waterlogging", "cyclone", "storm"]):
        return "SERVICE: Hospital/Police | ADVICE: Move to the highest floor. Avoid walking through water. Stay away from power lines."
    return None

def generate_ai_response(query):
    # Expanded System Prompt with Rain & Flood expertise
    SYSTEM_PROMPT = """
    You are 'CityTwin AI', the advanced Urban Intelligence System for Chennai.
    Your goal is to be a helpful, comprehensive city companion.
    
    CORE CAPABILITIES:
    1. Navigation & Places: Provide details on how to reach locations, suggest popular spots, and explain traffic patterns.
    2. Urban Facts: Answer questions about Chennai's history, landmarks, and infrastructure.
    3. Emergency & Safety: Maintain high expertise in disaster management (floods, rains) and emergency services.
    4. General Assistance: Help with any query the user has, maintain a professional and helpful tone.

    STRICT RULES:
    - If the user asks about a specific place or route, provide helpful context or advice.
    - For emergencies (fire, police, medical), ALWAYS start with 'SERVICE: [Type]' followed by safety advice.
    - Be concise, professional, and data-driven.
    - If a query is completely unrelated to anything useful (gibberish), politely guide them back to city services.
    """

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    models = [
        "openrouter/auto", # Automatically routes to the best available free model
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-r1:free",
        "mistralai/mistral-small-24b-instruct-2501:free",
        "google/gemma-2-9b-it:free"
    ]

    for model in models:
        try:
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                "temperature": 0.4,
                "top_p": 0.9
            }
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            
            # If the specific model failed, log the specific provider error and try the next one
            if "error" in result:
                err_msg = result['error'].get('message', 'Unknown Error')
                print(f"Model {model} failed: {err_msg}") # Server-side log
                continue 
                
        except Exception as e:
            print(f"Connection error for {model}: {str(e)}")
            continue

    fallback = get_keyword_fallback(query)
    if fallback:
        return f"🚨 (System Offline - Local Safety Mode) {fallback}"
    
    return f"I am CityTwin AI, currently operating in Limited Connectivity Mode. I can assist with emergency routing and basic city safety. How can I help with '{query}'?"
