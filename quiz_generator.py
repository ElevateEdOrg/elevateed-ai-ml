import google.generativeai as genai
from config import Config
from vector_db import QdrantClient
from typing import Dict, List, Union
import random
import json
import time
from datetime import datetime

class AutomatedMCQGenerator:
    def __init__(self, api_key: str, collection_name: str):
        """
        Initialize the Automated MCQ Generator.
        
        Args:
            api_key (str): Gemini API key for authentication.
            collection_name (str): Name of the Qdrant collection to use.
        """
        self.configure_gemini(api_key)
        self.qdrant_client = QdrantClient()
        self.collection_name = collection_name  # used if needed by new methods in QdrantClient
        
    @staticmethod
    def configure_gemini(api_key: str) -> None:
        """Configure Gemini AI with the provided API key."""
        genai.configure(api_key=api_key)
    
    def get_random_documents(self, num_docs: int = 3) -> List[Dict]:
        """
        Retrieve random documents from the collection.
        
        Returns:
            List[Dict]: List of document payloads.
        """
        try:
            # list_documents() should return a list of document payloads from Qdrant.
            all_docs = self.qdrant_client.list_documents(self.collection_name)
            if not all_docs:
                return []
            selected_docs = random.sample(all_docs, min(num_docs, len(all_docs)))
            return selected_docs
        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")
            return []

    def get_topic_based_documents(self, topic: str, num_docs: int = 3) -> List[Dict]:
        """
        Retrieve documents related to a specific topic.
        
        Args:
            topic (str): Topic to filter documents by.
            
        Returns:
            List[Dict]: List of relevant document payloads.
        """
        try:
            # search_by_topic() should be implemented in your Qdrant client.
            return self.qdrant_client.search_by_topic(
                self.collection_name, 
                topic=topic, 
                limit=num_docs
            )
        except Exception as e:
            print(f"Error retrieving topic-based documents: {str(e)}")
            return []

    def build_mcq_prompt(self, content: str, num_questions: int = 5) -> str:
        """Build prompt for MCQ generation."""
        return f"""
Generate {num_questions} diverse multiple-choice questions (MCQs) based on the following content.
Ensure questions:
- Cover different aspects of the content.
- Vary in difficulty (easy, medium, hard).
- Test both factual recall and conceptual understanding.

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

    def generate_automated_quiz(
        self,
        topic: str = None,
        num_questions: int = 5,
        num_docs: int = 3
    ) -> Dict[str, Union[str, List[Dict]]]:
        """
        Generate MCQs automatically from collection content.
        
        Args:
            topic (str, optional): Specific topic to generate questions for.
            num_questions (int): Number of questions to generate.
            num_docs (int): Number of documents to use.
            
        Returns:
            dict: Generated quiz with metadata.
        """
        try:
            # Get documents either by topic or randomly.
            if topic:
                documents = self.get_topic_based_documents(topic, num_docs)
            else:
                documents = self.get_random_documents(num_docs)
            
            if not documents:
                return {"status": "error", "message": "No documents found in collection."}
            
            # Combine content from documents.
            combined_content = " ".join(
                doc["metadata"].get("text", "") for doc in documents
            ).strip()
            
            if not combined_content:
                return {"status": "error", "message": "Retrieved documents contain no valid content."}
            
            # Build the prompt for Gemini AI.
            prompt = self.build_mcq_prompt(combined_content, num_questions)
            response = genai.generate_text(model="models/gemini-pro", content = prompt)
            
            if not response or not response.text:
                return {"status": "error", "message": "Failed to generate MCQs."}
            
            # Create quiz metadata.
            quiz_metadata = {
                "generated_at": datetime.now().isoformat(),
                "topic": topic if topic else "Random Selection",
                "num_documents_used": len(documents),
                "document_ids": [doc.get("id") for doc in documents if doc.get("id")]
            }
            
            return {"status": "success", "quiz": response.text, "metadata": quiz_metadata}
            
        except Exception as e:
            return {"status": "error", "message": f"Quiz generation failed: {str(e)}"}

    def schedule_quiz_generation(
        self,
        interval_hours: int = 24,
        topics: List[str] = None,
        num_questions: int = 5
    ) -> None:
        """
        Schedule automatic quiz generation at specified intervals.
        
        Args:
            interval_hours (int): Hours between quiz generations.
            topics (List[str], optional): List of topics to cycle through.
            num_questions (int): Number of questions per quiz.
        """
        while True:
            try:
                if topics:
                    for topic in topics:
                        quiz = self.generate_automated_quiz(topic=topic, num_questions=num_questions)
                        self.save_quiz(quiz)
                else:
                    quiz = self.generate_automated_quiz(num_questions=num_questions)
                    self.save_quiz(quiz)
                    
                # Wait for the next interval.
                time.sleep(interval_hours * 3600)
            except Exception as e:
                print(f"Error in scheduled quiz generation: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying.
    
    def save_quiz(self, quiz: Dict) -> None:
        """
        Save generated quiz to storage.
        Implement according to your storage needs (database, file, etc.).
        """
        if quiz.get("status") == "success":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quiz_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(quiz, f, indent=4)
        else:
            print("Quiz not generated successfully. Nothing to save.")

# Example usage (for testing purposes)
if __name__ == "__main__":
    # Initialize with your Gemini API key and the collection name (as set in your Qdrant config)
    quiz_generator = AutomatedMCQGenerator(
        api_key=Config.GEMINI_API_KEY,
        collection_name=Config.COLLECTION_NAME
    )
    
    # Generate a single quiz based on a topic (or leave topic as None for random documents)
    quiz = quiz_generator.generate_automated_quiz(topic="Machine Learning", num_questions=5)
    print(quiz)
    
    # To schedule regular quiz generation (this is a blocking call):
    # topics = ["Python", "JavaScript", "Data Structures"]
    # quiz_generator.schedule_quiz_generation(interval_hours=24, topics=topics, num_questions=5)
