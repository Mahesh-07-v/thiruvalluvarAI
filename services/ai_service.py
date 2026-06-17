import google.generativeai as genai
import json
import re
from models.kural import Kural

class AIService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"temperature": 0.7}
        )

    def explain_kural(self, kural: Kural, user_query: str) -> str:
        prompt = f"""
You are Thiruvalluvar.AI, an expert on the ancient Tamil classic Thirukkural.
The user asked: "{user_query}".
You are provided with this authentic, verified Kural from our database:

Kural Number: {kural.number}
Line 1: {kural.line1}
Line 2: {kural.line2}
Tamil Meaning (Mu. Varadharajan): {kural.mv}
Tamil Meaning (Solomon Pappaiah): {kural.sp}
English Explanation: {kural.explanation}

Your task is to present this Kural to the user. To prevent hallucinations and maintain absolute correctness, you must copy the values EXACTLY from the provided database fields. Do not alter the Tamil script, do not translate it yourself, and do not add any conversational text before or after.

Output the response in this exact format:

the kural is
{kural.line1}
{kural.line2}

tamil meaning:-
{kural.mv}

english meaning:-
{kural.explanation}
"""
        try:
            response = self.model.generate_content(prompt)
            # Strip any markdown formatting like ```text or ``` if the AI wraps it
            result_text = response.text.strip()
            result_text = re.sub(r'^```[a-zA-Z]*\n', '', result_text)
            result_text = re.sub(r'\n```$', '', result_text).strip()
            return result_text
        except Exception as e:
            return f"Error communicating with Gemini: {e}"

    def analyze_query_for_keywords(self, query: str) -> list:
        prompt = f"""
Given the Thirukkural chatbot search query: "{query}"
Identify the main core English subject/topic (e.g., "education", "god", "friendship", "anger", "love").
Output a JSON array containing up to 5 English synonyms/keywords that will help search a translation database.
For example, if the query is "education", return ["learn", "learning", "study", "wisdom", "education"].
Return ONLY the JSON array, no explanation, no commentary, and no markdown formatting.
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # Remove possible code blocks
            text = re.sub(r'^```[a-zA-Z]*\n', '', text)
            text = re.sub(r'\n```$', '', text).strip()
            return json.loads(text)
        except Exception:
            return []
