import json
import math
from typing import List, Dict
from scipy.stats import norm

def wilson_score(positive_ratings: float, total_ratings: int, confidence_level: float = 0.95) -> float:
    """
    Calculate Wilson Score Interval for a given rating and number of ratings.
    
    Args:
        positive_ratings (float): The number of positive ratings (converted from overall rating)
        total_ratings (int): Total number of ratings received
        confidence_level (float): Statistical confidence level between 0 and 1:
            - 0.90 for more aggressive rankings (favors newer places)
            - 0.95 for balanced rankings (default)
            - 0.99 for conservative rankings (favors established places)
    
    Returns:
        float: Lower bound of Wilson Score Interval
    """
    if total_ratings == 0:
        return 0

    if not 0 < confidence_level < 1:
        raise ValueError("Confidence level must be between 0 and 1")
    
    # Z-score for the given confidence level
    z_score = norm.ppf(1 - (1 - confidence_level) / 2)
    print(f"Debug: z_score = {z_score}")
    
    # Observed proportion of positive ratings
    observed_proportion = positive_ratings / total_ratings
    print(f"Debug: observed_proportion = {observed_proportion}")
    
    # Wilson score calculation components
    z_squared = z_score * z_score
    print(f"Debug: z_squared = {z_squared}")
    
    numerator = (observed_proportion + 
                 (z_squared / (2 * total_ratings)) - 
                 (z_score * math.sqrt((observed_proportion * (1 - observed_proportion) + 
                                     z_squared / (4 * total_ratings)) / total_ratings)))
    print(f"Debug: numerator = {numerator}")
    
    denominator = 1 + z_squared / total_ratings
    print(f"Debug: denominator = {denominator}")
    
    result = numerator / denominator
    print(f"Debug: result = {result}")
    
    return result

def rank_restaurants(input_file: str, output_file: str, confidence_level: float = 0.95):
    """
    Read restaurants from input JSON file, rank them using Wilson Score,
    and write sorted results to output JSON file.
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output JSON file
        confidence_level (float): Confidence level for Wilson Score calculation:
            - 0.90 favors newer places with fewer ratings
            - 0.95 provides balanced rankings (default)
            - 0.99 favors established places with many ratings
    """
    # Read input JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)
    
    restaurant_list = data.get('restaurants', [])
    
    # Calculate Wilson score for each restaurant
    for restaurant in restaurant_list:
        star_rating = restaurant.get('rating', 0)
        rating_count = restaurant.get('user_ratings_total', 0)
        
        # Convert 5-star rating to proportion of positive ratings
        print("star_rating: " + str(star_rating))
        positive_ratio = max(0, (star_rating - 3) / 2)
        positive_rating_count = positive_ratio * rating_count
        
        # Calculate Wilson score with specified confidence level
        print("Restaurant: " + restaurant.get('name'))
        wilson_lower_bound = wilson_score(
            positive_ratings=positive_rating_count,
            total_ratings=rating_count,
            confidence_level=confidence_level
        )
        restaurant['wilson_score'] = wilson_lower_bound
        
        # Add additional metadata about the calculation
        restaurant['ranking_metadata'] = {
            'confidence_level': confidence_level,
            'positive_ratio': positive_ratio,
            'positive_ratings': positive_rating_count
        }
    
    # Sort restaurants by Wilson score in descending order
    sorted_restaurants = sorted(
        restaurant_list,
        key=lambda restaurant: restaurant.get('wilson_score', 0),
        reverse=True
    )
    
    # Prepare output data with metadata
    output_data = {
        'restaurants': sorted_restaurants,
        'metadata': {
            'ranking_method': 'Wilson Score Interval',
            'confidence_level': confidence_level,
            'total_restaurants': len(restaurant_list),
            'ranking_interpretation': get_ranking_interpretation(confidence_level)
        }
    }
    
    # Write sorted results to output file
    with open(output_file, 'w') as file:
        json.dump(output_data, file, indent=2)

def get_ranking_interpretation(confidence_level: float) -> str:
    """
    Provides an interpretation of how the confidence level affects rankings.
    """
    if confidence_level >= 0.99:
        return "Conservative ranking: Strongly favors established places with many ratings"
    elif confidence_level >= 0.95:
        return "Balanced ranking: Moderate balance between ratings and rating count"
    elif confidence_level >= 0.90:
        return "Aggressive ranking: Gives more weight to places with high ratings but fewer reviews"
    else:
        return "Very aggressive ranking: Strongly favors high ratings regardless of review count"

if __name__ == "__main__":
    import sys
    import argparse
    import json  # Ensure json is imported

    parser = argparse.ArgumentParser(description='Rank restaurants using Wilson Score Interval')
    parser.add_argument('input_file', help='Input JSON file path')
    parser.add_argument('output_file', help='Output JSON file path')
    parser.add_argument('--confidence', type=float, default=0.95,
                        help='Confidence level (0.90, 0.95, or 0.99)')
    
    args = parser.parse_args()  # Correctly parse the arguments

    # Call the rank_restaurants function with parsed arguments
    rank_restaurants(args.input_file, args.output_file, args.confidence)