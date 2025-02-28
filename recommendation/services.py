import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from database import db
from models import User, QuizScore, Course, LearningPath

def fetch_data():
    """Fetch user-course interactions from DB."""
    query = db.session.execute("""
        SELECT u.id as user_id, c.id as course_id, q.score as student_score 
        FROM User u
        JOIN QuizScore q ON u.id = q.user_id
        JOIN Course c ON q.ai_assessment_id = c.id;
    """)
    df = pd.DataFrame(query.fetchall(), columns=["user_id", "course_id", "student_score"])
    return df

def load_and_preprocess():
    """Prepare the user-course matrix."""
    df = fetch_data()
    df['normalized_student_score'] = df['student_score'] / 100  # Normalize
    user_course_matrix = df.pivot_table(index='user_id', columns='course_id', values='normalized_student_score', aggfunc='mean').fillna(0)
    return user_course_matrix, df

def recommend_courses(user_id, top_n=3):
    """Collaborative filtering for course recommendations."""
    user_course_matrix, df = load_and_preprocess()
    user_matrix = user_course_matrix.values
    user_similarity = cosine_similarity(user_matrix)
    user_similarity_df = pd.DataFrame(user_similarity, index=user_course_matrix.index, columns=user_course_matrix.index)

    if user_id not in user_similarity_df.index:
        return []

    similar_users = user_similarity_df.loc[user_id].drop(user_id).sort_values(ascending=False).head(3).index
    target_user_courses = user_course_matrix.loc[user_id]

    recommended_courses = []
    for sim_user in similar_users:
        sim_user_ratings = user_course_matrix.loc[sim_user]
        high_rated = sim_user_ratings[(sim_user_ratings > 0.7) & (target_user_courses == 0)]
        recommended_courses.extend(high_rated.index.tolist())

    return list(set(recommended_courses))[:top_n]

def update_learning_path(user_id):
    """Update or insert recommendations into LearningPath."""
    top_courses = recommend_courses(user_id, top_n=3)
    
    existing_courses = db.session.query(LearningPath.course_id).filter_by(user_id=user_id).order_by(LearningPath.order).all()
    existing_courses = [c[0] for c in existing_courses]

    if existing_courses:
        for idx, course_id in enumerate(top_courses):
            if idx < len(existing_courses):
                db.session.query(LearningPath).filter_by(user_id=user_id, order=idx + 1).update({"course_id": course_id})
            else:
                db.session.add(LearningPath(user_id=user_id, course_id=course_id, order=idx + 1))
    else:
        for idx, course_id in enumerate(top_courses):
            db.session.add(LearningPath(user_id=user_id, course_id=course_id, order=idx + 1))

    db.session.commit()
