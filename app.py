import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Load the Excel file
file_path = "games.xlsx"  # Ensure this file is in the same directory
games_data = pd.read_excel(file_path)

# Prepare the dataset as a list of strings (split into chunks if necessary)
chunk_size = 450  # Token limit per chunk (to stay within model's 512-token limit)
data_list = [
    f"Game: {row['game name']}, Genre: {row['genre']}, Account Level: {row['Account lvl']}, "
    f"Price: ${row['price $']}, Price Negotiable: {row['price debatable ?']}"
    for _, row in games_data.iterrows()
]

# Split context into manageable chunks
context_chunks = [
    "\n".join(data_list[i:i+chunk_size]) for i in range(0, len(data_list), chunk_size)
]

# Load the Flan-T5 model from Hugging Face
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

# Helper function to handle specific queries
def handle_query(prompt):
    # Convert the prompt to lowercase for case-insensitive processing
    prompt_lower = prompt.lower()

    # "Do you have" or "What about" questions
    if "do you have" in prompt_lower or "what about" in prompt_lower:
        # Determine which phrase is present and extract the game name
        if "do you have" in prompt_lower:
            game_name = prompt_lower.replace("do you have", "").strip()
        elif "what about" in prompt_lower:
            game_name = prompt_lower.replace("what about", "").strip()

        # Filter the dataset for matching games
        matching_games = games_data[games_data["game name"].str.contains(game_name, case=False, na=False)]

        # Return results based on whether a match was found
        if not matching_games.empty:
            return f"Yes, {game_name} is available in the database. Here are the details:\n{matching_games.to_string(index=False)}"
        else:
            return f"No, {game_name} is not in the database."

    # Genre-related queries
    elif "genre" in prompt_lower and "and price" in prompt_lower:
        # Extract the genre from the prompt
        genre_query = prompt_lower.split("genre")[-1].split("and")[0].strip()

        # Handle combined genre and price queries
        if "above" in prompt_lower:
            # Extract and clean the price
            price_part = prompt_lower.split("above")[-1].strip().replace("$", "").strip()
            if not price_part.isdigit():
                return "Please specify a valid price (e.g., 'games in genre fantasy and price above 100')."
            price = int(price_part)
            matching_games = games_data[
                (games_data["genre"].str.contains(genre_query, case=False, na=False)) &
                (games_data["price $"] > price)
            ]
            if not matching_games.empty:
                return f"Here are {genre_query} games with prices above ${price}:\n{matching_games.to_string(index=False)}"
            else:
                return f"No {genre_query} games found with prices above ${price}."
        elif "below" in prompt_lower:
            # Extract and clean the price
            price_part = prompt_lower.split("below")[-1].strip().replace("$", "").strip()
            if not price_part.isdigit():
                return "Please specify a valid price (e.g., 'games in genre fantasy and price below 100')."
            price = int(price_part)
            matching_games = games_data[
                (games_data["genre"].str.contains(genre_query, case=False, na=False)) &
                (games_data["price $"] < price)
            ]
            if not matching_games.empty:
                return f"Here are {genre_query} games with prices below ${price}:\n{matching_games.to_string(index=False)}"
            else:
                return f"No {genre_query} games found with prices below ${price}."

    # Price-related queries
    elif "price" in prompt_lower:
        if "above" in prompt_lower:
            price_part = prompt_lower.split("above")[-1].strip()
            if not price_part.isdigit():
                return "Please specify a valid price (e.g., 'games with price above 100')."
            price = int(price_part)
            matching_games = games_data[games_data["price $"] > price]
            if not matching_games.empty:
                return f"Games with prices above ${price}:\n{matching_games.to_string(index=False)}"
            else:
                return f"No games found with prices above ${price}."
        elif "below" in prompt_lower:
            price_part = prompt_lower.split("below")[-1].strip()
            if not price_part.isdigit():
                return "Please specify a valid price (e.g., 'games with price below 100')."
            price = int(price_part)
            matching_games = games_data[games_data["price $"] < price]
            if not matching_games.empty:
                return f"Games with prices below ${price}:\n{matching_games.to_string(index=False)}"
            else:
                return f"No games found with prices below ${price}."
        elif "negotiable" in prompt_lower:
            matching_games = games_data[games_data["price debatable ?"].str.contains("YES", case=False, na=False)]
            if not matching_games.empty:
                return f"Here are games with negotiable prices:\n{matching_games.to_string(index=False)}"
            else:
                return "No games with negotiable prices found."

    # Account Level-related queries
    elif "account level" in prompt_lower:
        if "above" in prompt_lower:
            level_part = prompt_lower.split("above")[-1].strip()
            if not level_part.isdigit():
                return "Please specify a valid account level (e.g., 'games with account level above 200')."
            level = int(level_part)
            matching_games = games_data[games_data["Account lvl"] > level]
            if not matching_games.empty:
                return f"Games with account levels above {level}:\n{matching_games.to_string(index=False)}"
            else:
                return f"No games found with account levels above {level}."
        elif "below" in prompt_lower:
            level_part = prompt_lower.split("below")[-1].strip()
            if not level_part.isdigit():
                return "Please specify a valid account level (e.g., 'games with account level below 200')."
            level = int(level_part)
            matching_games = games_data[games_data["Account lvl"] < level]
            if not matching_games.empty:
                return f"Games with account levels below {level}:\n{matching_games.to_string(index=False)}"
            else:
                return f"No games found with account levels below {level}."

    # Return None if no specific query matches
    return "Sorry, I couldn't understand your query. Please ask about genres, prices, or account levels."





# Chat function
def chatbot(prompt, context_chunks, max_length=200):
    # First, check for specific queries
    specific_query_response = handle_query(prompt)
    if specific_query_response:
        return specific_query_response

    # If no specific query matched, use the LLM to generate a response
    answers = []
    for chunk in context_chunks:
        # Combine chunk and user prompt
        input_text = f"Context:\n{chunk}\n\nUser Query:\n{prompt}\n\nAnswer:"
        inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            num_return_sequences=1,
            do_sample=True,
            top_p=0.9,
            temperature=0.7
        )
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
        answers.append(answer)
    
    # Combine all answers into one response
    return "\n".join(answers)

# Start a chat loop
print("Welcome to the Video Game Chatbot! Ask me about the games.")
while True:
    user_input = input("\nYour question: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break
    response = chatbot(user_input, context_chunks)
    print("\n" + response)
