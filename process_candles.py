import pandas as pd
import locale
from datetime import datetime
import logging
from typing import Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_german_date(date_str: str) -> Optional[datetime]:
    """
    Parse a German date string into a datetime object.
    
    Args:
        date_str: Date string in German format (e.g., "Montag, 1. Januar 2024")
        
    Returns:
        datetime object if parsing successful, None otherwise
    """
    try:
        return pd.to_datetime(date_str, format='%A, %d. %B %Y')
    except Exception as e:
        logger.warning(f"Failed to parse date: {date_str}. Error: {str(e)}")
        return None

def process_candles(input_file: str, output_file: str) -> None:
    """
    Process candle data from a CSV file, filter for weeks with Mondays, and save to a new file.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to save the filtered CSV file
    """
    try:
        # Set locale to German
        locale.setlocale(locale.LC_TIME, 'German')
        
        # Read the CSV file
        logger.info(f"Reading data from {input_file}")
        df = pd.read_csv(input_file, sep=';', encoding='latin1')
        
        # Translate column headers to English
        df.columns = ['Date', 'Close', 'Open', 'High', 'Low']
        
        # Convert German date strings to datetime objects
        df['Date'] = df['Date'].apply(parse_german_date)
        
        # Remove any rows where date parsing failed
        df = df.dropna(subset=['Date'])
        
        # Add a week number column
        df['Week'] = df['Date'].dt.isocalendar().week
        df['Year'] = df['Date'].dt.isocalendar().year
        
        # Add a day of week column (Monday=0, Sunday=6)
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        
        # Find weeks that have a Monday
        weeks_with_monday = df[df['DayOfWeek'] == 0][['Week', 'Year']].drop_duplicates()
        
        # Filter the dataframe to only keep weeks that have a Monday
        filtered_df = pd.merge(df, weeks_with_monday, on=['Week', 'Year'])
        
        # Sort by date
        filtered_df = filtered_df.sort_values('Date')
        
        # Drop the helper columns
        filtered_df = filtered_df.drop(['Week', 'Year', 'DayOfWeek'], axis=1)
        
        # Save to new CSV file
        logger.info(f"Saving filtered data to {output_file}")
        filtered_df.to_csv(output_file, index=False, sep=';', date_format='%Y-%m-%d')
        
        logger.info(f"Processing complete!")
        logger.info(f"Original number of rows: {len(df)}")
        logger.info(f"Filtered number of rows: {len(filtered_df)}")
        
    except Exception as e:
        logger.error(f"An error occurred during processing: {str(e)}")
        raise

if __name__ == "__main__":
    process_candles('CME_DL_6E1!, 1D (2).csv', 'filtered_candles.csv') 