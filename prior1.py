from flask import Flask, render_template, jsonify
import google.generativeai as genai
import threading

# Configure Gemini API
genai.configure(api_key="AIzaSyB132JcIy5oeTqE865cpZiqPg88fZ1f8Ms")

# Update to include static_folder parameter
app = Flask(__name__, template_folder='templates', static_folder='static')

# Fixed text about the Taj Mahal
TEXT = """
The Taj Mahal, one of the most iconic monuments in the world, is a stunning masterpiece of Mughal architecture located in Agra, India. Built by the Mughal Emperor Shah Jahan in memory of his beloved wife, Mumtaz Mahal, the Taj Mahal is a symbol of eternal love and an architectural wonder that attracts millions of visitors every year. Construction of this grand mausoleum began in 1632 and was completed in 1648, although some finishing touches continued until 1653. Made primarily of white marble, the Taj Mahal stands majestically on the banks of the Yamuna River, its beauty amplified by the reflection in the water. The monument is a UNESCO World Heritage Site and is widely recognized as one of the Seven Wonders of the World. The intricate carvings, inlaid semi-precious stones, and the symmetrical design of the structure showcase the exquisite craftsmanship of Mughal artisans. The Taj Mahal complex consists of several structures, including a mosque, a guest house, and an elaborate garden that represents the concept of paradise in Islamic tradition. The central dome, which rises to about 73 meters, is surrounded by four minarets that lean slightly outward to prevent damage in case of an earthquake. The interiors of the Taj Mahal feature delicate marble screens, calligraphy inscriptions from the Quran, and floral motifs that enhance its ethereal beauty. The cenotaphs of Mumtaz Mahal and Shah Jahan are placed inside the main chamber, though their actual tombs lie in a lower crypt. The construction of the Taj Mahal required the labor of around 20,000 artisans and workers, along with materials sourced from various regions, including Rajasthan, China, Tibet, and Afghanistan. The white marble used in the structure was transported from Makrana in Rajasthan, while jade and crystal came from China. The harmonious blend of Persian, Islamic, and Indian architectural styles is evident in the detailed ornamentation and symmetrical planning of the monument. The Taj Mahal's beauty changes with the time of day, appearing pinkish in the morning, milky white in the afternoon, and golden under the moonlight. This unique transformation is attributed to the reflective properties of the marble, which interact with different lighting conditions. The lush gardens surrounding the Taj Mahal, known as the Charbagh, are divided into four sections, symbolizing the four rivers of paradise as described in Islamic texts. These gardens are filled with fountains, water channels, and perfectly aligned pathways that enhance the monument's grandeur. The Taj Mahal is not just a historical monument but a living testament to the artistic and engineering brilliance of the Mughal era. Over the years, it has withstood the test of time, surviving natural calamities and environmental changes. However, pollution and industrial emissions have posed significant threats to the pristine white marble, leading to discoloration and structural damage. The Indian government and international organizations have taken several measures to protect and preserve the Taj Mahal, including restricting vehicular movement near the site and implementing conservation projects. Despite these challenges, the Taj Mahal continues to be a major tourist attraction, drawing visitors from all over the world who come to admire its unparalleled beauty and historical significance. It is especially popular among couples and newlyweds, who view it as a symbol of everlasting love. The Taj Mahal also plays a crucial role in India's tourism industry, contributing significantly to the economy through ticket sales, guided tours, and local businesses. Many poets, historians, and travelers have written extensively about the Taj Mahal, describing it as a dream in marble and an architectural marvel that transcends time. Rabindranath Tagore famously referred to it as "a teardrop on the cheek of time," highlighting its emotional and artistic significance. The Taj Mahal's history is also marked by intrigue and legend, with stories suggesting that Shah Jahan planned to build a black marble replica across the Yamuna River as his own tomb, though this plan never materialized. After Shah Jahan's death, he was laid to rest beside Mumtaz Mahal, completing the love story that inspired the monument. The Taj Mahal remains a powerful reminder of India's rich cultural heritage and the artistic legacy of the Mughal Empire. It serves as a place of inspiration for architects, artists, and historians, who continue to study its design and construction techniques. The monument has also been featured in numerous films, books, and artworks, further cementing its status as a global icon. Whether viewed up close or from a distance, the Taj Mahal never fails to captivate its admirers with its timeless elegance and romantic allure. As the sun sets over Agra, the silhouette of the Taj Mahal against the twilight sky creates a breathtaking scene, leaving visitors in awe of its splendor. The magic of the Taj Mahal lies not only in its architectural perfection but also in the emotions it evokes—a monument of love, loss, and eternal beauty that continues to stand as a beacon of human creativity and devotion.
"""

# Improved function to summarize text using Gemini API
def summarize_text():
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    
    # Simplified prompt that requests only the most important points
    prompt = f"""
    Create a very concise summary with ONLY 10-12 bullet points total about the Taj Mahal based on the text below.
    The summary should be organized into these 5 categories, with exactly 2 points per category:
    
    - Historical facts and dates (2 points)
    - Architectural features (2 points)
    - Cultural significance (2 points)
    - Environmental challenges (2 points)
    - Interesting details (2 points)
    
    Format each category as a main bullet point, with its 2 sub-points underneath.
    Keep each point very brief (1 line each).
    Use only information explicitly stated in the provided text.
    
    Text to summarize:
    {TEXT}
    """
    
    # Add generation parameters for better quality and deterministic output
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,  # Lower temperature for more deterministic output
            max_output_tokens=800,
            response_mime_type="text/plain"
        )
    )
    return response.text

# Cache for storing the summary to avoid repeated API calls
summary_cache = None
summary_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('prior.html')

@app.route('/get_summary', methods=['GET'])
def get_summary():
    global summary_cache
    
    # Check if summary is already cached
    with summary_lock:
        if not summary_cache:
            summary_cache = summarize_text()
    
    return jsonify({"summary": summary_cache})

if __name__ == '__main__':
    app.run(debug=True)