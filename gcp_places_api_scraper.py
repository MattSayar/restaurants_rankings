import requests
import json
import math
from typing import List, Dict, Set
from dataclasses import dataclass

@dataclass
class Coordinates:
    latitude: float
    longitude: float

class RestaurantFinder:
    def __init__(self, api_key: str, center_lat: float, center_lng: float, radius_km: float):
        self.api_key = api_key
        self.center = Coordinates(latitude=center_lat, longitude=center_lng)
        self.radius_km = radius_km
        self.seen_place_ids: Set[str] = set()
        self.results: List[Dict] = []
        self.base_url = "https://places.googleapis.com/v1/places:searchNearby"
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName.text,places.primaryTypeDisplayName.text,places.rating,places.id,places.shortFormattedAddress,places.userRatingCount,places.location,places.googleMapsUri"
        }

    def _calculate_new_coordinates(self, center: Coordinates, distance_km: float, bearing: float) -> Coordinates:
        """Calculate new coordinates given a starting point, distance, and bearing."""
        R = 6371  # Earth's radius in kilometers
        
        lat1 = math.radians(center.latitude)
        lon1 = math.radians(center.longitude)
        bearing = math.radians(bearing)
        
        lat2 = math.asin(
            math.sin(lat1) * math.cos(distance_km/R) +
            math.cos(lat1) * math.sin(distance_km/R) * math.cos(bearing)
        )
        
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(distance_km/R) * math.cos(lat1),
            math.cos(distance_km/R) - math.sin(lat1) * math.sin(lat2)
        )
        
        return Coordinates(
            latitude=math.degrees(lat2),
            longitude=math.degrees(lon2)
        )

    def _get_restaurants_for_location(self, location: Coordinates, radius_meters: float) -> List[Dict]:
        """Make API call to get restaurants for a specific location and radius."""
        payload = {
            "includedTypes": ["restaurant"],
            "maxResultCount": 20,
            "rankPreference": "DISTANCE",
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": location.latitude,
                        "longitude": location.longitude
                    },
                    "radius": radius_meters
                }
            }
        }
        
        response = requests.post(self.base_url, headers=self.headers, json=payload)
        return response.json().get("places", [])

    def _process_results(self, places: List[Dict]) -> None:
        """Process and deduplicate restaurant results."""
        print(f"Processing {len(places)} places.")
        for place in places:
            place_id = place.get("id")
            if place_id and place_id not in self.seen_place_ids:
                self.seen_place_ids.add(place_id)
                
                processed_result = {
                    "name": place.get("displayName", {}).get("text"),
                    "place_id": place_id,
                    "type": place.get("primaryTypeDisplayName", {}).get("text"),
                    "rating": place.get("rating"),
                    "user_ratings_total": place.get("userRatingCount"),
                    "location": place.get("location"),
                    "address": place.get("shortFormattedAddress"),
                    "maps_url": place.get("googleMapsUri")
                }
                
                self.results.append(processed_result)

    def find_all_restaurants(self) -> List[Dict]:
        """Find all restaurants within the specified radius."""
        # Calculate smaller search radius to handle API limit
        # Using 500m radius for each search to ensure overlap and complete coverage
        search_radius_km = 0.5
        search_radius_meters = search_radius_km * 1000
        
        # Calculate number of circles needed
        num_circles = math.ceil(self.radius_km / (search_radius_km * 1.5))  # 1.5 for overlap
        
        # Create grid of search points
        for ring in range(num_circles):
            if ring == 0:
                # Search center point
                restaurants = self._get_restaurants_for_location(
                    self.center,
                    search_radius_meters
                )
                self._process_results(restaurants)
            else:
                # Calculate points around the ring
                ring_radius_km = ring * (search_radius_km * 1.5)
                num_points = max(8 * ring, 8)  # Increase points for outer rings
                
                for i in range(num_points):
                    bearing = (360 / num_points) * i
                    location = self._calculate_new_coordinates(
                        self.center,
                        ring_radius_km,
                        bearing
                    )
                    
                    restaurants = self._get_restaurants_for_location(
                        location,
                        search_radius_meters
                    )
                    self._process_results(restaurants)
        
        # Sort results by rating (highest first)
        print(f"Found {len(self.results)} restaurants.")
        self.results.sort(
            key=lambda x: (
                x.get("rating") if x.get("rating") is not None else 0,
                x.get("user_ratings_total") if x.get("user_ratings_total") is not None else 0
            ),
            reverse=True
        )
        return self.results

def main():
    # Replace with your API key
    API_KEY = open('gcp_key.txt').read().strip()
    
    # Colorado Springs coordinates
    CENTER_LAT = 38.878400
    CENTER_LNG = -104.767914
    RADIUS_KM = 15
    
    finder = RestaurantFinder(API_KEY, CENTER_LAT, CENTER_LNG, RADIUS_KM)
    results = finder.find_all_restaurants()
    
    # Save results to JSON file
    with open("restaurants.json", "w", encoding="utf-8") as f:
        json.dump({"restaurants": results}, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()