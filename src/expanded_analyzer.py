import pandas as pd
import os
from loguru import logger

def analyze_expanded_metrics():
    # 1. Total review volumes
    metrics_file = "data/metrics_database.csv"
    if os.path.exists(metrics_file):
        df_m = pd.read_csv(metrics_file)
        df_rc = df_m[df_m['metric_type'] == 'review_count']
        df_rc = df_rc.sort_values('timestamp').drop_duplicates(subset=['competitor', 'platform'], keep='last')
        
        print("\n" + "="*80)
        print("TOTAL REVIEW VOLUMES BY COMPETITOR AND PLATFORM")
        print("="*80)
        volumes = df_rc.groupby(['competitor', 'platform'])['value'].sum().unstack(fill_value=0).sort_index()
        volumes['Total'] = volumes.sum(axis=1)
        volumes = volumes.sort_values('Total', ascending=False)
        print(volumes.to_string(float_format="{:,.0f}".format))
    
    # 2. Response Quality (Boilerplate / Uniqueness)
    reviews_file = "data/reviews_database.csv"
    if os.path.exists(reviews_file):
        df_r = pd.read_csv(reviews_file)
        
        df_resp = df_r[(df_r['response_text'].notna()) & (df_r['response_text'] != '')].copy()
        
        print("\n" + "="*80)
        print("DEVELOPER RESPONSE QUALITY (UNIQUENESS) BY PLATFORM (Google Play & Trustpilot)")
        print("="*80)
        
        def calculate_quality(group):
            total_responses = len(group)
            if total_responses == 0:
                return pd.Series({'Total': 0, 'Unique': 0, 'Uniqueness %': 0.0, 'Avg Length': 0.0})
            unique_responses = group['response_text'].nunique()
            avg_length = group['response_text'].str.len().mean()
            return pd.Series({
                'Total Resp': total_responses,
                'Unique Resp': unique_responses,
                'Uniq %': (unique_responses / total_responses) * 100,
                'Avg Len': avg_length
            })
            
        quality_df = df_resp.groupby(['competitor', 'platform']).apply(calculate_quality).round(1)
        print(quality_df.to_string())
        
        # 3. Sentiment Breakdown
        print("\n" + "="*80)
        print("SENTIMENT DISTRIBUTION BY PLATFORM (1-5 Stars)")
        print("="*80)
        
        def calculate_sentiment(group):
            total = len(group)
            if total == 0:
                return pd.Series()
            
            p_1 = (len(group[group['star_rating'] == 1.0]) / total) * 100
            p_2 = (len(group[group['star_rating'] == 2.0]) / total) * 100
            p_3 = (len(group[group['star_rating'] == 3.0]) / total) * 100
            p_4 = (len(group[group['star_rating'] == 4.0]) / total) * 100
            p_5 = (len(group[group['star_rating'] == 5.0]) / total) * 100
            
            return pd.Series({
                'Total Sample': total,
                '1* %': p_1,
                '2* %': p_2,
                '3* %': p_3,
                '4* %': p_4,
                '5* %': p_5,
            })
            
        sentiment_df = df_r.groupby(['competitor', 'platform']).apply(calculate_sentiment).round(1)
        print(sentiment_df.to_string())
        
        # 4. Response speed and rate
        print("\n" + "="*80)
        print("RESPONSE SPEED AND RATE BY PLATFORM (Google Play & Trustpilot)")
        print("="*80)
        # Exclude Apple from Response Tracking since we can't scrape responses there
        df_for_speed = df_r[df_r['platform'] != "Apple App Store"].copy()
        df_for_speed['review_date'] = pd.to_datetime(df_for_speed['review_date'], format='ISO8601', utc=True)
        df_for_speed['response_date'] = pd.to_datetime(df_for_speed['response_date'], format='ISO8601', utc=True)
        df_for_speed['has_response'] = df_for_speed['response_text'].notna() & (df_for_speed['response_text'] != '')
        valid_responses = df_for_speed['has_response'] & df_for_speed['response_date'].notna()
        df_for_speed['response_time_hours'] = pd.Series(dtype='float64')
        df_for_speed.loc[valid_responses, 'response_time_hours'] = (
            df_for_speed.loc[valid_responses, 'response_date'] - df_for_speed.loc[valid_responses, 'review_date']
        ).dt.total_seconds() / 3600.0
        df_for_speed['response_time_hours'] = df_for_speed['response_time_hours'].apply(lambda x: max(x, 0) if pd.notna(x) else x)
        
        speed_df = df_for_speed.groupby(['competitor', 'platform']).agg(
            Resp_Rate_Pct=('has_response', lambda x: x.mean() * 100),
            Avg_Resp_Time_Hrs=('response_time_hours', 'mean')
        ).round(1)
        print(speed_df.to_string())

if __name__ == "__main__":
    analyze_expanded_metrics()
