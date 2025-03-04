import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from recommendation.models import Enrollment
import logging

logger = logging.getLogger(__name__)

def get_recommendations_for_user(user_id, top_n=5, rating_threshold=2.5):
    """
    Generate course recommendations for a given user using collaborative filtering.
    
    Cold Start & Hybrid Handling:
      - If the target user has no enrollment data, return the top courses based on overall average rating.
      - If collaborative filtering yields no recommendations, fall back to popular courses.
      
    Parameters:
      - user_id: The identifier of the target user.
      - top_n: The maximum number of recommendations to return.
      - rating_threshold: The minimum final rating to consider a course as "highly rated".
      
    Returns:
      - A list of recommended course IDs (strings).
    """
    # 1. Query all enrollments from the database with error handling
    try:
        enrollments = Enrollment.objects.all()
        
        # Debug logging to check if we're getting data
        enrollment_count = enrollments.count()
        logger.info(f"Retrieved {enrollment_count} enrollments from database")
        
        if enrollment_count == 0:
            logger.warning("No enrollments found in database")
            return get_popular_courses(top_n)
    except Exception as e:
        logger.error(f"Error retrieving enrollments: {str(e)}")
        return []
    
    # 2. Convert query results to a DataFrame with error handling
    try:
        data = []
        for e in enrollments:
            # Use getattr to safely get 'student_score' (default to 0.0 if not present)
            record = {
                'user_id': str(e.user_id),
                'course_id': str(e.course_id),
                'progress': e.progress if e.progress is not None else 0.0,
                'course_rating': e.course_rating if e.course_rating is not None else 0.0,
                'student_score': getattr(e, 'student_score', 0.0)
            }
            data.append(record)
        
        df = pd.DataFrame(data)
        
        logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        # 3. If the DataFrame is empty, return popular courses
        if df.empty:
            logger.warning("DataFrame is empty after conversion")
            return get_popular_courses(top_n)
    except Exception as e:
        logger.error(f"Error creating DataFrame: {str(e)}")
        return []
    
    # 4. Ensure the "student_score" column exists even if no record had it
    if 'student_score' not in df.columns:
        df['student_score'] = 0.0
    
    # 5. Preprocessing: Normalize values and compute final rating
    df['normalized_student_score'] = df['student_score'] / 50.0
    df['normalized_progress'] = df['progress'] / 100.0
    df['final_rating'] = (0.5 * df['course_rating'] +
                          0.3 * df['normalized_student_score'] +
                          0.2 * df['normalized_progress'])
    
    target_user = str(user_id)
    logger.info(f"Processing recommendations for user: {target_user}")
    
    # 6. Cold Start Check: If the target user has no enrollment data, return popular courses
    if target_user not in df['user_id'].unique():
        logger.info(f"Cold start: User {target_user} has no enrollment data")
        return get_popular_courses_from_df(df, top_n)
    
    # 7. Create a user-course matrix from the final ratings
    try:
        user_course_matrix = df.pivot_table(
            index='user_id',
            columns='course_id',
            values='final_rating',
            aggfunc='mean'
        ).fillna(0)
        
        logger.info(f"Created user-course matrix with shape: {user_course_matrix.shape}")
    except Exception as e:
        logger.error(f"Error creating user-course matrix: {str(e)}")
        return get_popular_courses_from_df(df, top_n)
    
    # 8. Compute cosine similarity between users
    try:
        user_matrix = user_course_matrix.values
        user_similarity = cosine_similarity(user_matrix)
        user_similarity_df = pd.DataFrame(
            user_similarity,
            index=user_course_matrix.index,
            columns=user_course_matrix.index
        )
    except Exception as e:
        logger.error(f"Error computing user similarity: {str(e)}")
        return get_popular_courses_from_df(df, top_n)
    
    # 9. Identify top similar users (excluding the target user)
    try:
        sim_scores = user_similarity_df.loc[target_user].drop(target_user)
        sim_scores = sim_scores.sort_values(ascending=False)
        
        # Check if we have any similar users
        if len(sim_scores) == 0:
            logger.warning(f"No similar users found for user {target_user}")
            return get_popular_courses_from_df(df, top_n)
            
        # Get top 3 similar users or all if less than 3
        top_n_similar = min(3, len(sim_scores))
        top_sim_users = sim_scores.head(top_n_similar).index
        
        logger.info(f"Found {len(top_sim_users)} similar users for user {target_user}")
    except Exception as e:
        logger.error(f"Error identifying similar users: {str(e)}")
        return get_popular_courses_from_df(df, top_n)
    
    # 10. Retrieve courses that the target user has already rated
    target_user_ratings = user_course_matrix.loc[target_user]
    target_user_courses = set(target_user_ratings[target_user_ratings > 0].index)
    logger.info(f"User {target_user} has taken {len(target_user_courses)} courses")
    
    # 11. Collect recommended courses from similar users (only courses the target user hasn't taken)
    recommended_courses = []
    for sim_user in top_sim_users:
        try:
            sim_user_ratings = user_course_matrix.loc[sim_user]
            # Find courses that similar user rated highly and target user hasn't taken
            high_rated_indices = sim_user_ratings[sim_user_ratings > rating_threshold].index
            high_rated_not_taken = [c for c in high_rated_indices if c not in target_user_courses]
            
            recommended_courses.extend(high_rated_not_taken)
            logger.info(f"Similar user {sim_user} contributed {len(high_rated_not_taken)} recommendations")
        except Exception as e:
            logger.error(f"Error processing similar user {sim_user}: {str(e)}")
            continue
    
    # Remove duplicates and limit to top_n recommendations
    final_recommendations = list(dict.fromkeys(recommended_courses))[:top_n]
    
    # 12. Fallback: If no recommendations were found, use popular courses
    if not final_recommendations:
        logger.info("No collaborative filtering recommendations found, falling back to popular courses")
        final_recommendations = get_popular_courses_from_df(df, top_n)
    
    logger.info(f"Returning {len(final_recommendations)} recommendations for user {target_user}")
    return final_recommendations


def get_popular_courses_from_df(df, top_n=5):
    """
    Get popular courses based on average final rating from an existing DataFrame.
    
    Parameters:
      - df: DataFrame containing course data
      - top_n: Number of popular courses to return
    
    Returns:
      - List of popular course IDs
    """
    try:
        popular_courses = (
            df.groupby('course_id')['final_rating']
              .mean()
              .sort_values(ascending=False)
              .head(top_n)
              .index.tolist()
        )
        logger.info(f"Returning {len(popular_courses)} popular courses")
        return popular_courses
    except Exception as e:
        logger.error(f"Error getting popular courses from DataFrame: {str(e)}")
        return []


def get_popular_courses(top_n=5):
    """
    Get popular courses directly from the database.
    Used as a fallback when no DataFrame is available.
    
    Parameters:
      - top_n: Number of popular courses to return
    
    Returns:
      - List of popular course IDs
    """
    try:
        # Get all enrollments with course ratings
        enrollments_with_ratings = Enrollment.objects.filter(course_rating__isnull=False)
        
        # Create a dictionary to store course ratings
        course_ratings = {}
        
        # Calculate average rating for each course
        for enrollment in enrollments_with_ratings:
            course_id = str(enrollment.course_id)
            rating = enrollment.course_rating or 0.0
            
            if course_id not in course_ratings:
                course_ratings[course_id] = {'total': rating, 'count': 1}
            else:
                course_ratings[course_id]['total'] += rating
                course_ratings[course_id]['count'] += 1
        
        # Calculate average ratings
        average_ratings = {
            course_id: data['total'] / data['count']
            for course_id, data in course_ratings.items()
        }
        
        # Sort courses by average rating and get top N
        popular_courses = sorted(
            average_ratings.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        # Return just the course IDs
        return [course_id for course_id, _ in popular_courses]
    except Exception as e:
        logger.error(f"Error getting popular courses directly from database: {str(e)}")
        return []