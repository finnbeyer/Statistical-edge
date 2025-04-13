import pandas as pd
import numpy as np
from collections import Counter
import logging
from typing import Dict, Tuple, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load and prepare the data for analysis.
    
    Args:
        file_path: Path to the CSV file containing candle data
        
    Returns:
        DataFrame with prepared data
    """
    try:
        df = pd.read_csv(file_path, sep=';')
        df['Date'] = pd.to_datetime(df['Date'])
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['Week'] = df['Date'].dt.isocalendar().week
        df['Year'] = df['Date'].dt.isocalendar().year
        return df
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise

def analyze_monday_ranges(df: pd.DataFrame) -> Tuple[int, int, int, int, Dict[int, int], Dict[int, int]]:
    """
    Analyze Monday ranges and track when they are broken.
    
    Args:
        df: DataFrame containing the candle data
        
    Returns:
        Tuple containing:
        - total_mondays: Total number of Mondays analyzed
        - monday_highs_taken: Number of times Monday's high was broken
        - monday_lows_taken: Number of times Monday's low was broken
        - both_broken: Number of times both high and low were broken
        - day_high_break: Counter of which days broke Monday's high
        - day_low_break: Counter of which days broke Monday's low
    """
    monday_highs_taken = 0
    monday_lows_taken = 0
    both_broken = 0
    total_mondays = 0
    day_high_break = Counter()
    day_low_break = Counter()

    for (week, year), week_data in df.groupby(['Week', 'Year']):
        monday_data = week_data[week_data['DayOfWeek'] == 0]
        if len(monday_data) == 0:
            continue
            
        total_mondays += 1
        monday_high = monday_data['High'].iloc[0]
        monday_low = monday_data['Low'].iloc[0]
        
        rest_of_week = week_data[week_data['DayOfWeek'].isin([1,2,3,4])]
        
        # Check high break
        high_break_days = rest_of_week[rest_of_week['High'] > monday_high]
        high_broken = not high_break_days.empty
        if high_broken:
            monday_highs_taken += 1
            first_break_day = high_break_days['DayOfWeek'].iloc[0]
            day_high_break[first_break_day] += 1
        
        # Check low break
        low_break_days = rest_of_week[rest_of_week['Low'] < monday_low]
        low_broken = not low_break_days.empty
        if low_broken:
            monday_lows_taken += 1
            first_break_day = low_break_days['DayOfWeek'].iloc[0]
            day_low_break[first_break_day] += 1
            
        # Track weeks where both were broken
        if high_broken and low_broken:
            both_broken += 1

    return total_mondays, monday_highs_taken, monday_lows_taken, both_broken, day_high_break, day_low_break

def calculate_probabilities(
    total_mondays: int,
    monday_highs_taken: int,
    monday_lows_taken: int,
    both_broken: int,
    day_high_break: Dict[int, int],
    day_low_break: Dict[int, int]
) -> Tuple[float, float, Dict[str, float], Dict[str, float]]:
    """
    Calculate various probabilities from the analysis results.
    
    Args:
        total_mondays: Total number of Mondays analyzed
        monday_highs_taken: Number of times Monday's high was broken
        monday_lows_taken: Number of times Monday's low was broken
        both_broken: Number of times both high and low were broken
        day_high_break: Counter of which days broke Monday's high
        day_low_break: Counter of which days broke Monday's low
        
    Returns:
        Tuple containing:
        - high_break_prob: Probability of Monday's high being broken
        - low_break_prob: Probability of Monday's low being broken
        - day_high_probs: Dictionary of day-specific probabilities for high breaks
        - day_low_probs: Dictionary of day-specific probabilities for low breaks
    """
    high_break_prob = monday_highs_taken / total_mondays if total_mondays > 0 else 0
    low_break_prob = monday_lows_taken / total_mondays if total_mondays > 0 else 0
    
    day_names = {1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday'}
    day_high_probs = {day_names[day]: count/monday_highs_taken if monday_highs_taken > 0 else 0 
                     for day, count in day_high_break.items()}
    day_low_probs = {day_names[day]: count/monday_lows_taken if monday_lows_taken > 0 else 0 
                    for day, count in day_low_break.items()}
    
    return high_break_prob, low_break_prob, day_high_probs, day_low_probs

def print_results(
    total_mondays: int,
    monday_highs_taken: int,
    monday_lows_taken: int,
    both_broken: int,
    high_break_prob: float,
    low_break_prob: float,
    day_high_probs: Dict[str, float],
    day_low_probs: Dict[str, float]
) -> None:
    """
    Print the analysis results in a formatted way.
    """
    print("\n=== Monday Range Analysis ===")
    print(f"Total number of Mondays analyzed: {total_mondays}")
    
    print(f"\nHigh Break Analysis:")
    print(f"Number of times Monday's high was broken: {monday_highs_taken}")
    print(f"Probability of Monday's high being broken: {high_break_prob:.2%}")
    print("\nDay-specific probabilities for high breaks:")
    for day, prob in day_high_probs.items():
        print(f"{day}: {prob:.2%}")
    
    print(f"\nLow Break Analysis:")
    print(f"Number of times Monday's low was broken: {monday_lows_taken}")
    print(f"Probability of Monday's low being broken: {low_break_prob:.2%}")
    print("\nDay-specific probabilities for low breaks:")
    for day, prob in day_low_probs.items():
        print(f"{day}: {prob:.2%}")
    
    # Calculate combined probability using the correct formula: P(A or B) = P(A) + P(B) - P(A and B)
    either_break_prob = (monday_highs_taken + monday_lows_taken - both_broken) / total_mondays if total_mondays > 0 else 0
    print(f"\nProbability of either Monday's high or low being broken: {either_break_prob:.2%}")

def main():
    try:
        # Load and prepare data
        df = load_data('filtered_candles.csv')
        
        # Analyze Monday ranges
        total_mondays, monday_highs_taken, monday_lows_taken, both_broken, day_high_break, day_low_break = analyze_monday_ranges(df)
        
        # Calculate probabilities
        high_break_prob, low_break_prob, day_high_probs, day_low_probs = calculate_probabilities(
            total_mondays, monday_highs_taken, monday_lows_taken, both_broken, day_high_break, day_low_break
        )
        
        # Print results
        print_results(
            total_mondays, monday_highs_taken, monday_lows_taken, both_broken,
            high_break_prob, low_break_prob, day_high_probs, day_low_probs
        )
        
    except Exception as e:
        logger.error(f"An error occurred during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main() 