import streamlit as st
from langchain_community.tools import DuckDuckGoSearchResults
import re
import requests
import urllib.parse
from bs4 import BeautifulSoup

search = DuckDuckGoSearchResults()

# --- Prioritized Websites ---
PRIORITIZED_WEBSITES = {
    "Serious Eats": "https://www.seriouseats.com",
    "Rick Bayless": "https://www.rickbayless.com",
    "Wikipedia": "https://en.wikipedia.org",
}

def is_valid_link(url):
    try:
        response = requests.head(url, timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def fetch_and_extract_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Try <p> first
        text_elements = [p.get_text() for p in soup.find_all('p')]

        # If not enough content, try <li> tags (common in recipes)
        if len(text_elements) < 10:
            text_elements += [li.get_text() for li in soup.find_all('li')]

        # Fallback: grab all visible text if content still looks short
        text = ' '.join(text_elements).strip()
        return text if len(text) > 200 else None
    except Exception as e:
        st.error(f"Error fetching or parsing content: {e}")
        return None


def parse_search_results(rsp):
    # Try to capture actual URL inside redirection
    matches = re.findall(r'link:\s*(https?://[^\s,]+)', rsp)
    clean_links = []

    for raw_link in matches:
        # Decode if it's a DuckDuckGo redirect
        if "duckduckgo.com/l/?" in raw_link and "uddg=" in raw_link:
            parsed = urllib.parse.urlparse(raw_link)
            query = urllib.parse.parse_qs(parsed.query)
            clean_url = query.get("uddg", [None])[0]
            if clean_url:
                clean_links.append(clean_url)
        else:
            clean_links.append(raw_link)

    return clean_links


def search_prioritized_websites(query, prioritized_websites):
    """
    Searches for a query within a list of prioritized websites.

    Args:
        query (str): The user's search query.
        prioritized_websites (dict): A dictionary of website names and their URLs.

    Returns:
        tuple: A tuple containing (snippet, title, clean_link) if found, otherwise None.
    """
    for name, base_url in prioritized_websites.items():
        website_query = f"site:{base_url} {query}"
        rsp = search.invoke(website_query)

        # Try to extract all URLs from the response
        clean_links = parse_search_results(rsp)

        if clean_links:
            link = clean_links[0]
            title = f"{name} recipe"  # Or extract title with regex if needed
            snippet = ""  # Optional: add regex for snippet
            return (snippet, title, link)

    return None


def init_st_var(varname, value, do_init=True): 
    if varname not in st.session_state and do_init:
        st.session_state[varname] = value
 