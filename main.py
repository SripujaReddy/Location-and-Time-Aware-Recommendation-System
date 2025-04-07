from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import requests

app = FastAPI()

# Load templates
templates = Jinja2Templates(directory="templates")

# Nominatim API URL
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Function to get recommendations based on time of day
def get_recommendations(lat, lon, keywords):
    recommendations = []
    headers = {'User-Agent': 'my-fastapi-app/1.0'}
    
    for keyword in keywords:
        params = {
            'q': keyword,
            'format': 'json',
            'limit': 5,  
            'viewbox': f"{lon-0.1},{lat-0.1},{lon+0.1},{lat+0.1}",  # ✅ Correct format: lon, lat order
            'bounded': 1
        }
        print(f"Query for '{keyword}': {params}")

        try:
            response = requests.get(NOMINATIM_URL, params=params, headers=headers)
            print(f"Response Status for '{keyword}': {response.status_code}")
            print(f"Response Content for '{keyword}': {response.text[:300]}")

            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                continue

            results = response.json()
            if not results:
                print(f"No results for '{keyword}'")

            for place in results:
                name = place.get('display_name')
                latitude = place.get('lat')
                longitude = place.get('lon')

                if name and latitude and longitude:
                    recommendations.append({
                        'name': name,
                        'latitude': float(latitude),
                        'longitude': float(longitude)
                    })

        except requests.exceptions.RequestException as e:
            print(f"Request error for '{keyword}': {e}")
        except Exception as e:
            print(f"Parsing error for '{keyword}': {e}")

    if not recommendations:
        print("No recommendations found after all attempts.")
        
    return recommendations

# Route for frontend
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Route to fetch recommendations
@app.get("/recommend")
async def recommend(lat: float, lon: float):
    hour = datetime.now().hour

    if 5 <= hour < 12:
        keywords = ['cafe', 'park']  
    elif 12 <= hour < 17:
        keywords = ['restaurant', 'museum', 'mall']  
    elif 17 <= hour < 21:
        keywords = ['bar', 'restaurant', 'movie theater', 'park']  
    else:
        keywords = ['night club', 'diner', 'store']  

    print(f"Fetching recommendations for lat={lat}, lon={lon}, hour={hour}")

    recommendations = get_recommendations(lat, lon, keywords)

    if not recommendations:
        return JSONResponse({"message": "No recommendations found. Try again later."}, status_code=404)

    return JSONResponse({"recommendations": recommendations})
