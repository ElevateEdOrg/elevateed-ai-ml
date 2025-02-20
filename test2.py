from typing import Optional, Dict, Any, List
from qdrant_client import QdrantClient
import google.generativeai as genai
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
        self.setup_gemini()
        self.quiz_dir = "generated_quizzes"
        os.makedirs(self.quiz_dir, exist_ok=True)

    def setup_gemini(self):
        """Configure Gemini AI with API key."""
        genai.configure(api_key=Config.GEMINI_API_KEY)

    def get_collection_points(
        self,
        collection_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve points from specified collection."""
        try:
            points = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                offset=offset
            )[0]
            return points
        except Exception as e:
            self.console.print(f"[red]Error retrieving points: {str(e)}[/red]")
            return []

    def display_point_details(self, point: Dict[str, Any]) -> None:
        """Display detailed information about a single point."""
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold blue")
        table.add_column("Field", style="dim")
        table.add_column("Value")

        table.add_row("Point ID", str(point.id))
        
        if hasattr(point, 'payload'):
            for key, value in point.payload.items():
                if isinstance(value, (dict, list)):
                    table.add_row(key, json.dumps(value, indent=2))
                else:
                    table.add_row(key, str(value))

        if hasattr(point, 'vector'):
            vector_length = len(point.vector) if point.vector else 0
            table.add_row("Vector Length", str(vector_length))

        self.console.print(Panel(table, title=f"Point {point.id}", border_style="blue"))

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
            # Combine content from selected points
            combined_content = ""
            for point in points:
                if point.id in selected_ids:
                    content = point.payload.get('text', '')
                    combined_content += f"\n{content}"

            if not combined_content.strip():
                return {
                    "status": "error",
                    "message": "No content found in selected points."
                }

            # Generate quiz using Gemini
            prompt = self.build_mcq_prompt(combined_content)
            response = genai.generate_text(
                model="tunedModels/gemini-1.0-pro",
                prompt=prompt
            )


            if not response or not response.text:
                return {
                    "status": "error",
                    "message": "Failed to generate MCQs."
                }

            return {
                "status": "success",
                "quiz": response.text,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "source_ids": selected_ids,
                    "num_documents": len(selected_ids)
                }
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Quiz generation failed: {str(e)}"
            }

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
        offset = 0
        limit = 10
        selected_points = set()

        while True:
            self.console.clear()
            points = self.get_collection_points(collection_name, limit, offset)
            
            if not points:
                self.console.print("[red]No points found or error occurred[/red]")
                break

            self.console.print(f"\n[bold blue]Collection: {collection_name}[/bold blue]")
            self.console.print(f"Showing points {offset + 1} to {offset + len(points)}\n")

            # Display points table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim")
            table.add_column("Selected", style="green")
            table.add_column("Filename")
            table.add_column("Content Preview")

            for point in points:
                is_selected = "✓" if point.id in selected_points else ""
                filename = point.payload.get("filename", "N/A")
                content = point.payload.get("text", "")
                content_preview = content[:50] + "..." if len(content) > 50 else content
                
                table.add_row(
                    str(point.id),
                    is_selected,
                    filename,
                    content_preview
                )

            self.console.print(table)

            # Show selection info
            if selected_points:
                self.console.print(f"\n[green]Selected points: {', '.join(map(str, selected_points))}[/green]")

            # Navigation options
            self.console.print("\n[bold green]Options:[/bold green]")
            self.console.print("n: Next page")
            self.console.print("p: Previous page")
            self.console.print("s <id>: Select/unselect point")
            self.console.print("d <id>: Display point details")
            self.console.print("g: Generate quiz from selected points")
            self.console.print("c: Clear selection")
            self.console.print("q: Quit")

            choice = input("\nEnter your choice: ").strip().lower()

            if choice == 'q':
                break
            elif choice == 'n':
                offset += limit
            elif choice == 'p':
                offset = max(0, offset - limit)
            elif choice.startswith('s '):
                try:
                    point_id = int(choice.split()[1])
                    if point_id in selected_points:
                        selected_points.remove(point_id)
                    else:
                        selected_points.add(point_id)
                except (ValueError, IndexError):
                    self.console.print("[red]Invalid point ID[/red]")
            elif choice.startswith('d '):
                try:
                    point_id = int(choice.split()[1])
                    point = next((p for p in points if p.id == point_id), None)
                    if point:
                        self.display_point_details(point)
                        input("\nPress Enter to continue...")
                    else:
                        self.console.print("[red]Point not found[/red]")
                except (ValueError, IndexError):
                    self.console.print("[red]Invalid point ID[/red]")
            elif choice == 'g':
                if not selected_points:
                    self.console.print("[red]No points selected. Please select points first.[/red]")
                    input("\nPress Enter to continue...")
                else:
                    self.console.print("[yellow]Generating quiz...[/yellow]")
                    quiz = self.generate_quiz(points, list(selected_points))
                    if quiz["status"] == "success":
                        self.save_quiz(quiz)
                        self.console.print("\n[green]Quiz generated successfully![/green]")
                        self.console.print("\nQuiz content:")
                        self.console.print(quiz["quiz"])
                    else:
                        self.console.print(f"\n[red]Error: {quiz['message']}[/red]")
                    input("\nPress Enter to continue...")
            elif choice == 'c':
                selected_points.clear()

def main():
    """Main function to start the viewer."""
    viewer = QdrantQuizViewer()
    collection_name = input("Enter collection name: ")
    viewer.interactive_viewer(collection_name)

if __name__ == "__main__":
    main()