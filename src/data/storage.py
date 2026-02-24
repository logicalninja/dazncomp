import pandas as pd
import os
from datetime import datetime
from loguru import logger

class StorageManager:
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Metrics setup
        self.metrics_columns = ['timestamp', 'competitor', 'platform', 'metric_type', 'value']
        self.metrics_file = os.path.join(self.output_dir, "metrics_database.csv")
        if not os.path.exists(self.metrics_file):
            df = pd.DataFrame(columns=self.metrics_columns)
            df.to_csv(self.metrics_file, index=False)
            
        # Reviews setup
        self.reviews_columns = ['scrape_timestamp', 'competitor', 'platform', 'review_date', 'star_rating', 'review_text', 'author', 'response_date', 'response_text']
        self.reviews_file = os.path.join(self.output_dir, "reviews_database.csv")
        if not os.path.exists(self.reviews_file):
            df = pd.DataFrame(columns=self.reviews_columns)
            df.to_csv(self.reviews_file, index=False)
            
    def append_metric(self, competitor: str, platform: str, metric_type: str, value: float):
        """Append a single metric record to the CSV storage."""
        try:
            timestamp = datetime.now().isoformat()
            row = pd.DataFrame([{
            'timestamp': timestamp,
            'competitor': competitor,
            'platform': platform,
            'metric_type': metric_type,
            'value': value
        }])
            row.to_csv(self.metrics_file, mode='a', header=False, index=False)
            logger.debug(f"Saved Metric: {competitor} - {platform} - {metric_type}: {value}")
        except Exception as e:
            logger.error(f"Failed to save metric for {competitor} on {platform}: {str(e)}")

    def append_review(self, competitor: str, platform: str, review_date: str, star_rating: float, review_text: str, author: str = "", response_date: str = "", response_text: str = ""):
        """Appends a single review entry to the CSV file including developer responses."""
        timestamp = datetime.now().isoformat()
        row = pd.DataFrame([{
            'scrape_timestamp': timestamp,
            'competitor': competitor,
            'platform': platform,
            'review_date': review_date,
            'star_rating': star_rating,
            'review_text': str(review_text).replace('\n', ' ').replace('\r', ' '), # Clean newlines for CSV safety
            'author': author,
            'response_date': response_date,
            'response_text': str(response_text).replace('\n', ' ').replace('\r', ' ') if response_text else ""
        }])
        row.to_csv(self.reviews_file, mode='a', header=False, index=False)
        logger.debug(f"Saved Review: {competitor} - {platform} - {star_rating} chars: {len(str(review_text))} (Replied: {bool(response_text)})")
            
    def export_summary(self):
        """Export a summarized pivot table view of the latest metrics."""
        if not os.path.exists(self.metrics_file):
            logger.warning("No data to summarize yet.")
            return

        df = pd.read_csv(self.metrics_file)
        if df.empty:
            return
            
        # Get only the latest entry per competitor/platform/metric
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        latest_df = df.sort_values('timestamp').groupby(['competitor', 'platform', 'metric_type']).tail(1)
        
        # Create a clean pivot table format
        pivot_df = latest_df.pivot_table(
            index=['competitor'], 
            columns=['platform', 'metric_type'], 
            values='value',
            aggfunc='first'
        )
        
        summary_file = os.path.join(self.output_dir, "latest_summary_matrix.csv")
        pivot_df.to_csv(summary_file)
        logger.info(f"Summary exported to {summary_file}")
