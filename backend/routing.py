import requests

def get_nearby_amenities(lat, lon, amenity_type):
    # Mapping custom labels to OSM amenity tags
    osm_tags = {
        "Fire Station": "fire_station",
        "Police Station": "police",
        "Hospital": "hospital"
    }
    tag = osm_tags.get(amenity_type, amenity_type)
    
    # Overpass API (Free) to find amenities within 5km
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="{tag}"](around:5000,{lat},{lon});
      way["amenity"="{tag}"](around:5000,{lat},{lon});
      relation["amenity"="{tag}"](around:5000,{lat},{lon});
    );
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=10)
        data = response.json()
        results = []
        for element in data.get('elements', []):
            name = element.get('tags', {}).get('name', f"Unnamed {amenity_type}")
            e_lat = element.get('lat') or element.get('center', {}).get('lat')
            e_lon = element.get('lon') or element.get('center', {}).get('lon')
            if e_lat and e_lon:
                results.append({"name": name, "lat": e_lat, "lon": e_lon})
        return results[:5] # Return top 5
    except:
        return []

def get_route(start=None, end=None, start_coords=None, end_coords=None):
    # 1. Convert address to Coordinates (Geocoding) using Nominatim (Free)
    def geocode(address):
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
        headers = {'User-Agent': 'CityTwinAI/1.0'}
        try:
            res = requests.get(url, headers=headers).json()
            if res:
                return float(res[0]['lon']), float(res[0]['lat'])
        except:
            pass
        return None

    if not start_coords and start:
        start_coords = geocode(f"{start}, Chennai")
    elif start_coords:
        # If coords provided as [lat, lon], convert to [lon, lat] for OSRM
        start_coords = [start_coords[1], start_coords[0]]

    if not end_coords and end:
        end_coords = geocode(f"{end}, Chennai")
    elif end_coords:
        end_coords = [end_coords[1], end_coords[0]]

    if not start_coords or not end_coords:
        return None

    # 2. Get Route from OSRM (Free Routing Engine) with Alternatives
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}?overview=full&geometries=geojson&steps=true&alternatives=3"
    route_res = requests.get(osrm_url).json()

    if "routes" not in route_res:
        return None

    routes_list = []
    
    for idx, route_data in enumerate(route_res["routes"]):
        # OSRM returns [lon, lat], Folium needs [lat, lon]
        coords = route_data["geometry"]["coordinates"]
        route_points = [[p[1], p[0]] for p in coords]
        
        # Extract metadata
        duration_sec = route_data.get("duration", 0)
        distance_m = route_data.get("distance", 0)
        
        # --- SIMULATED TRAFFIC & PREDICTION LOGIC ---
        traffic_delay = 0
        prediction_msg = "Route clear"
        prediction_accuracy = 95
        
        if idx == 0:
            traffic_delay = 600
            prediction_msg = "Traffic congestion: expected to clear in 12 mins."
            prediction_accuracy = 88
        elif idx == 1:
            traffic_delay = 120
            prediction_msg = "Minor slowdown: clearing in 5 mins."
            prediction_accuracy = 92
        else:
            traffic_delay = 0
            prediction_msg = "Optimal flow: no predicted delays."
            prediction_accuracy = 98

        total_time_min = round((duration_sec + traffic_delay) / 60)
        
        # Extract instructions
        steps = []
        for leg in route_data.get("legs", []):
            for step in leg.get("steps", []):
                m = step.get("maneuver", {})
                m_type = m.get("type", "proceed")
                m_mod = m.get("modifier", "")
                road_name = step.get("name", "unnamed road")
                
                if m_type == "depart":
                    instr = f"Head toward {road_name}"
                elif m_type == "arrive":
                    instr = f"Arrive at destination on {road_name}"
                else:
                    instr = f"{m_type.replace('_', ' ').capitalize()} {m_mod} onto {road_name}"
                
                steps.append({
                    "instruction": instr,
                    "name": road_name,
                    "distance": step.get("distance"),
                    "location": [m.get("location")[1], m.get("location")[0]]
                })

        routes_list.append({
            "id": idx,
            "points": route_points,
            "steps": steps,
            "duration_min": total_time_min,
            "distance_km": round(distance_m / 1000, 2),
            "prediction": prediction_msg,
            "prediction_accuracy": prediction_accuracy,
            "traffic_delay_min": round(traffic_delay / 60),
            "is_recommended": False
        })

    # Recommendation Logic
    if routes_list:
        fastest_route = min(routes_list, key=lambda x: x['duration_min'])
        fastest_route['is_recommended'] = True

    return routes_list
