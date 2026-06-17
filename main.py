import os
import sys
import re

# Ensure UTF-8 console output for Windows to prevent Unicode print crashes
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from services.database import KuralDatabase
from services.ai_service import AIService

# Load environment variables
load_dotenv()

# Initialize Kural Database
db = KuralDatabase("kurals.json")

# Initialize AI Service if key is set
api_key = os.getenv("GEMINI_API_KEY")
ai = AIService(api_key) if api_key else None

app = Flask(__name__)

def is_another_request(message: str) -> bool:
    msg = message.lower()
    triggers = ["another", "next", "one more", "other", "different", "more", "else", "ஒன்று", "வேறு"]
    return any(trigger in msg for trigger in triggers)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    global ai
    if not ai:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            ai = AIService(api_key)
            
    data = request.json or {}
    message = data.get("message", "").strip()
    shown_kurals = data.get("shown_kurals", [])
    last_query = data.get("last_query", "")
    
    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    # Conversational intent parsing
    words = re.sub(r'[^\w\s]', '', message.lower()).split()
    triggers = {"another", "next", "one", "more", "other", "different", "else", "give", "show", "me", "tell", "kural"}
    has_other_terms = any(w not in triggers for w in words)
    
    is_another = is_another_request(message)
    
    if is_another and not has_other_terms and last_query:
        search_query = last_query
    else:
        search_query = message
        # Determine if we changed topic
        is_same_topic = False
        if last_query:
            last_words = set(re.sub(r'[^\w\s]', '', last_query.lower()).split())
            new_words = set(words)
            is_same_topic = any(w in last_words for w in new_words if w not in triggers)
        
        if not is_same_topic and not is_another:
            shown_kurals = []

    if not is_another or has_other_terms:
        last_query = message

    # 1. Expand query using Gemini keywords
    search_keywords = []
    if ai:
        search_keywords = ai.analyze_query_for_keywords(search_query)
    
    combined_query = search_query
    if search_keywords:
        combined_query += " " + " ".join(search_keywords)
        
    # 2. Search local database
    results = db.search(combined_query, exclude_numbers=shown_kurals)
    
    if not results:
        # Fallback to general search with original message
        results = db.search(search_query, exclude_numbers=shown_kurals)

    if not results:
        return jsonify({
            "response": "I couldn't find a matching Kural for your query. Try searching for topics like god, virtue, education, or friendship."
        })

    # Pick the top result
    matched_kural = results[0]
    shown_kurals.append(matched_kural.number)
    
    # 3. Format using AI or fallback to direct database values
    response_text = None
    if ai:
        try:
            response_text = ai.explain_kural(matched_kural, message)
            if "Error" in response_text or "429" in response_text or "Quota exceeded" in response_text:
                response_text = None
        except Exception:
            response_text = None

    if not response_text:
        response_text = (
            f"the kural is\n{matched_kural.line1}\n{matched_kural.line2}\n\n"
            f"tamil meaning:-\n{matched_kural.mv}\n\n"
            f"english meaning:-\n{matched_kural.explanation}"
        )

    return jsonify({
        "kural": matched_kural.to_dict(),
        "response": response_text,
        "last_query": last_query,
        "shown_kurals": shown_kurals
    })

def run_cli():
    global ai
    print("==================================================")
    print("                Thiruvalluvar.AI                  ")
    print("==================================================")
    
    if not api_key:
        print("Note: GEMINI_API_KEY is not set in .env. Running in local database fallback mode.\n")
        
    shown_kurals = []
    last_query = ""
    
    print("bot:- Enter your query...")
    while True:
        try:
            user_input = input("user:- ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("bot:- Goodbye!")
                break
                
            if not ai:
                api_key_reload = os.getenv("GEMINI_API_KEY")
                if api_key_reload:
                    ai = AIService(api_key_reload)

            # Conversational state checks
            words = re.sub(r'[^\w\s]', '', user_input.lower()).split()
            triggers = {"another", "next", "one", "more", "other", "different", "else", "give", "show", "me", "tell", "kural"}
            has_other_terms = any(w not in triggers for w in words)
            
            is_another = is_another_request(user_input)
            
            if is_another and not has_other_terms and last_query:
                search_query = last_query
            else:
                search_query = user_input
                # Check if same topic
                is_same_topic = False
                if last_query:
                    last_words = set(re.sub(r'[^\w\s]', '', last_query.lower()).split())
                    new_words = set(words)
                    is_same_topic = any(w in last_words for w in new_words if w not in triggers)
                
                if not is_same_topic and not is_another:
                    shown_kurals = []
                    
            if not is_another or has_other_terms:
                last_query = user_input

            # 1. Expand query keywords
            search_keywords = []
            if ai:
                search_keywords = ai.analyze_query_for_keywords(search_query)
            
            combined_query = search_query
            if search_keywords:
                combined_query += " " + " ".join(search_keywords)
                
            # 2. Search database with exclusions
            results = db.search(combined_query, exclude_numbers=shown_kurals)
            if not results:
                results = db.search(search_query, exclude_numbers=shown_kurals)
                
            if not results:
                print("bot:- I could not find a matching Kural. Try querying about 'god', 'education', or 'friendship'.\n")
                continue
                
            matched_kural = results[0]
            shown_kurals.append(matched_kural.number)
            
            # 3. Format response
            response = None
            if ai:
                try:
                    response = ai.explain_kural(matched_kural, user_input)
                    if "Error" in response or "429" in response or "Quota exceeded" in response:
                        response = None
                except Exception:
                    response = None

            if not response:
                response = (
                    f"the kural is\n{matched_kural.line1}\n{matched_kural.line2}\n\n"
                    f"tamil meaning:-\n{matched_kural.mv}\n\n"
                    f"english meaning:-\n{matched_kural.explanation}"
                )
                
            print(f"bot:- {response}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nbot:- Goodbye!")
            break

if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        print("Starting Thiruvalluvar.AI Web Server...")
        print("Open http://127.0.0.1:5000 in your browser to experience the chatbot.")
        app.run(debug=True, port=5000)
