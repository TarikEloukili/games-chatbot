from flask import Flask, request, jsonify, render_template
import pandas as pd
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

app = Flask(__name__)

# Load the game data from an Excel file
game_data = pd.read_excel('games.xlsx')

template = """
You are a chatbot for an ecommerce website that sells games. You must answer questions based on the data provided in the Excel file only. Provide detailed information about games, their genres, account levels, prices, and whether the price is debatable.

Here is the conversation history: {context}

Question: {question}

Answer:
"""

model = OllamaLLM(model="llama3")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

def get_game_details_by_genre(genre):
    try:
        games = game_data[game_data['genre'].str.lower() == genre.lower()]
        if not games.empty:
            return games[['game name', 'Account lvl', 'price $', 'price debatable ?']].to_dict(orient='records')
        else:
            return None
    except KeyError as e:
        print(f"Column not found: {e}")
        return None

@app.route('/')
def index():
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('question', '')
    context = data.get('context', '')
    
    if "genre" in user_input.lower() or "game" in user_input.lower():
        genre = user_input.lower().replace("genre", "").replace("game", "").strip()
        games = get_game_details_by_genre(genre)
        if games:
            available_games = games
            response = "Here are the games available in the {} genre:\n".format(genre.capitalize())
            for game in games:
                response += "- {}\n".format(game['game name'])
            response += "Would you like to know the price and other details of these games? (yes/no)"
        else:
            response = "Sorry, we don't have any games in the {} genre.".format(genre)
    else:
        response = chain.invoke({"context": context, "question": user_input})
    
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
