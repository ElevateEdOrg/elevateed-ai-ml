import re
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

from qdrant_client import QdrantClient
from groq import Groq
from config import Config
from rich.console import Console
from rich.table import Table

# QdrantService is responsible for interacting with Qdrant.
class QdrantService:
    def __init__(self, host: str = "localhost", port: int = 6333, logger: logging.Logger = None):
        self.client = QdrantClient(host=host, port=port)
        self.logger = logger or logging.getLogger(__name__)
    
    def get_collection_points(self, collection_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            points = self.client.scroll(collection_name=collection_name, limit=limit, offset=offset)[0]
            self.logger.info(f'Points retrieved from collection {collection_name}')
            return points
        except Exception as e:
            self.logger.error(f'Error retrieving points: {str(e)}')
            return []

# QuizParser is responsible for converting plain-text quiz output into a structured dictionary.
class QuizParser:
    def parse(self, quiz_text: str) -> Dict[str, Any]:
        question_blocks = re.split(r'\n*Question \d+:\n', quiz_text)[1:]
        quiz_dict = {}
        for idx, block in enumerate(question_blocks, start=1):
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if not lines:
                continue

            # Extract the question text (assumed to be the first line)
            question_text = lines[0]

            # Extract options that start with (A), (B), etc.
            options = {}
            option_pattern = re.compile(r'^\((.)\)\s*(.*)')
            current_index = 1
            while current_index < len(lines):
                match = option_pattern.match(lines[current_index])
                if match:
                    letter = match.group(1)
                    option_text = match.group(2)
                    options[letter] = option_text
                    current_index += 1
                else:
                    break

            # Extract the remaining fields
            correct_answer = ""
            explanation = ""
            difficulty = ""
            for line in lines[current_index:]:
                if line.startswith("Correct Answer:"):
                    correct_answer = line.split("Correct Answer:")[-1].strip()
                elif line.startswith("Explanation:"):
                    explanation = line.split("Explanation:")[-1].strip()
                elif line.startswith("Difficulty:"):
                    difficulty = line.split("Difficulty:")[-1].strip()

            quiz_dict[f"Q{idx}"] = {
                "q": question_text,
                "options": options,
                "ans": correct_answer,
                "explanation": explanation,
                "difficulty": difficulty
            }
        return quiz_dict

# QuizGenerator builds the prompt, calls the Groq API, and parses the response.
class QuizGenerator:
    def __init__(self, groq_client: Groq, quiz_parser: QuizParser, logger: logging.Logger = None):
        self.groq_client = groq_client
        self.quiz_parser = quiz_parser
        self.logger = logger or logging.getLogger(__name__)
    
    def build_prompt(self, content: str, num_questions: int = 5) -> str:
        self.logger.info('Building MCQ prompt')
        return f"""
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

    def generate(self, content: str, num_questions: int = 5) -> Dict[str, Any]:
        if not content.strip():
            self.logger.error('No content provided for quiz generation.')
            return {"status": "error", "message": "No content provided for quiz generation."}
        
        prompt = self.build_prompt(content, num_questions)
        try:
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}]
            )
            if not response or not response.choices:
                self.logger.error('Failed to generate MCQs.')
                return {"status": "error", "message": "Failed to generate MCQs."}
            
            quiz_text = response.choices[0].message.content
            quiz_structured = self.quiz_parser.parse(quiz_text)
            return {
                "status": "success",
                "quiz": quiz_structured,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "num_questions": num_questions
                }
            }
        except Exception as e:
            self.logger.error(f'Quiz generation failed: {str(e)}')
            return {"status": "error", "message": f"Quiz generation failed: {str(e)}"}

# QuizSaver is responsible for persisting the generated quiz to disk.
class QuizSaver:
    def __init__(self, quiz_dir: str = "generated_quizzes", logger: logging.Logger = None):
        self.quiz_dir = quiz_dir
        os.makedirs(self.quiz_dir, exist_ok=True)
        self.logger = logger or logging.getLogger(__name__)
    
    def save(self, quiz: Dict[str, Any], source_ids: List[int]) -> None:
        if quiz.get("status") != "success":
            self.logger.error('Quiz not generated successfully. Nothing to save.')
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_ids_str = "_".join(map(str, source_ids))
        filename = f"quiz_{source_ids_str}_{timestamp}.json"
        filepath = os.path.join(self.quiz_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(quiz, f, indent=4)
            self.logger.info(f'Quiz saved to: {filepath}')
        except Exception as e:
            self.logger.error(f'Failed to save quiz: {str(e)}')

# QdrantQuizViewer orchestrates the interactive workflow.
class QdrantQuizViewer:
    def __init__(self,
                 qdrant_service: QdrantService,
                 quiz_generator: QuizGenerator,
                 quiz_saver: QuizSaver,
                 console: Console,
                 logger: logging.Logger = None):
        self.qdrant_service = qdrant_service
        self.quiz_generator = quiz_generator
        self.quiz_saver = quiz_saver
        self.console = console
        self.logger = logger or logging.getLogger(__name__)

    def interactive_viewer(self, collection_name: str) -> None:
        points = self.qdrant_service.get_collection_points(collection_name)
        selected_points = set()
        
        while True:
            self.console.clear()
            if not points:
                self.console.print("[red]No points found or error occurred[/red]")
                self.logger.error('No points found or error occurred')
                break

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim")
            table.add_column("Selected", style="green")
            table.add_column("Filename")
            table.add_column("Content Preview")

            for point in points:
                is_selected = "✓" if point.id in selected_points else ""
                filename = point.payload.get("filename", "N/A")
                content_preview = point.payload.get("text", "")[:50] + "..."
                table.add_row(str(point.id), is_selected, filename, content_preview)

            self.console.print(table)
            self.console.print("\nOptions: [s <id>] Select, [g] Generate, [q] Quit")
            choice = input("\nEnter choice: ").strip().lower()

            if choice == 'q':
                break
            elif choice.startswith('s '):
                try:
                    point_id = int(choice.split()[1])
                    if point_id in selected_points:
                        selected_points.remove(point_id)
                    else:
                        selected_points.add(point_id)
                except (ValueError, IndexError):
                    self.console.print("[red]Invalid point ID[/red]")
                    self.logger.error('Invalid point ID')
            elif choice == 'g':
                if not selected_points:
                    self.console.print("[red]No points selected. Please select points first.[/red]")
                    self.logger.error('No points selected. Please select points first.')
                else:
                    combined_content = "\n".join(
                        [point.payload.get('text', '') for point in points if point.id in selected_points]
                    )
                    quiz = self.quiz_generator.generate(combined_content)
                    if quiz["status"] == "success":
                        self.quiz_saver.save(quiz, list(selected_points))
                        self.console.print("\n[green]Quiz generated successfully![/green]")
                        self.console.print("\nQuiz content:")
                        self.console.print(json.dumps(quiz["quiz"], indent=4))
                        self.logger.info('Quiz generated successfully')
                    else:
                        self.console.print(f"\n[red]Error: {quiz['message']}[/red]")
                        self.logger.error(f'Error: {quiz["message"]}')

def main():
    # Set up logging
    logger = logging.getLogger("QdrantQuizViewer")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('qdrant_quiz_viewer.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    console = Console()

    # Dependency injection for inversion of control
    qdrant_service = QdrantService(logger=logger)
    quiz_parser = QuizParser()
    groq_client = Groq(api_key=Config.GROQ_API_KEY)
    quiz_generator = QuizGenerator(groq_client, quiz_parser, logger=logger)
    quiz_saver = QuizSaver(logger=logger)

    viewer = QdrantQuizViewer(qdrant_service, quiz_generator, quiz_saver, console, logger=logger)
    collection_name = input("Enter collection name: ")
    viewer.interactive_viewer(collection_name)

if __name__ == "__main__":
    main()
