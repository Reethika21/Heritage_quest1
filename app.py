from flask import Flask, request, jsonify, render_template, session, send_from_directory, Response
import google.generativeai as genai
import re
import secrets
import threading
import concurrent.futures
import os
import sqlite3
import io

# Set up the API Key
genai.configure(api_key="AIzaSyB132JcIy5oeTqE865cpZiqPg88fZ1f8Ms")  # Your new API key

app = Flask(__name__, static_folder='static')
app.secret_key = secrets.token_hex(16)  # Generate a random secret key for session management

# Get the current directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Function to get image from database
def get_image_from_db(image_name):
    conn = sqlite3.connect('quiz_app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT image_data FROM achievement_cards WHERE name = ?", (image_name,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    return None

# Database setup function
def setup_achievement_database():
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect('quiz_app.db')
    cursor = conn.cursor()
    
    # Create a table for achievement cards
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievement_cards (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        image_data BLOB
    )
    ''')
    
    # Function to insert an image into the database
    def insert_image(name, image_path):
        try:
            # Try to use the absolute path
            full_path = os.path.join(BASE_DIR, 'static', f"{name}.jpeg")
            
            # Check if the file exists at the expected location
            if os.path.exists(full_path):
                with open(full_path, 'rb') as file:
                    image_data = file.read()
            else:
                print(f"Warning: Image not found at {full_path}")
                # Insert a record with NULL image data if file doesn't exist
                image_data = None
            
            # Check if record already exists
            cursor.execute("SELECT id FROM achievement_cards WHERE name = ?", (name,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute(
                    "UPDATE achievement_cards SET image_data = ? WHERE name = ?",
                    (image_data, name)
                )
            else:
                # Insert new record
                cursor.execute(
                    "INSERT INTO achievement_cards (name, image_data) VALUES (?, ?)",
                    (name, image_data)
                )
            
            conn.commit()
            print(f"Added {name} achievement card to database")
            
        except Exception as e:
            print(f"Error processing {name} image: {str(e)}")
    
    # Insert your achievement card images
    achievement_types = ['bronze', 'silver', 'elite']
    
    for name in achievement_types:
        insert_image(name, f"{name}.jpeg")
    
    print("Database setup complete!")
    conn.close()

# Expanded Taj Mahal text remains the same
taj_mahal_text = """
The Taj Mahal is one of the most iconic monuments in the world, known for its breathtaking beauty and rich history. 
Located in Agra, India, it was commissioned by Mughal Emperor Shah Jahan in 1632 as a symbol of love for his wife, 
Mumtaz Mahal, who died during childbirth. The construction took approximately 16 years to complete, from 1632 to 1648,
with thousands of artisans and craftsmen contributing to its grandeur. The monument is made of white marble, which was
transported from Makrana, Rajasthan, and reflects different shades depending on the time of day.

The architecture of the Taj Mahal is an extraordinary blend of Persian, Islamic, and Indian styles. It features a 
massive central dome that reaches a height of 73 meters (240 feet) surrounded by four slender minarets, each standing 
at an angle to protect the structure in case of an earthquake. The interior of the mausoleum is adorned with intricate 
calligraphy, floral patterns, and semi-precious gemstones like jade, crystal, lapis lazuli, and turquoise embedded in 
the marble through a technique called pietra dura.

The Taj Mahal complex is set in a large 42-acre garden, following the Mughal charbagh design - a formal Persian garden 
divided into four parts by walkways and water channels. The complex also includes a mosque and a guest house on either 
side of the mausoleum, maintaining perfect symmetry. The entire complex is surrounded by a wall with beautiful gates, 
with the main entrance being the Great Gate, or Darwaza-i-Rauza.

Beyond its architectural beauty, the Taj Mahal holds deep historical and cultural significance. It was designated as 
a UNESCO World Heritage Site in 1983 and is recognized as one of the Seven Wonders of the World. Over the centuries, 
it has survived wars, natural disasters, and environmental threats, yet it continues to stand as a testament to 
India's rich heritage.

Despite its enduring beauty, the Taj Mahal faces challenges from pollution and environmental damage. The nearby Yamuna 
River has suffered from pollution, affecting the monument's foundation, while air pollution from nearby industries has 
led to discoloration of its pristine white marble. Conservation efforts, including restricting vehicular traffic and 
regular cleaning, have been put in place to preserve its magnificence. The monument attracts 7-8 million visitors 
annually, making it one of the most visited tourist attractions in India.
"""

# Improved function to generate MCQs with optimized prompt
def generate_mcq(text, difficulty):
    model = genai.GenerativeModel("gemini-2.0-flash-lite-001")  # Using the lightweight model for speed

    # Enhanced prompt with clearer instructions and constraints
    prompt = f"""
    Generate a {difficulty}-level multiple-choice question based on this text about the Taj Mahal:
    {text}
    
    Requirements:
    - Make the question factually accurate and directly based on the text
    - For "easy" level: focus on basic facts and clear details
    - For "medium" level: focus on connections between concepts
    - For "hard" level: focus on deeper implications and specific details
    - Ensure ONE CLEAR correct answer and three plausible but incorrect alternatives
    - Structure options so the correct answer isn't always in the same position
    
    Format your response EXACTLY as follows with no additional text or explanation:
    Question: <MCQ Question>
    a) <Option A>
    b) <Option B>
    c) <Option C>
    d) <Option D>
    Answer: <Correct Option>
    """

    # Add generation parameters for faster responses
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,           # Lower temperature for more deterministic output
            max_output_tokens=300,     # Limit token length
            response_mime_type="text/plain"
        )
    )
    return response.text.strip()  # Extract the generated MCQ

# Function to parse MCQ into components
def parse_mcq(mcq_text):
    # Extract question
    question_match = re.search(r'Question: (.*?)(?=\na\)|\r\na\))', mcq_text, re.DOTALL)
    question = question_match.group(1).strip() if question_match else ""
    
    # Extract options
    options = {}
    for option in ['a', 'b', 'c', 'd']:
        option_match = re.search(rf'{option}\) (.*?)(?=\n[b-d]\)|\nAnswer:|\r\n[b-d]\)|\r\nAnswer:|$)', mcq_text, re.DOTALL)
        options[option] = option_match.group(1).strip() if option_match else ""
    
    # Extract answer
    answer_match = re.search(r'Answer: ([a-d])', mcq_text)
    answer = answer_match.group(1) if answer_match else ""
    
    return {
        "question": question,
        "options": options,
        "answer": answer
    }

# Generate MCQs in parallel for speed
def generate_mcqs_parallel(text, difficulties, questions_per_difficulty):
    all_mcqs = {difficulty: [] for difficulty in difficulties}
    
    # Function to generate and parse a single MCQ for a specific difficulty
    def generate_and_parse(difficulty):
        mcq_text = generate_mcq(text, difficulty)
        parsed_mcq = parse_mcq(mcq_text)
        parsed_mcq["difficulty"] = difficulty
        return difficulty, parsed_mcq
    
    # Create tasks for parallel execution
    tasks = []
    for difficulty in difficulties:
        for _ in range(questions_per_difficulty):
            tasks.append(difficulty)
    
    # Execute tasks in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(generate_and_parse, tasks))
    
    # Organize results
    for difficulty, parsed_mcq in results:
        all_mcqs[difficulty].append(parsed_mcq)
    
    return all_mcqs

# API Route for serving achievement images from the database
@app.route('/api/achievement-image/<image_name>')
def serve_achievement_image(image_name):
    image_data = get_image_from_db(image_name)
    
    if image_data:
        return Response(
            io.BytesIO(image_data),
            mimetype='image/jpeg'
        )
    
    # Try to serve from static folder as fallback
    static_path = os.path.join(BASE_DIR, 'static', f"{image_name}.jpeg")
    if os.path.exists(static_path):
        return send_from_directory(app.static_folder, f"{image_name}.jpeg")
    
    return "Image not found", 404

# API Route for generating MCQs
@app.route('/generate_mcqs', methods=['POST'])
def generate_mcqs():
    # Generate questions for each difficulty level in parallel
    all_mcqs = generate_mcqs_parallel(
        text=taj_mahal_text,
        difficulties=["easy", "medium", "hard"],
        questions_per_difficulty=2
    )
    
    # Store in session for retrieval
    session["mcqs"] = all_mcqs
    session["current_difficulty"] = "easy"
    session["current_index"] = 0
    session["score"] = 0
    # Initialize achievements
    session["achievements"] = {
        "easy": False,
        "medium": False,
        "hard": False
    }
    
    # Return the first question (easy level, first question)
    first_question = all_mcqs["easy"][0]
    return jsonify({
        "question": first_question["question"],
        "options": first_question["options"],
        "difficulty": "easy",
        "currentDifficulty": "easy",
        "currentIndex": 0,
        "totalEasy": len(all_mcqs["easy"]),
        "totalMedium": len(all_mcqs["medium"]),
        "totalHard": len(all_mcqs["hard"]),
        "score": 0,
        "achievements": session["achievements"]
    })

# API Route for checking answers
@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    selected_option = data.get("selectedOption")
    
    mcqs = session.get("mcqs", {})
    current_difficulty = session.get("current_difficulty", "easy")
    current_index = session.get("current_index", 0)
    score = session.get("score", 0)
    achievements = session.get("achievements", {"easy": False, "medium": False, "hard": False})
    
    if not mcqs:
        return jsonify({"error": "No questions available"}), 400
    
    # Get current question
    current_mcq = mcqs[current_difficulty][current_index]
    is_correct = selected_option == current_mcq["answer"]
    
    if is_correct:
        score += 1
        session["score"] = score
    
    # Determine next question
    next_difficulty = current_difficulty
    next_index = current_index + 1
    achievement_earned = None
    
    # If we've finished the current difficulty level
    if next_index >= len(mcqs[current_difficulty]):
        # Mark achievement for completed difficulty
        achievements[current_difficulty] = True
        session["achievements"] = achievements
        achievement_earned = current_difficulty
        
        # Move to next difficulty level
        if current_difficulty == "easy":
            next_difficulty = "medium"
            next_index = 0
        elif current_difficulty == "medium":
            next_difficulty = "hard"
            next_index = 0
        else:  # We've finished all questions
            return jsonify({
                "isCorrect": is_correct,
                "correctAnswer": current_mcq["answer"],
                "score": score,
                "isComplete": True,
                "totalQuestions": len(mcqs["easy"]) + len(mcqs["medium"]) + len(mcqs["hard"]),
                "achievements": achievements,
                "achievementEarned": achievement_earned
            })
    
    # Update session
    session["current_difficulty"] = next_difficulty
    session["current_index"] = next_index
    
    # Get next question
    next_mcq = mcqs[next_difficulty][next_index]
    
    return jsonify({
        "isCorrect": is_correct,
        "correctAnswer": current_mcq["answer"],
        "score": score,
        "isComplete": False,
        "achievements": achievements,
        "achievementEarned": achievement_earned,
        "nextQuestion": {
            "question": next_mcq["question"],
            "options": next_mcq["options"],
            "difficulty": next_difficulty,
            "currentDifficulty": next_difficulty,
            "currentIndex": next_index,
            "totalEasy": len(mcqs["easy"]),
            "totalMedium": len(mcqs["medium"]),
            "totalHard": len(mcqs["hard"])
        }
    })

# Reset quiz
@app.route('/reset_quiz', methods=['POST'])
def reset_quiz():
    session.pop("mcqs", None)
    session.pop("current_difficulty", None)
    session.pop("current_index", None)
    session.pop("score", None)
    session.pop("achievements", None)
    return jsonify({"status": "reset"})

# Serve HTML frontend
@app.route('/')
def index():
    return render_template("index.html")

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    # Setup the achievement database before starting the app
    setup_achievement_database()
    app.run(debug=True)