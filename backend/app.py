from fastapi import FastAPI
from routing import get_route, get_nearby_amenities
from ai import generate_ai_response
import requests

app = FastAPI()

@app.get("/nearby")
def nearby(lat: float, lon: float, type: str):
    return {"results": get_nearby_amenities(lat, lon, type)}

@app.get("/")
def home():
    return {"message": "Backend running"}

@app.get("/weather")
def get_weather():
    try:
        # Fetching Chennai weather from wttr.in (Free/No Key)
        res = requests.get("https://wttr.in/Chennai?format=j1").json()
        curr = res['current_condition'][0]
        return {
            "temp": curr['temp_C'],
            "desc": curr['weatherDesc'][0]['value'],
            "humidity": curr['humidity'],
            "wind": curr['windspeedKmph'],
            "uv": curr['uvIndex'],
            "visibility": curr['visibility'],
            "pressure": curr['pressure'],
            "cloud": curr['cloudcover']
        }
    except:
        return {
            "temp": "28", "desc": "Clear", "humidity": "65", "wind": "12", 
            "uv": "5", "visibility": "10", "pressure": "1012", "cloud": "10"
        }

@app.get("/route")
def route(start: str = None, end: str = None, 
          start_lat: float = None, start_lon: float = None,
          end_lat: float = None, end_lon: float = None):
    
    start_coords = [start_lat, start_lon] if start_lat and start_lon else None
    end_coords = [end_lat, end_lon] if end_lat and end_lon else None
    
    routes = get_route(start, end, start_coords, end_coords)
    return {"routes": routes}

@app.get("/chat")
def chat(query: str):
    return {"response": generate_ai_response(query)}
