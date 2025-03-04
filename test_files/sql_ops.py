import logging
from typing import List
from config import Config
import psycopg2
import json

logging.basicConfig(
    filename = "sql_ops.log",
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s"
)

class SqlOps:
    def __init__(self):
        self.db_host = Config.DB_HOST
        self.db_port = Config.DB_PORT
        self.db_user = Config.DB_USER
        self.db_password = Config.DB_PASSWORD
        self.db_name = Config.DB_NAME

        try:
            self.conn = psycopg2.connect(database=self.db_name, user=self.db_user, password=self.db_password, host=self.db_host, port=self.db_port)
            self.cursor = self.conn.cursor()

        except Exception as e:
            logging.error(f"Error connecting database: {e}")

    def fetch_new_courses(self):
        """
        Fetches new courses from the database, which are courses that have been added since the last time the function was called.
        """
        try:
            query = (
                "SELECT * From customers; "
            )
            self.cursor.execute(query)
            new_courses = self.cursor.fetchall()
            logging.info(f"Fetched {len(new_courses)} new courses")
            return new_courses
        except Exception as e:
            logging.error(f"Error fetching new courses: {e}")
            return []
        
    def fetch_courses_without_quiz(self) -> List[tuple]:
        """
        Retrieves all courses that do not have any quiz (assessment) generated.
        
        Returns:
            List[tuple]: A list of courses (each represented as a tuple) that do not have a corresponding entry in the assessments table.
        """
        try:
            query = """
                SELECT c.*
                FROM courses c
                LEFT JOIN assessments a ON c.id = a.course_id
                WHERE a.id IS NULL;
            """
            self.cursor.execute(query)
            courses = self.cursor.fetchall()
            logging.info("Fetched %d courses without quiz", len(courses))
            return courses
        except Exception as e:
            logging.error("Error fetching courses without quiz: %s", e)
            return []

        
    def insert_quiz(self, course_id: str, file_path: str):
        """
        Reads json file and insert its component into the assesment table.
        fieds: id, course_id, assesment_data(getting from filepath)
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                query = """
                        Insert into assessments (course_id, assessment_data)
                        values (%s, %s)
                        RETURNING id;
                        """
                self.cursor.execute(query, (course_id, json.dumps(data)))
                new_id = self.cursor.fetchone()[0]
                self.conn.commit()

                logging.info(f"Inserted json data for course_id = {course_id} with id = {new_id}")
        except Exception as e:
            logging.error(f"Error inserting quiz: {e}")
            raise



    def close(self):
        """
        Closes the database cursor and connection..
        """

        try:
            self.cursor.close()
            self.conn.close()
            logging.info("Database connection closed")
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")

        
        
# def main():
#     # Create an instance of the SqlOps class
#     sql = SqlOps()
#     # Fetch new courses from the database
#     #new_courses = sql.fetch_new_courses()
#     #print(new_courses)
#     # Close the database connection
#     try:
#         new_record_id = sql.insert_quiz(
#             course_id="7652108b-ba01-4397-a1f1-6577d7239d18",
#             file_path="D:\\Wappnet\\repo\\transcription\\Gradient descent for multiple linear regression.json"
#         )
#         print(f"New record inserted with id: {new_record_id}")
#     except Exception as e:
#         print(f"Error inserting data: {e}")
#     sql.close()

# if __name__ == '__main__':
#     main()
        