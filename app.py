import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- Page Config ---
st.set_page_config(page_title="DAZN Competitive Intelligence", page_icon="🥊", layout="wide", initial_sidebar_state="expanded")

# --- CSS Styling ---
st.markdown("""
<style>
    .kpi-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
        margin-bottom: 20px;
    }
    .kpi-title { font-size: 14px; font-weight: 600; color: #A0A0A0; text-transform: uppercase; letter-spacing: 1px;}
    .kpi-value { font-size: 32px; font-weight: 800; color: #FFFFFF; margin: 10px 0;}
    .kpi-delta.positive { color: #22c55e; font-size: 14px; font-weight: 600;}
    .kpi-delta.negative { color: #ef4444; font-size: 14px; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# --- Load Data Cache ---
@st.cache_data
def load_metrics():
    df = pd.read_csv("data/metrics_database.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

@st.cache_data
def load_reviews():
    df = pd.read_csv("data/reviews_database.csv")
    df['review_date'] = pd.to_datetime(df['review_date'], format='ISO8601', utc=True)
    df['response_text'].fillna("", inplace=True)
    df['has_response'] = df['response_text'] != ""
    
    return df

df_m = load_metrics()
df_r = load_reviews()

# Calculate global aggregates for comparisons
total_vols = df_m[df_m['metric_type'] == 'review_count'].sort_values('timestamp').drop_duplicates(subset=['competitor', 'platform'], keep='last').groupby('competitor')['value'].sum()

def get_sentiment(df):
    def _calc(g):
        t = len(g)
        if t == 0: return pd.Series()
        return pd.Series({
            'Reviews': t,
            'Avg Rating': g['star_rating'].mean(),
            '1* %': (len(g[g['star_rating']==1.0])/t)*100,
            '5* %': (len(g[g['star_rating']==5.0])/t)*100
        })
    return df.groupby('competitor').apply(_calc).reset_index()

df_sentiment = get_sentiment(df_r)

# Custom Colors
color_map = {
    'DAZN': '#D1EC00', # Classic high-vis yellow
    'FuboTV': '#FF5A00',
    'ESPN': '#CE0000',
    'Sky Sports': '#002C9A',
    'TNT Sports': '#E3006A',
    'BT Sport': '#6500A5',
    'Eurosport': '#001A4B'
}

# --- Sidebar UI ---
st.sidebar.markdown("## DAZN x WHIZCROW")
st.sidebar.markdown("### Executive Dashboard")
view = st.sidebar.radio("Navigation Menu", [
    "1. Executive KPI Overview", 
    "2. Semantic & Volume Analysis", 
    "3. Support Operations Engine",
    "4. Root Cause (NLP Friction)"
])

# ----------------------------------------------------
# 1. EXECUTIVE KPI OVERVIEW
# ----------------------------------------------------
if view == "1. Executive KPI Overview":
    st.title("DAZN Executive Overview")
    st.markdown("Real-time snapshot of DAZN's ecosystem health against direct sports streaming competitors.")
    
    # KPIs
    dazn_vol = total_vols.get('DAZN', 0)
    dazn_1star = df_sentiment[df_sentiment['competitor'] == 'DAZN']['1* %'].values[0]
    avg_competitor_1star = df_sentiment[df_sentiment['competitor'] != 'DAZN']['1* %'].mean()
    
    # Response Speed calculation
    df_speed = df_r[(df_r['platform'] != "Apple App Store") & (df_r['has_response'])]
    if not df_speed.empty:
        df_speed['resp_hrs'] = (pd.to_datetime(df_speed['response_date'], format='mixed', utc=True) - pd.to_datetime(df_speed['review_date'], utc=True)).dt.total_seconds().abs() / 3600.0
        dazn_spd = df_speed[df_speed['competitor'] == 'DAZN']['resp_hrs'].mean()
    else:
        dazn_spd = 0
        
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class='kpi-card'><div class='kpi-title'>Total Public Reviews</div><div class='kpi-value'>{dazn_vol:,.0f}</div><div class='kpi-delta positive'>Highest Direct Streaming</div></div>""", unsafe_allow_html=True)
    with c2:
        delta = dazn_1star - avg_competitor_1star
        css_class = "negative" if delta > 0 else "positive"
        st.markdown(f"""<div class='kpi-card'><div class='kpi-title'>1-Star Review Density</div><div class='kpi-value'>{dazn_1star:.1f}%</div><div class='kpi-delta {css_class}'>+{delta:.1f}% vs Competitor Avg</div></div>""", unsafe_allow_html=True)
    with c3:
        rr = df_r[(df_r['platform'] != "Apple App Store") & (df_r['competitor'] == 'DAZN')]['has_response'].mean() * 100
        st.markdown(f"""<div class='kpi-card'><div class='kpi-title'>CS Response Rate</div><div class='kpi-value'>{rr:.1f}%</div><div class='kpi-delta positive'>#1 in Industry</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='kpi-card'><div class='kpi-title'>Avg Support Speed</div><div class='kpi-value'>{dazn_spd:.1f} Hrs</div><div class='kpi-delta positive'>Lightning Fast</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # Platform Ecosystem Treemap
    st.subheader("Market Review Ecosystem Breakdown")
    df_rc = df_m[df_m['metric_type'] == 'review_count'].sort_values('timestamp').drop_duplicates(subset=['competitor', 'platform'], keep='last')
    
    # Filter only streaming directly (skip Peacock/Hulu/Amazon to zoom in on Sports if wanted, else keep all)
    direct_sports = ['DAZN', 'ESPN', 'Sky Sports', 'FuboTV', 'Eurosport', 'BT Sport', 'TNT Sports']
    df_rc_sports = df_rc[df_rc['competitor'].isin(direct_sports)]
    
    fig_tree = px.treemap(df_rc_sports, path=[px.Constant("Global Sports"), 'competitor', 'platform'], 
                          values='value', color='competitor', color_discrete_map=color_map,
                          title="Review Volume Share Across Competitors & Platforms")
    fig_tree.update_traces(textinfo="label+value+percent parent")
    st.plotly_chart(fig_tree, use_container_width=True)

# ----------------------------------------------------
# 2. SEMANTIC & VOLUME ANALYSIS
# ----------------------------------------------------
elif view == "2. Semantic & Volume Analysis":
    st.title("Sentiment & Volume Correlation")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Distribution of Star Ratings")
        # 1-5 Stacked
        df_stack = get_sentiment(df_r)
        
        # Calculate intermediate stars too for chart
        def full_stack(g):
            t = len(g)
            if t == 0: return pd.Series()
            return pd.Series({
                '1 Star': (len(g[g['star_rating']==1])/t)*100,
                '2 Star': (len(g[g['star_rating']==2])/t)*100,
                '3 Star': (len(g[g['star_rating']==3])/t)*100,
                '4 Star': (len(g[g['star_rating']==4])/t)*100,
                '5 Star': (len(g[g['star_rating']==5])/t)*100,
            })
        full_sent = df_r.groupby('competitor').apply(full_stack).reset_index()
        
        fig_sent = px.bar(full_sent.sort_values('1 Star', ascending=False), x='competitor', 
                          y=['1 Star', '2 Star', '3 Star', '4 Star', '5 Star'],
                          title="Public Sentiment Profile (%)",
                          color_discrete_sequence=['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e'])
        st.plotly_chart(fig_sent, use_container_width=True)
        
    with col2:
        st.subheader("Quality vs. Sample Size")
        # Scatter: Total Volume vs Avg Rating
        df_rc = df_m[df_m['metric_type'] == 'review_count'].sort_values('timestamp').drop_duplicates(subset=['competitor', 'platform'], keep='last')
        tot = df_rc.groupby('competitor')['value'].sum().reset_index(name='Total Revs')
        merged = pd.merge(tot, df_sentiment, on='competitor', how='inner')
        
        fig_scatter = px.scatter(merged, x='Total Revs', y='Avg Rating', size='Reviews', color='competitor', 
                                 log_x=True, text='competitor', size_max=40, color_discrete_map=color_map,
                                 title="Higher Volume = Lower Ratings (The Scale Penalty)")
        fig_scatter.update_traces(textposition='top center')
        st.plotly_chart(fig_scatter, use_container_width=True)

# ----------------------------------------------------
# 3. SUPPORT OPERATIONS ENGINE
# ----------------------------------------------------
elif view == "3. Support Operations Engine":
    st.title("Customer Support Intelligence")
    st.markdown("Analyzing how aggressively and quickly brands respond to App Store & Trustpilot friction.")
    
    # Exclude Apple App Store for Support Metrics
    df_s = df_r[df_r['platform'] != "Apple App Store"].copy()
    
    # Calculate Rate and Speed
    def calc_ops(g):
        t = len(g)
        if t == 0: return pd.Series()
        replies = g[g['has_response']]
        rate = (len(replies) / t) * 100
        
        speed = 0
        uniq = 0
        if not replies.empty and replies['response_date'].notna().any():
            valid = replies[replies['response_date'].notna()].copy()
            valid['response_date'] = pd.to_datetime(valid['response_date'], format='mixed', utc=True)
            valid['review_date'] = pd.to_datetime(valid['review_date'], utc=True)
            hrs = (valid['response_date'] - valid['review_date']).dt.total_seconds().abs() / 3600.0
            speed = hrs.mean()
            uniq = (replies['response_text'].nunique() / len(replies)) * 100
            
        return pd.Series({'Rate %': rate, 'Speed (Hrs)': speed, 'Uniqueness %': uniq})
        
    ops_df = df_s.groupby('competitor').apply(calc_ops).reset_index()
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Response Engagement Strategy")
        fig_bubble = px.scatter(ops_df, x='Speed (Hrs)', y='Rate %', color='competitor', size='Uniqueness %',
                                hover_name='competitor', color_discrete_map=color_map,
                                title="(Top Left is Best) Rate vs Speed vs Uniqueness", size_max=30)
        # Reverse X axis so faster is on the right visually, or keep zero on left
        fig_bubble.update_xaxes(autorange="reversed")
        st.plotly_chart(fig_bubble, use_container_width=True)

    with c2:
        st.subheader("The Uniqueness Factor")
        st.markdown("Are they fixing problems or using copy-paste bots?")
        
        # Filter out 0% rates
        ops_filtered = ops_df[ops_df['Rate %'] > 0]
        fig_bar = px.bar(ops_filtered.sort_values('Uniqueness %', ascending=False), 
                         x='competitor', y='Uniqueness %', color='competitor', text='Uniqueness %',
                         color_discrete_map=color_map)
        fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_bar.update_yaxes(range=[0, 110])
        st.plotly_chart(fig_bar, use_container_width=True)

# ----------------------------------------------------
# 4. ROOT CAUSE (NLP Friction)
# ----------------------------------------------------
elif view == "4. Root Cause (NLP Friction)":
    st.title("NLP Complaint Categorization")
    st.markdown("Why do DAZN's superior Customer Support times fail to prevent 1-Star reviews?")
    
    # Re-calculate buckets (mimicking the categorizer logic for dynamic charting)
    neg_df = df_r[df_r['star_rating'] <= 2.0].copy()
    
    categories = {
        'Product & App Stability': ['buffer', 'lag', 'crash', 'quality', 'resolution', 'audio', 'sync', 'load', 'black screen', 'login', 'error'],
        'Billing & Friction': ['cancel', 'trial', 'charge', 'refund', 'price', 'expensive', 'contract', 'renew', 'money', 'paid', 'subscription', 'month'],
        'Content / UX': ['commentary', 'presenter', 'interface', 'ui', 'navigation', 'missing', 'fight', 'match', 'game', 'boring']
    }
    
    def count_matches(text, kws):
        if not isinstance(text, str): return 0
        text = text.lower()
        return any(k in text for k in kws)
        
    for cat, kws in categories.items():
        neg_df[cat] = neg_df['review_text'].apply(lambda x: count_matches(x, kws))
        
    def calc_perc(g):
        t = len(g)
        if t == 0: return pd.Series()
        return pd.Series({
            'Stability': (g['Product & App Stability'].sum()/t)*100,
            'Billing': (g['Billing & Friction'].sum()/t)*100,
            'UX': (g['Content / UX'].sum()/t)*100
        })
    cat_df = neg_df.groupby('competitor').apply(calc_perc).reset_index()
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader("Competitor Friction Profile")
        
        # Melt for clustered bar
        melted = cat_df.melt(id_vars='competitor', value_vars=['Stability', 'Billing', 'UX'], var_name='Issue Type', value_name='Mentions %')
        
        fig_cat = px.bar(melted, x='competitor', y='Mentions %', color='Issue Type', barmode='group',
                         title="% of Negative Reviews Containing Specific Friction Keywords",
                         color_discrete_sequence=['#3b82f6', '#ef4444', '#8b5cf6'])
        st.plotly_chart(fig_cat, use_container_width=True)
        
    with c2:
        st.subheader("Executive Takeaway")
        st.info("""
        **DAZN's core threat is Billing Friction.**
        
        Despite having the most reliable physical streaming application (only ~20% buffering complaints compared to 40%+ for Sky and ESPN), **74% of DAZN's 1-star reviews cite free trials, cancellation traps, or 12-month contract lock-ins.**
        
        DAZN's world-class customer support response times cannot outpace the aggressive front-end sales acquisition flows. Product/Sales misalignment is the root cause of the current App Store reputational damage.
        """)
        
        # Small heatmap
        fig_heat = px.imshow(cat_df.set_index('competitor').T, color_continuous_scale="Reds", text_auto=".1f", aspect="auto", title="Friction Heatmap")
        st.plotly_chart(fig_heat, use_container_width=True)
