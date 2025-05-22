from flask import Flask, request, jsonify
from textblob import TextBlob
from database import store_session, fetch_user_sessions, fetch_session_by_id, fetch_similar_sessions
from weather_main import WeatherAgent  # Import your WeatherAgent
from flask_cors import CORS  # Add this import

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes (use specific origins in production)



# Initialize the weather agent
agent = WeatherAgent(model="llama-3.3-70b-versatile")

@app.route('/weather', methods=['POST'])
def weather_query():
    data = request.json
    query = data.get('query')
    user_id = data.get('user_id', 'default_user')  # Default user ID for simplicity
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Analyze sentiment
        sentiment = TextBlob(query).sentiment.polarity
        
        # === Step 1: Retrieve 2–3 similar recent sessions as context ===
        similar_sessions = fetch_similar_sessions(query, user_id, limit=5)  # fetch more to sort by recency
        sorted_sessions = sorted(
            similar_sessions,
            key=lambda s: s["timestamp"],
            reverse=True
        )[:3]  # Take top 3 most recent
        
        # === Step 2: Build context from previous Q&A ===
        context = ""
        if sorted_sessions:
            context_lines = [
                f"User previously asked: \"{s['query']}\"\nAgent replied: \"{s['response']}\"\n"
                for s in sorted_sessions
            ]
            context = "Here is some context from earlier sessions:\n" + "\n".join(context_lines) + "\n"
        
        # === Step 3: Build prompt with context add sentiment value===
        final_prompt = context + query + f"\nSentiment score: {sentiment:.2f}\n"
        
        # === Step 4: Get the response from the weather agent ===
        response = agent.process_weather_query(final_prompt)
        print(f"Agent response: {response}")

        
        # === Step 6: Store session ===
        fallback_keywords = ["sorry", "I couldn't", "error", "please try again"]
        if not any(keyword in response.lower() for keyword in fallback_keywords):
            session_id = store_session(user_id, query, response)
        else:
            session_id = None

        
        return jsonify({
            "response": response,
            "session_id": session_id
        })

    except Exception as e:
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500


@app.route('/sessions/<user_id>', methods=['GET'])
def get_sessions(user_id):
    try:
        sessions = fetch_user_sessions(user_id)
        print(f"Fetched sessions for user {user_id}: {sessions}")
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"error": f"Error fetching sessions: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)