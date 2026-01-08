import streamlit as st
from newsapi import NewsApiClient
from gnews import GNews
from newspaper import Article
import pandas as pd
from datetime import datetime, timedelta
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="AI News Scraper & Summarizer", layout="wide")
NEWS_API_KEY = "YOUR_NEWSAPI_KEY_HERE" # Get from newsapi.org

# --- HELPER FUNCTIONS ---
def get_summary(url):
    """Downloads article and returns a max 5-line summary."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp() # Performs NLP to get the summary
        summary = article.summary
        # Clean up and limit to 5 lines
        lines = [line.strip() for line in summary.split('.') if line.strip()]
        return ". ".join(lines[:5]) + "."
    except:
        return "Summary unavailable for this source."

def to_excel(df):
    """Converts dataframe to an Excel file buffer."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Latest News')
    return output.getvalue()

# --- APP UI ---
st.title("🗞️ 24h AI News Scraper")
st.markdown("Fetching the most recent news, summarizing with AI, and exporting to Excel.")

with st.sidebar:
    query = st.text_input("Search Topic", "Global Economy")
    num_results = st.slider("Max results per source", 5, 20, 5)
    search_btn = st.button("Scrape & Summarize")

if search_btn:
    all_news = []
    
    # Calculate time 24 hours ago
    last_24h = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')

    with st.spinner('Scraping and Summarizing... please wait...'):
        # 1. NewsAPI (Filtered to last 24h)
        try:
            api = NewsApiClient(api_key=NEWS_API_KEY)
            res = api.get_everything(q=query, from_param=last_24h, language='en', sort_by='publishedAt', page_size=num_results)
            for a in res['articles']:
                all_news.append({
                    "Source": a['source']['name'],
                    "Title": a['title'],
                    "Timestamp": a['publishedAt'],
                    "URL": a['url'],
                    "Summary": get_summary(a['url'])
                })
        except Exception as e:
            st.error(f"NewsAPI Error: {e}")

        # 2. Google News (Filtered to last 24h)
        try:
            google_news = GNews(language='en', period='1d', max_results=num_results)
            g_res = google_news.get_news(query)
            for ga in g_res:
                all_news.append({
                    "Source": ga['publisher']['title'],
                    "Title": ga['title'],
                    "Timestamp": ga['published date'],
                    "URL": ga['url'],
                    "Summary": get_summary(ga['url'])
                })
        except Exception as e:
            st.error(f"Google News Error: {e}")

    # --- DISPLAY & DOWNLOAD ---
    if all_news:
        df = pd.DataFrame(all_news)
        
        # Display in App
        for index, row in df.iterrows():
            with st.container():
                st.subheader(row['Title'])
                st.caption(f"🕒 {row['Timestamp']} | 🏛️ {row['Source']}")
                st.write(f"**AI Summary:** {row['Summary']}")
                st.write(f"[Read Original Article]({row['URL']})")
                st.divider()

        # Excel Download Button
        excel_data = to_excel(df)
        st.sidebar.download_button(
            label="📥 Download Results as Excel",
            data=excel_data,
            file_name=f"news_{query}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No news found in the last 24 hours for this topic.")
