import streamlit as st
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import re
import pandas as pd
import json

# --- Load Environment Variables ---
load_dotenv("./config/dev_sample.env")

# --- Configuration ---
PROJECT_ID = 'hrl-dev-genai'
LOCATION = 'us-central1'
MODEL_NAME = 'gemini-2.0-flash-001'

# --- Initialize LLM ---
llm = ChatVertexAI(
    model_name=MODEL_NAME,
    project=PROJECT_ID,
    location=LOCATION,
    temperature=0.0,
)

def _invoke_llm_chain(prompt_template: str, text: str, error_message: str, max_chars: int = 8000):
    """Helper function to invoke an LLM chain with error handling."""
    if not text:
        return error_message

    trimmed_text = text[:max_chars]
    prompt = PromptTemplate.from_template(prompt_template)
    chain = LLMChain(llm=llm, prompt=prompt)

    try:
        result = chain.invoke({"text": trimmed_text})
        return result.get('text', error_message)
    except Exception as e:
        st.error(f"LLM chain failed: {e}")
        return error_message

def summarize_recipe(text):
    if not text:
        return "Could not retrieve recipe summary."
    prompt_template = """
    You are a world-class chef, known for your ability to distill complex recipes into concise and informative summaries.
    Please provide a detailed summary of the following recipe, highlighting the key steps, techniques, and flavors.
    Recipe:
    {text}
    """
    return _invoke_llm_chain(prompt_template, text, "Could not summarize recipe.")

def extract_ingredients(text):
    prompt_template = """
    You are a world-class chef, skilled at identifying ingredients and their quantities from recipes.  
    Please extract all ingredients **with their exact measurements** from the following recipe and list them in bullet-point format like:
    - 1 cup of flour
    - 2 tablespoons olive oil
    Recipe:
    {text}
    """
    return _invoke_llm_chain(prompt_template, text, "Could not extract ingredients.")

def get_structured_ingredients_via_llm(ingredient_text: str, max_chars: int = 6000):
    """
    Send a list-of-ingredient lines to Gemini and get structured JSON back.
    Returns [] if the model fails or returns non-JSON.
    """
    cache_key = f"structured_{hash(ingredient_text)}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    trimmed = ingredient_text[:max_chars]          # keep request comfortably small

    template = """
    You are a culinary assistant. Convert the ingredient list below into
    JSON with keys: Ingredient, Quantity, Unit, Type.
    Return **only** the JSON array—no commentary.

    Ingredients:
    {text}
    """
    prompt = PromptTemplate.from_template(template)
    chain  = LLMChain(llm=llm, prompt=prompt)

    try:
        raw = chain.invoke({"text": trimmed})           # may be dict or str
        if isinstance(raw, dict):
            raw = raw.get("text", "")

        # Pull out the first JSON array in the response
        match = re.search(r"\[[\s\S]*\]", raw)   # grabs the first JSON array even if wrapped
        if not match:
            st.error("LLM response did not contain JSON data.")
            return []

        structured = json.loads(match.group(0))
        st.session_state[cache_key] = structured        # cache for this session
        return structured

    except json.JSONDecodeError:
        st.error("LLM returned malformed JSON.")
        return []
    except Exception as e:
        st.error(f"Structured-ingredient extraction failed: {e}")
        return []