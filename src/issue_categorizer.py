import pandas as pd
import os
import re

def categorize_issues():
    reviews_file = "data/reviews_database.csv"
    if not os.path.exists(reviews_file):
        print("No DB")
        return
        
    df = pd.read_csv(reviews_file)
    
    # Filter to 1 and 2 star reviews
    neg_df = df[df['star_rating'] <= 2.0].copy()
    
    categories = {
        'Product & App Stability': ['buffer', 'lag', 'crash', 'quality', 'resolution', 'audio', 'sync', 'load', 'black screen', 'login', 'sign in', 'glitch', 'error', 'work', 'working', 'play', 'playing'],
        'Billing & Friction': ['cancel', 'trial', 'charge', 'refund', 'price', 'expensive', 'contract', 'renew', 'money', 'pay', 'paid', 'subscription', 'month', 'year', 'cost'],
        'Content & Experience': ['commentary', 'commentator', 'presenter', 'pundit', 'interface', 'ui ', 'navigation', 'find', 'missing', 'show', 'event', 'fight', 'match', 'game', 'boring', 'boring']
    }
    
    # Helper to count matches
    def count_matches(text, keywords):
        if not isinstance(text, str): return 0
        text = text.lower()
        return any(kw in text for kw in keywords)
        
    for cat, kws in categories.items():
        neg_df[cat] = neg_df['review_text'].apply(lambda x: count_matches(x, kws))
        
    # Aggregate by competitor
    # We want to see what % of negative reviews mention each category
    def calc_percentages(group):
        total = len(group)
        if total == 0: return pd.Series()
        return pd.Series({
            'Total Neg Reviews': total,
            'Product/App Stability %': (group['Product & App Stability'].sum() / total) * 100,
            'Billing & Friction %': (group['Billing & Friction'].sum() / total) * 100,
            'Content & UX %': (group['Content & Experience'].sum() / total) * 100
        })
        
    cat_df = neg_df.groupby('competitor').apply(calc_percentages).round(1).sort_values('Total Neg Reviews', ascending=False)
    
    print("\n" + "="*80)
    print("NEGATIVE REVIEW COMPLAINT CATEGORIZATION (% of negative reviews mentioning category)")
    print("="*80)
    print(cat_df.to_string())
    
    # Let's also create a specific highlight of top DAZN issues vs top competitors
    print("\n" + "="*80)
    print("TOP ISSUE FOCUS")
    print("="*80)
    focus = {}
    for comp in cat_df.index:
        row = cat_df.loc[comp]
        if row['Total Neg Reviews'] > 50:
            max_cat = row[['Product/App Stability %', 'Billing & Friction %', 'Content & UX %']].idxmax()
            val = row[max_cat]
            focus[comp] = f"{max_cat.replace(' %', '')} ({val}%)"
            
    for k, v in focus.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    categorize_issues()
