"""
RestoCopilot AI - SerpApi Google Maps Reviews Integrator
Fetches live customer reviews and restaurant metadata from Google Maps via SerpApi.
"""

import os
import requests
from typing import Dict, Any, List

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

def _load_env_key() -> str:
    # Check os.environ first
    key = os.getenv("SERPAPI_API_KEY", "").strip()
    if key:
        return key
    # Parse .env directly
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SERPAPI_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return ""

def fetch_google_maps_reviews(restaurant_query: str, api_key: str = None, num_reviews: int = 10) -> Dict[str, Any]:
    """
    Fetches Google Maps reviews and place profile for a given restaurant query or place ID.
    Supports real SerpApi queries if an API key is provided, with realistic simulation fallback.
    """
    key = api_key or _load_env_key()
    
    if key:
        try:
            # Step 1: Search for the restaurant on Google Maps
            search_params = {
                "engine": "google_maps",
                "q": restaurant_query,
                "api_key": key
            }
            res = requests.get(SERPAPI_ENDPOINT, params=search_params, timeout=14)
            if res.status_code == 200:
                data = res.json()
                
                place_info = {}
                data_id = None
                reviews_list = []
                
                # Check place_results
                if "place_results" in data:
                    pr = data["place_results"]
                    place_info = {
                        "title": pr.get("title", restaurant_query),
                        "rating": pr.get("rating", 4.3),
                        "reviews_count": pr.get("reviews", 150),
                        "address": pr.get("address", "New Delhi, India"),
                        "price": pr.get("price", "₹₹"),
                        "thumbnail": pr.get("thumbnail", "")
                    }
                    data_id = pr.get("data_id")
                    
                    # Direct user_reviews inside place_results
                    if "user_reviews" in pr and "most_relevant" in pr["user_reviews"]:
                        for r in pr["user_reviews"]["most_relevant"]:
                            reviews_list.append({
                                "author": r.get("username", "Google Diner"),
                                "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&auto=format&fit=crop",
                                "rating": int(r.get("rating", 5)),
                                "date": r.get("date", "Recent"),
                                "snippet": r.get("description", ""),
                                "likes": 0,
                                "source": "Google Maps (Live SerpApi)"
                            })
                            
                elif "local_results" in data and len(data["local_results"]) > 0:
                    lr = data["local_results"][0]
                    place_info = {
                        "title": lr.get("title", restaurant_query),
                        "rating": lr.get("rating", 4.3),
                        "reviews_count": lr.get("reviews", 150),
                        "address": lr.get("address", "New Delhi, India"),
                        "price": lr.get("price", "₹₹"),
                        "thumbnail": lr.get("thumbnail", "")
                    }
                    data_id = lr.get("data_id")
                
                # Step 2: If data_id exists, fetch deeper reviews with google_maps_reviews engine
                if data_id:
                    rev_params = {
                        "engine": "google_maps_reviews",
                        "data_id": data_id,
                        "sort_by": "newestFirst",
                        "api_key": key
                    }
                    rev_res = requests.get(SERPAPI_ENDPOINT, params=rev_params, timeout=12)
                    if rev_res.status_code == 200:
                        rev_data = rev_res.json()
                        raw_reviews = rev_data.get("reviews", [])
                        if raw_reviews:
                            reviews_list = [] # replace with detailed reviews
                            for r in raw_reviews[:num_reviews]:
                                snippet = r.get("snippet", r.get("extracted_snippet", {}).get("original", ""))
                                reviews_list.append({
                                    "author": r.get("user", {}).get("name", "Google Diner"),
                                    "avatar": r.get("user", {}).get("thumbnail", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop"),
                                    "rating": int(r.get("rating", 5)),
                                    "date": r.get("date", "Recent"),
                                    "snippet": snippet,
                                    "likes": r.get("likes", 0),
                                    "source": "Google Maps (Live SerpApi)"
                                })
                                
                if reviews_list:
                    return {
                        "status": "SUCCESS",
                        "is_live_api": True,
                        "restaurant": place_info,
                        "reviews": reviews_list
                    }
        except Exception as e:
            print(f"SerpApi Error: {e}, falling back to intelligent simulator...")
            
    # Fallback if key missing or request fails
    return get_simulated_google_maps_reviews(restaurant_query)


def get_simulated_google_maps_reviews(restaurant_query: str) -> Dict[str, Any]:
    """
    Returns realistic simulated Google Maps reviews tailored to the restaurant query.
    Enables instant testing without consuming paid API credits.
    """
    cleaned_name = restaurant_query.strip().title() or "Royal Spice Bistro"
    
    place_info = {
        "title": cleaned_name,
        "rating": 4.4,
        "reviews_count": 842,
        "address": "Connaught Place, Inner Circle, New Delhi, India",
        "price": "₹₹",
        "thumbnail": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&auto=format&fit=crop"
    }
    
    simulated_reviews = [
        {
            "author": "Aarav Mehra",
            "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&auto=format&fit=crop",
            "rating": 5,
            "date": "2 days ago",
            "snippet": f"Celebrated our anniversary at {cleaned_name}. The Dal Makhani was simmered to perfection and the Garlic Naan was exceptionally crisp! Service by Rahul was attentive and warm. Will definitely return!",
            "likes": 4,
            "source": "Google Maps (Simulated Stream)"
        },
        {
            "author": "Sunita Aggarwal",
            "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop",
            "rating": 2,
            "date": "Yesterday",
            "snippet": f"The Butter Chicken flavor was decent, but our food took 40 minutes to arrive and came to the table lukewarm. Staff seemed hurried and ignored our request for extra butter naan twice.",
            "likes": 7,
            "source": "Google Maps (Simulated Stream)"
        },
        {
            "author": "Dr. Kabir Roy",
            "avatar": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100&auto=format&fit=crop",
            "rating": 5,
            "date": "3 days ago",
            "snippet": "Outstanding culinary consistency! The Paneer Tikka had that authentic smokey tandoor aroma and the mint chutney was refreshing. Clean washrooms and great hygiene standards.",
            "likes": 2,
            "source": "Google Maps (Simulated Stream)"
        },
        {
            "author": "Neha Malhotra",
            "avatar": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=100&auto=format&fit=crop",
            "rating": 1,
            "date": "5 days ago",
            "snippet": "Terrible experience with billing. We were charged for two bottled waters we never ordered, and when we pointed it out to the counter, they argued with us before reversing it. Zero hospitality.",
            "likes": 12,
            "source": "Google Maps (Simulated Stream)"
        },
        {
            "author": "Vikram Sethi",
            "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop",
            "rating": 4,
            "date": "1 week ago",
            "snippet": "Very nice family restaurant. Good portion sizes and generous paneer cubes. The Gulab Jamun dessert with rabri was a fantastic finish. Slightly noisy during Saturday peak hours.",
            "likes": 3,
            "source": "Google Maps (Simulated Stream)"
        }
    ]
    
    return {
        "status": "SUCCESS",
        "is_live_api": False,
        "restaurant": place_info,
        "reviews": simulated_reviews
    }
