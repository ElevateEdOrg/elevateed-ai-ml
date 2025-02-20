from typing import Optional, Dict, Any, List
from qdrant_client import QdrantClient
import json
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

class QdrantViewer:
    def __init__(self, host: str = "localhost", port: int = 6333):
        """
        Initialize QdrantViewer with connection details.
        
        Args:
            host (str): Qdrant server host
            port (int): Qdrant server port
        """
        self.client = QdrantClient(host=host, port=port)
        self.console = Console()

    def get_collection_points(
        self,
        collection_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve points from specified collection.
        
        Args:
            collection_name (str): Name of the collection
            limit (int): Maximum number of points to retrieve
            offset (int): Number of points to skip
            
        Returns:
            List[Dict]: List of points with their data
        """
        try:
            # Get points from collection
            points = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                offset=offset
            )[0]  # scroll returns (points, offset)
            
            return points
        except Exception as e:
            self.console.print(f"[red]Error retrieving points: {str(e)}[/red]")
            return []

    def display_point_details(self, point: Dict[str, Any]) -> None:
        """
        Display detailed information about a single point.
        
        Args:
            point (Dict): Point data including payload and vectors
        """
        # Create a rich table for point details
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold blue")
        table.add_column("Field", style="dim")
        table.add_column("Value")

        # Add basic point information
        table.add_row("Point ID", str(point.id))
        
        # Display payload
        if hasattr(point, 'payload'):
            for key, value in point.payload.items():
                if isinstance(value, (dict, list)):
                    table.add_row(key, json.dumps(value, indent=2))
                else:
                    table.add_row(key, str(value))

        # Display vector information
        if hasattr(point, 'vector'):
            vector_length = len(point.vector) if point.vector else 0
            table.add_row("Vector Length", str(vector_length))

        self.console.print(Panel(table, title=f"Point {point.id}", border_style="blue"))

    def interactive_viewer(self, collection_name: str) -> None:
        """
        Start an interactive viewer for the collection.
        
        Args:
            collection_name (str): Name of the collection to view
        """
        offset = 0
        limit = 10
        while True:
            self.console.clear()
            points = self.get_collection_points(collection_name, limit, offset)
            
            if not points:
                self.console.print("[red]No points found or error occurred[/red]")
                break

            # Display collection information
            self.console.print(f"\n[bold blue]Collection: {collection_name}[/bold blue]")
            self.console.print(f"Showing points {offset + 1} to {offset + len(points)}\n")

            # Create main table for points list
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim")
            table.add_column("Payload Preview")
            table.add_column("Vector Length")

            for point in points:
                payload_preview = str(point.payload)[:50] + "..." if len(str(point.payload)) > 50 else str(point.payload)
                vector_length = len(point.vector) if point.vector else 0
                table.add_row(
                    str(point.id),
                    payload_preview,
                    str(vector_length)
                )

            self.console.print(table)

            # Navigation options
            self.console.print("\n[bold green]Options:[/bold green]")
            self.console.print("n: Next page")
            self.console.print("p: Previous page")
            self.console.print("d <id>: Display point details")
            self.console.print("q: Quit")

            choice = input("\nEnter your choice: ").strip().lower()

            if choice == 'q':
                break
            elif choice == 'n':
                offset += limit
            elif choice == 'p':
                offset = max(0, offset - limit)
            elif choice.startswith('d '):
                try:
                    point_id = int(choice.split()[1])
                    point = next((p for p in points if p.id == point_id), None)
                    if point:
                        self.display_point_details(point)
                        input("\nPress Enter to continue...")
                    else:
                        self.console.print("[red]Point not found[/red]")
                        input("\nPress Enter to continue...")
                except (ValueError, IndexError):
                    self.console.print("[red]Invalid point ID[/red]")
                    input("\nPress Enter to continue...")

def main():
    """Main function to start the viewer."""
    viewer = QdrantViewer()
    collection_name = input("Enter collection name: ")
    viewer.interactive_viewer(collection_name)

if __name__ == "__main__":
    main()