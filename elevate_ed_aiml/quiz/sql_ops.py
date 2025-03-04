# quiz/sql_ops.py

import logging
import psycopg2
import json
from typing import List, Tuple
import os
from quiz.config import Config

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

logging.basicConfig(
    filename="sql_ops.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class SqlOps:
    def __init__(self):
        self.db_host = DB_HOST
        self.db_port = DB_PORT
        self.db_user = DB_USER
        self.db_password = DB_PASSWORD
        self.db_name = DB_NAME
        try:
            self.conn = psycopg2.connect(
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")

    def fetch_lecture_paths_for_course(self, course_id: str) -> List[Tuple[str, str]]:
        try:
            query = """
                select lectures.id, lectures.video_path 
                from lectures 
                full join courses 
                on courses.id = lectures.course_id
                where lectures.course_id = %s	;
            """
            self.cursor.execute(query, (course_id,))
            rows = self.cursor.fetchall()
            logging.info(f"Fetched {len(rows)} lecture paths for course {course_id}")
            return rows
        except Exception as e:
            logging.error(f"Error fetching lecture paths: {e}")
            return []

    def insert_quiz(self, course_id: str, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            query = """
                INSERT INTO assessments (course_id, assessment_data)
                VALUES (%s, %s)
                RETURNING id;
            """
            self.cursor.execute(query, (course_id, json.dumps(data)))
            new_id = self.cursor.fetchone()[0]
            self.conn.commit()
            logging.info(f"Inserted quiz JSON for course_id = {course_id} with id = {new_id}")
            return new_id
        except Exception as e:
            logging.error(f"Error inserting quiz: {e}")
            raise

    def close(self):
        try:
            self.cursor.close()
            self.conn.close()
            logging.info("Database connection closed")
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")
