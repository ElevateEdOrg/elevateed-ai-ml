from typing import Optional, Dict, Any, List
from qdrant_client import QdrantClient
from groq import Groq
from config import Config
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import json
from datetime import datetime
import os

class QdrantQuizViewer:
    def __init__(self, host: str = "localhost", port: int = 6333):
        """
        Initialize QdrantQuizViewer with connection details.
        """
        self.client = QdrantClient(host=host, port=port)
        self.console = Console()
        self.setup_groq()
        self.quiz_dir = "generated_quizzes"
        os.makedirs(self.quiz_dir, exist_ok=True)

    def setup_groq(self):
        """Configure Groq API with API key."""
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)

    def get_collection_points(self, collection_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve points from specified collection."""
        try:
            points = self.client.scroll(collection_name=collection_name, limit=limit, offset=offset)[0]
            return points
        except Exception as e:
            self.console.print(f"[red]Error retrieving points: {str(e)}[/red]")
            return []

    def build_mcq_prompt(self, content: str, num_questions: int = 5) -> str:
        """Build prompt for MCQ generation."""
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
    
    def generate_quiz(self, points: List[Dict], selected_ids: List[int]) -> Dict:
        """Generate quiz from selected points."""
        try:
            combined_content = "\n".join([point.payload.get('text', '') for point in points if point.id in selected_ids])
            
            if not combined_content.strip():
                return {"status": "error", "message": "No content found in selected points."}
            
            prompt = self.build_mcq_prompt(combined_content)
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}]
            )
            
            if not response or not response.choices:
                return {"status": "error", "message": "Failed to generate MCQs."}
            
            return {
                "status": "success",
                "quiz": response.choices[0].message.content,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "source_ids": selected_ids,
                    "num_documents": len(selected_ids)
                }
            }
        except Exception as e:
            return {"status": "error", "message": f"Quiz generation failed: {str(e)}"}
    
    def save_quiz(self, quiz: Dict) -> None:
        """Save generated quiz to file."""
        if quiz.get("status") == "success":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_ids = "_".join(map(str, quiz.get("metadata", {}).get("source_ids", [])))
            filename = f"quiz_{source_ids}_{timestamp}.json"
            filepath = os.path.join(self.quiz_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(quiz, f, indent=4)
            self.console.print(f"[green]Quiz saved to: {filepath}[/green]")
        else:
            self.console.print("[red]Quiz not generated successfully. Nothing to save.[/red]")
    
    def interactive_viewer(self, collection_name: str) -> None:
        """Start an interactive viewer for the collection."""
        points = self.get_collection_points(collection_name)
        selected_points = set()
        
        while True:
            self.console.clear()
            if not points:
                self.console.print("[red]No points found or error occurred[/red]")
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
            self.console.print("\nOptions: [n] Next, [p] Prev, [s <id>] Select, [g] Generate, [q] Quit")
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
            elif choice == 'g':
                if not selected_points:
                    self.console.print("[red]No points selected. Please select points first.[/red]")
                else:
                    quiz = self.generate_quiz(points, list(selected_points))
                    if quiz["status"] == "success":
                        self.save_quiz(quiz)
                        self.console.print("\n[green]Quiz generated successfully![/green]")
                        self.console.print("\nQuiz content:")
                        self.console.print(quiz["quiz"])
                    else:
                        self.console.print(f"\n[red]Error: {quiz['message']}[/red]")
            

def main():
    """Main function to start the viewer."""
    viewer = QdrantQuizViewer()
    collection_name = input("Enter collection name: ")
    viewer.interactive_viewer(collection_name)

if __name__ == "__main__":
    main()
