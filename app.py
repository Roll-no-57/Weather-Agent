from flask import Flask, request, jsonify
from textblob import TextBlob
from database import create_chat_index, store_query_response, fetch_similar_query_responses, fetch_chat_messages
from weather_main import WeatherAgent
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

agent = WeatherAgent(model="gemini-1.5-flash")

# In-memory chat list (replace with a database in production)
user_chats = {}

@app.route('/create_chat', methods=['POST'])
def create_chat():
    data = request.json
    user_id = data.get('user_id', 'default_user')
    chat_id = str(uuid.uuid4())
    index_name = create_chat_index(chat_id)
    
    if user_id not in user_chats:
        user_chats[user_id] = []
    user_chats[user_id].append({"chat_id": chat_id, "title": f"Chat {len(user_chats[user_id]) + 1}"})
    
    return jsonify({"chat_id": chat_id, "index_name": index_name})

@app.route('/weather', methods=['POST'])
def weather_query():
    data = request.json
    query = data.get('query')
    chat_id = data.get('chat_id')
    user_id = data.get('user_id', 'default_user')
    
    if not query or not chat_id:
        return jsonify({"error": "No query or chat_id provided"}), 400
    
    try:
        sentiment = TextBlob(query).sentiment.polarity
        similar_messages = fetch_similar_query_responses(chat_id, query, limit=3)
        
        context = ""
        if similar_messages:
            context_lines = [
                f"User previously asked: \"{m['query']}\"\nAgent replied: \"{m['response']}\"\n"
                for m in similar_messages
            ]
            context = "Here is some context from earlier in this chat:\n" + "\n".join(context_lines) + "\n"
        
        final_prompt = f"\nSentiment score: {sentiment:.2f}\n" + context + query
        response = agent.process_weather_query(final_prompt)
        
        fallback_keywords = ["sorry", "I couldn't", "error", "please try again"]
        if not any(keyword in response.lower() for keyword in fallback_keywords):
            message_id = store_query_response(chat_id, query, response)
        else:
            message_id = None
        
        return jsonify({
            "response": response,
            "message_id": message_id
        })
    
    except Exception as e:
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500

@app.route('/chats/<user_id>', methods=['GET'])
def get_chats(user_id):
    chats = user_chats.get(user_id, [])
    return jsonify({"chats": chats})

@app.route('/chat/<chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    try:
        messages = fetch_chat_messages(chat_id)
        return jsonify({"messages": messages})
    except Exception as e:
        return jsonify({"error": f"Error fetching messages: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)