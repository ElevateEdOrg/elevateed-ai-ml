def generate_mcqs(text: str, num_questions: int = 5):
    """
    Generate sample multiple-choice questions (MCQs) based on input text.
    This dummy implementation simply returns sample questions.
    Replace this with your actual integration with Gemini AI if needed.
    """
    questions = []
    for i in range(num_questions):
        question = f"Sample Question {i+1} based on: {text[:50]}..."
        options = [f"Option {opt}" for opt in ["A", "B", "C", "D"]]
        answer = options[0]  # Dummy correct answer
        questions.append({
            "question": question,
            "options": options,
            "answer": answer
        })
    return questions
