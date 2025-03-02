# recommendation/services.py

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from recommendation.models import Enrollment

def get_recommendations_for_user(user_id, top_n=5, rating_threshold=2.5):
    """
    Build a user-based collaborative filtering system to recommend courses for a given user_id.
    
    Parameters:
      - user_id: The identifier of the target user.
      - top_n: The maximum number of recommendations to return.
      - rating_threshold: The minimum final rating value to consider a course as "highly rated".
      
    Returns:
      - A list of recommended course IDs (strings). If the user has no enrollment data,
        an empty list is returned.
    """
    # 1. Query all enrollments using Django ORM
    enrollments = Enrollment.objects.all()
    if not enrollments.exists():
        return []

    # 2. Convert query results to a DataFrame
    data = []
    for e in enrollments:
        data.append({
            'user_id': str(e.user_id),
            'course_id': str(e.course_id),
            'progress': e.progress if e.progress else 0.0,
            'course_rating': e.course_rating if e.course_rating else 0.0,
            'student_score': e.student_score if e.student_score else 0.0
        })
    df = pd.DataFrame(data)

    # Quick check: if the target user is not in the data, return empty list
    if str(user_id) not in df['user_id'].unique():
        return []

    # 3. Preprocessing: normalize values and compute final rating
    # Assuming max quiz score = 50, max progress = 100, rating scale = 1-5
    df['normalized_student_score'] = df['student_score'] / 50.0
    df['normalized_progress'] = df['progress'] / 100.0

    df['final_rating'] = (0.5 * df['course_rating'] +
                          0.3 * df['normalized_student_score'] +
                          0.2 * df['normalized_progress'])

    # 4. Create a user-course matrix
    user_course_matrix = df.pivot_table(
        index='user_id',
        columns='course_id',
        values='final_rating',
        aggfunc='mean'
    ).fillna(0)

    # 5. Compute cosine similarity between users
    user_matrix = user_course_matrix.values
    user_similarity = cosine_similarity(user_matrix)
    user_similarity_df = pd.DataFrame(
        user_similarity,
        index=user_course_matrix.index,
        columns=user_course_matrix.index
    )

    # 6. Identify top similar users (excluding the target user)
    target_user = str(user_id)
    sim_scores = user_similarity_df.loc[target_user]
    sim_scores = sim_scores.drop(target_user)
    sim_scores = sim_scores.sort_values(ascending=False)
    top_sim_users = sim_scores.head(3).index  # Top 3 similar users

    # 7. Retrieve courses that the target user has already rated
    target_user_ratings = user_course_matrix.loc[target_user]

    # 8. Collect recommended courses from similar users (only courses target user hasn't taken)
    recommended_courses = []
    for sim_user in top_sim_users:
        sim_user_ratings = user_course_matrix.loc[sim_user]
        high_rated = sim_user_ratings[(sim_user_ratings > rating_threshold) & (target_user_ratings == 0)]
        recommended_courses.extend(high_rated.index.tolist())

    # Remove duplicates and limit to top_n recommendations
    final_recommendations = list(set(recommended_courses))[:top_n]

    return final_recommendations
