import google.generativeai as genai
from config import Config
from file_processor import FileProcessor

genai.configure(api_key=Config.GEMINI_API_KEY)

processor = FileProcessor()

def generate_mcqs(query):
    """Retrieve relevant text using get_text_from_qdrant() and generate MCQs"""
    text = processor.get_text_from_qdrant(query, limit=3)

    if not text.strip():
        return "No valid text content found for quiz generation."

    prompt = f"""
    Generate multiple-choice questions (MCQs) based on the following text:
    {text}

    Format:
    Question:
    (A) Option 1
    (B) Option 2
    (C) Option 3
    (D) Option 4
    Correct Answer: (Letter)
    Explanation: Brief explanation of the correct answer

    Generate 5 diverse questions.
    """

    try:
        response = genai.generate_text(content=prompt)
        return response.text if response else "Failed to generate MCQs"
    except Exception as e:
        return f"MCQ generation failed: {str(e)}"
