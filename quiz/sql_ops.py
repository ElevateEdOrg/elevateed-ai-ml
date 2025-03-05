# # quiz/sql_ops.py

# import logging
# import psycopg2
# import json
# from typing import List, Tuple
# from quiz.config import Config

# logging.basicConfig(
#     filename="sql_ops.log",
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s"
# )

# class SqlOps:
#     def __init__(self):
#         self.db_host = Config.DB_HOST
#         self.db_port = Config.DB_PORT
#         self.db_user = Config.DB_USER
#         self.db_password = Config.DB_PASSWORD
#         self.db_name = Config.DB_NAME

#         try:
#             self.conn = psycopg2.connect(
#                 database=self.db_name,
#                 user=self.db_user,
#                 password=self.db_password,
#                 host=self.db_host,
#                 port=self.db_port
#             )
#             # self.conn = psycopg2.connect(
#             #     dbname="Elevatedb",
#             #     user="postgres",
#             #     password="new_password",
#             #     host="localhost",
#             #     port="5432"
#             # )
#             self.cursor = self.conn.cursor()
#         except Exception as e:
#             logging.error(f"Error connecting to database: {e}")

#     def fetch_lecture_paths_for_course(self, course_id: str) -> List[Tuple[str, str]]:
#         """
#         Fetches (lecture_id, video_path) for all lectures in a given course.
#         """
#         try:
#             query = """
#                select lectures.id, lectures.video_path 
#                 from lectures 
#                 full join 
#                 courses 
#                 on courses.id = lectures.course_id
#                 where lectures.course_id = %s
#                 and lectures.video_path is not null	;
#             """
#             self.cursor.execute(query, (course_id,))
#             rows = self.cursor.fetchall()
#             logging.info(f"Fetched {len(rows)} lecture paths for course {course_id}")
#             return rows
#         except Exception as e:
#             logging.error(f"Error fetching lecture paths: {e}")
#             return []

#     def insert_quiz(self, course_id: str, file_path: str):
#         """
#         Reads a JSON file from file_path and inserts its content into the 'assessments' table.
#         Fields: course_id, assessment_data (JSON)
#         """
#         try:
#             with open(file_path, 'r', encoding='utf-8') as file:
#                 data = json.load(file)
#                 query = """
#                     INSERT INTO assessments (course_id, assessment_data)
#                     VALUES (%s, %s)
#                     ON CONFLICT (course_id)
#                     DO UPDATE SET assessment_data = EXCLUDED.assessment_data
#                     RETURNING id;
#                 """
#                 self.cursor.execute(query, (course_id, json.dumps(data)))
#                 new_id = self.cursor.fetchone()[0]
#                 self.conn.commit()

#                 logging.info(f"Inserted quiz JSON for course_id = {course_id} with assessment_id = {new_id}")
#         except Exception as e:
#             logging.error(f"Error inserting quiz: {e}")
#             raise

#     def close(self):
#         """
#         Closes the database cursor and connection.
#         """
#         try:
#             if self.cursor:
#                 self.cursor.close()
#             if self.conn:
#                 self.conn.close()
#             logging.info("Database connection closed")
#         except Exception as e:
#             logging.error(f"Error closing database connection: {e}")


import logging
import psycopg2
import json
from typing import List, Tuple
from quiz.config import Config

logging.basicConfig(
    filename="sql_ops.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class SqlOps:
    def __init__(self):
        self.db_host = Config.DB_HOST
        self.db_port = Config.DB_PORT
        self.db_user = Config.DB_USER
        self.db_password = Config.DB_PASSWORD
        self.db_name = Config.DB_NAME

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
        """
        Fetches (lecture_id, video_path) for all lectures in a given course.
        """
        try:
            query = """
               SELECT lectures.id, lectures.video_path 
               FROM lectures 
               FULL JOIN courses ON courses.id = lectures.course_id
               WHERE lectures.course_id = %s
               AND lectures.video_path IS NOT NULL;
            """
            self.cursor.execute(query, (course_id,))
            rows = self.cursor.fetchall()
            logging.info(f"Fetched {len(rows)} lecture paths for course {course_id}")
            return rows
        except Exception as e:
            logging.error(f"Error fetching lecture paths: {e}")
            return []

    def insert_quiz(self, course_id: str, lecture_id: str, file_path: str):
        """
        Reads a JSON file from file_path and inserts its content into the 'assessments' table.
        Fields: course_id, lecture_id, assessment_data (JSON)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # Make sure you have a UNIQUE constraint or PRIMARY KEY on (lecture_id)
                # or a unique index for ON CONFLICT to work properly with lecture_id.
                query = """
                    INSERT INTO assessments (course_id, lecture_id, assessment_data)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (lecture_id)
                    DO UPDATE 
                        SET assessment_data = EXCLUDED.assessment_data
                    RETURNING id;
                """
                self.cursor.execute(query, (course_id, lecture_id, json.dumps(data)))
                result = self.cursor.fetchone()

                # result should be a tuple containing the returned 'id'
                if result:
                    new_id = result[0]
                    logging.info(
                        f"Inserted/updated quiz for course_id={course_id}, lecture_id={lecture_id}, assessment_id={new_id}"
                    )
                else:
                    # If nothing is returned (unlikely if the table is set up properly),
                    # handle it accordingly:
                    new_id = None
                    logging.warning(
                        f"No row returned after insert/update for course_id={course_id}, lecture_id={lecture_id}"
                    )

                self.conn.commit()
        except Exception as e:
            logging.error(f"Error inserting quiz: {e}")
            raise


    def close(self):
        """
        Closes the database cursor and connection.
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logging.info("Database connection closed")
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")
