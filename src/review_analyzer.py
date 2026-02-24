import pandas as pd
import os
from loguru import logger

def analyze_reviews(data_dir: str = "data"):
    reviews_file = os.path.join(data_dir, "reviews_database.csv")
    
    if not os.path.exists(reviews_file):
        logger.error(f"Cannot find database at {reviews_file}")
        return
        
    logger.info("Loading review dataset...")
    df = pd.read_csv(reviews_file)
    
    # Clean Datetime columns
    logger.info("Cleaning dates and calculating KPIs...")
    df['review_date'] = pd.to_datetime(df['review_date'], format='ISO8601', utc=True)
    df['response_date'] = pd.to_datetime(df['response_date'], format='ISO8601', utc=True)
    
    # Filter Apple App Store - we know we couldn't get responses here
    # We will exclude them from the response rate / time averaging so they don't drag down the metrics inaccurately
    df_responses = df[df['platform'] != "Apple App Store"].copy()
    
    # Calculate if each review was responded to
    df_responses['has_response'] = df_responses['response_text'].notna() & (df_responses['response_text'] != '')
    
    # Calculate response time
    # Only calculate for those that have a valid response date
    valid_responses = df_responses['has_response'] & df_responses['response_date'].notna()
    
    # response time in hours
    df_responses['response_time_hours'] = pd.Series(dtype='float64')
    df_responses.loc[valid_responses, 'response_time_hours'] = (
        df_responses.loc[valid_responses, 'response_date'] - df_responses.loc[valid_responses, 'review_date']
    ).dt.total_seconds() / 3600.0
    
    # Prevent negative response times if platforms report dates slightly out of order
    df_responses['response_time_hours'] = df_responses['response_time_hours'].apply(lambda x: max(x, 0) if pd.notna(x) else x)

    # ------------------
    # AGGREGATION
    # ------------------
    logger.info("Generating Competitor Report...\n")
    
    # Group by Competitor
    grouped = df_responses.groupby('competitor').agg(
        Total_Analyzed_Reviews=('competitor', 'count'),
        Average_Star_Rating=('star_rating', 'mean'),
        Response_Rate=('has_response', lambda x: x.mean() * 100),  # percentage
        Average_Response_Time_Hours=('response_time_hours', 'mean')
    ).round(2)
    
    # Sort by how fast they reply
    grouped = grouped.sort_values('Response_Rate', ascending=False)
    
    print("="*80)
    print(f"{'OVERALL COMPETITOR CUSTOMER SUPPORT INSIGHTS (Google Play & Trustpilot)':^80}")
    print("="*80)
    print(grouped.to_string(formatters={
        'Response_Rate': '{:.1f}%'.format,
        'Average_Response_Time_Hours': '{:.1f} hrs'.format
    }))
    print("="*80)
    print("\n")
    
    
    # ------------------
    # PLATFORM BREAKDOWN
    # ------------------
    print("="*80)
    print(f"{'PLATFORM SPECIFIC BREAKDOWN':^80}")
    print("="*80)
    platform_grouped = df_responses.groupby(['platform', 'competitor']).agg(
        Reviews=('competitor', 'count'),
        Rating=('star_rating', 'mean'),
        Resp_Rate=('has_response', lambda x: x.mean() * 100),
        Avg_Resp_Time_Hrs=('response_time_hours', 'mean')
    ).round(2)
    
    print(platform_grouped.to_string(formatters={
        'Resp_Rate': '{:.1f}%'.format,
        'Avg_Resp_Time_Hrs': '{:.1f} hrs'.format
    }))
    print("="*80)

if __name__ == "__main__":
    analyze_reviews()
