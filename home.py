import streamlit as st
import pandas as pd
from utilis import *
from genaiutils import *

# --- Streamlit App ---
st.set_page_config(layout="wide")

# --- Initialize chat state once ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown(
    "<h1 style='text-align: center; margin-bottom: 0.5rem;'>What are you looking to cook?</h1>",
    unsafe_allow_html=True
)
# Create slightly uneven columns to shift the checkbox just right of center
col1, col2, col3 = st.columns([2.2, 1, 0.9])
with col2:
    show_measurements = st.checkbox("Show Measurement Data", help="Toggle ingredient measurement breakdown.")

# --- Display chat history ---
for message in st.session_state.chat_history:
    st.markdown(f"**You:** {message['user']}")
    st.markdown(f"**Assistant:** {message['assistant']}")

# ---------------- Chat input workflow ----------------
user_input = st.chat_input("Type a recipe idea or question...")

if user_input:
    # search / fetch logic
    content = None
    title = ""
    link = ""

    # try prioritized search
    res = search_prioritized_websites(user_input, PRIORITIZED_WEBSITES)
    if res:
        _, title, link = res
        if is_valid_link(link):               
            content = fetch_and_extract_content(link) # fetch page
    else:
        rsp = search.invoke(user_input)
        links = parse_search_results(rsp)
        if links:
            link = links[0]
            title = "Recipe"
            if is_valid_link(link):
                content = fetch_and_extract_content(link)

    if content:
        summary     = summarize_recipe(content)
        ingredients = extract_ingredients(content)
        st.session_state["raw_ingredients"] = ingredients

        response_md = (
            f"**Title:** [{title.strip()}]({link})\n\n"
            f"**Summary:**\n{summary}\n\n"
            f"**Ingredients:**\n{ingredients}"
        )
        st.markdown(response_md)
        st.session_state.chat_history.append({"user": user_input,
                                              "assistant": response_md})
    else:
        st.session_state.chat_history.append({"user": user_input,
                                              "assistant": "Sorry, couldn’t find a recipe."})

# measurement table 
if show_measurements and st.session_state.get("raw_ingredients"):
    parsed = get_structured_ingredients_via_llm(st.session_state["raw_ingredients"])
    if parsed:
        st.markdown("### Measurement Breakdown")
        st.dataframe(pd.DataFrame(parsed))
    else:
        st.info("Could not extract structured ingredient data.")
