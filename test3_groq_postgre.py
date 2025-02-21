import os
import psycopg2
import json
from datetime import datetime
from groq import Groq
from rich.console import Console
import logging
from config import Config  # Should define PG_HOST, PG_PORT, PG_DBNAME, PG_USER, PG_PASSWORD, DOCUMENT_TABLE, GROQ_API_KEY, QUIZ_DIR

class PostgresQuizGenerator:
    def __init__(self):
        # Connect to PostgreSQL using parameters from Config
        conn_str = (
            f"dbname={Config.PG_DBNAME} user={Config.PG_USER} "
            f"password={Config.PG_PASSWORD} host={Config.PG_HOST} port={Config.PG_PORT}"
        )
        try:
            self.conn = psycopg2.connect(conn_str)
        except Exception as e:
            raise Exception(f"Error connecting to PostgreSQL: {str(e)}")
        
        self.console = Console()
        # Set up Groq API client using your Groq API key
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
        # Set up logging to file
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('postgres_quiz_generator.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        # The table containing document content
        self.table_name = Config.DOCUMENT_TABLE  # e.g., "documents"

    def retrieve_content(self, limit: int = 100, selected_ids: list = None) -> str:
        """
        Retrieve and aggregate document content from PostgreSQL.
        If selected_ids is provided, only fetch content for those IDs.
        """
        try:
            cur = self.conn.cursor()
            if selected_ids:
                query = f"SELECT content FROM {self.table_name} WHERE id = ANY(%s) LIMIT %s;"
                cur.execute(query, (selected_ids, limit))
            else:
                query = f"SELECT content FROM {self.table_name} LIMIT %s;"
                cur.execute(query, (limit,))
            rows = cur.fetchall()
            cur.close()
            # Combine all retrieved content into one string.
            combined = "\n".join(row[0] for row in rows if row[0])
            self.logger.info("Content retrieved successfully.")
            return combined
        except Exception as e:
            self.logger.error(f"Error retrieving content: {str(e)}")
            return ""

    def build_mcq_prompt(self, content: str, num_questions: int = 5) -> str:
        """
        Build the prompt for generating multiple-choice questions.
        """
        prompt = f"""
Generate {num_questions} diverse multiple-choice questions (MCQs) based on the following content.
Ensure questions:
- Cover different aspects of the content
- Vary in difficulty (easy, medium, hard)
- Test both factual recall and conceptual understanding

Content:
{content}

Format each question as:
Question:
(A) Option 1
(B) Option 2
(C) Option 3
(D) Option 4
Correct Answer: (Letter)
Explanation: Brief explanation of the correct answer
Difficulty: [Easy/Medium/Hard]
        """
        self.logger.info("MCQ prompt built.")
        return prompt.strip()

    def generate_quiz(self, num_questions: int = 5, selected_ids: list = None) -> dict:
        """
        Retrieve content, build a prompt, call Groq to generate a quiz, and return the result.
        """
        content = self.retrieve_content(selected_ids=selected_ids)
        if not content.strip():
            self.logger.error("No content found to generate quiz.")
            return {"status": "error", "message": "No content found."}
        
        prompt = self.build_mcq_prompt(content, num_questions)
        self.logger.info("Sending prompt to Groq for quiz generation.")
        try:
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}]
            )
            if not response or not response.choices:
                self.logger.error("Failed to generate quiz via Groq.")
                return {"status": "error", "message": "Quiz generation failed."}
            quiz_text = response.choices[0].message.content
            return {
                "status": "success",
                "quiz": quiz_text,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "num_questions": num_questions,
                    "source_ids": selected_ids if selected_ids else "all"
                }
            }
        except Exception as e:
            self.logger.error(f"Quiz generation error: {str(e)}")
            return {"status": "error", "message": f"Quiz generation error: {str(e)}"}

    def save_quiz(self, quiz: dict) -> None:
        """
        Save the generated quiz to a JSON file.
        """
        if quiz.get("status") == "success":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quiz_{timestamp}.json"
            quiz_dir = Config.QUIZ_DIR if hasattr(Config, "QUIZ_DIR") else "generated_quizzes"
            os.makedirs(quiz_dir, exist_ok=True)
            filepath = os.path.join(quiz_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(quiz, f, indent=4)
            self.console.print(f"[green]Quiz saved to: {filepath}[/green]")
            self.logger.info(f"Quiz saved to: {filepath}")
        else:
            self.console.print("[red]Quiz generation was not successful. Nothing to save.[/red]")
            self.logger.error("Quiz generation not successful; nothing saved.")

    def close(self):
        self.conn.close()
        self.logger.info("PostgreSQL connection closed.")

def main():
    generator = PostgresQuizGenerator()
    # Optionally, let user specify specific document IDs; otherwise, all content is used.
    selected = input("Enter comma-separated document IDs to use (or leave blank for all): ").strip()
    selected_ids = [int(x) for x in selected.split(",") if x.strip().isdigit()] if selected else None
    quiz = generator.generate_quiz(num_questions=5, selected_ids=selected_ids)
    if quiz.get("status") == "success":
        generator.console.print("[green]Quiz generated successfully![/green]")
        generator.console.print("\nQuiz content:")
        generator.console.print(quiz["quiz"])
        generator.save_quiz(quiz)
    else:
        generator.console.print(f"[red]Error: {quiz.get('message')}[/red]")
    generator.close()

if __name__ == "__main__":
    main()
