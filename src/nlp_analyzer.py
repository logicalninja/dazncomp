import pandas as pd
import os
import re
from loguru import logger
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.corpus import stopwords
import string

def get_top_ngrams(corpus, n=2, top_k=5):
    """Extract top N-grams (bigrams/trigrams) from a text corpus using scikit-learn."""
    if not corpus: return []
    
    # Custom stop words specifically for our domain to remove noise
    stop_words = set(stopwords.words('english'))
    custom_stops = {
        'dazn', 'eurosport', 'fubotv', 'bleacher', 'report', 'app', 'streaming', 
        'stream', 'watch', 'watching', 'subscription', 'subscribe', 'subscribed',
        'account', 'service', 'time', 'even', 'get', 'got', 'money', 'pay', 'paid',
        'month', 'months', 'year', 'years', 'day', 'days', 'like', 'would', 'one',
        'two', 'make', 'made', 'said', 'told', 'give', 'given', 'take', 'taken',
        'back', 'use', 'using', 'tried', 'trying', 'want', 'wanted', 'let', 'show',
        'every', 'never', 'ever', 'always', 'can', 'could', 'cannot', 'couldnt',
        'will', 'would', 'shall', 'should', 'im', 'ive', 'ill', 'id', 'dont', 'doesnt',
        'didnt', 'wont', 'wouldnt', 'cant', 'isnt', 'arent', 'wasnt', 'werent',
        'havent', 'hasnt', 'hadnt', 'customer', 'support', 'cancel', 'cancelled', 'cancellation'
    }
    stop_words.update(custom_stops)
    
    def clean_text(text):
        if not isinstance(text, str): return ""
        # Remove punctuation, lowercase everything
        text = text.translate(str.maketrans('', '', string.punctuation)).lower()
        return text

    cleaned_corpus = [clean_text(doc) for doc in corpus]
    
    try:
        vec = CountVectorizer(ngram_range=(n, n), stop_words=list(stop_words))
        bow = vec.fit_transform(cleaned_corpus)
        sum_words = bow.sum(axis=0)
        
        words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
        words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
        return words_freq[:top_k]
    except ValueError:
        return [] # Empty vocabulary


def analyze_complaints():
    data_dir = "data"
    reviews_file = os.path.join(data_dir, "reviews_database.csv")
    
    if not os.path.exists(reviews_file):
        logger.error("Dataset not found!")
        return
        
    df = pd.read_csv(reviews_file)
    logger.info(f"Loaded {len(df)} total reviews.")
    
    # We only care about negative reviews to find complaints
    negative_reviews = df[df['star_rating'] <= 2.0]
    logger.info(f"Analyzing {len(negative_reviews)} negative reviews (1 or 2 stars).")
    
    competitors = df['competitor'].unique()
    
    print("\n" + "="*80)
    print(f"{'TOP 5 COMPLAINT THEMES BY COMPETITOR (BIGRAMS/TRIGRAMS)':^80}")
    print("="*80)
    
    for comp in competitors:
        comp_reviews = negative_reviews[negative_reviews['competitor'] == comp]['review_text'].tolist()
        if not comp_reviews:
            print(f"\n[{comp}] - Not enough negative reviews for analysis.")
            continue
            
        print(f"\n--- {comp} ({len(comp_reviews)} negative reviews) ---")
        
        top_bigrams = get_top_ngrams(comp_reviews, n=2, top_k=5)
        top_trigrams = get_top_ngrams(comp_reviews, n=3, top_k=3)
        
        print("  Key Issues (Bigrams):")
        for word, freq in top_bigrams:
            print(f"    - '{word}' ({freq} mentions)")
            
        print("  Context (Trigrams):")
        for word, freq in top_trigrams:
            print(f"    - '{word}' ({freq} mentions)")

if __name__ == "__main__":
    analyze_complaints()
