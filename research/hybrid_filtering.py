import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def load_and_preprocess(df):
    """
    Preprocess the data:
      - Print basic diagnostics (number of users, courses, ratings)
      - Create a user-course rating matrix
      - Build a course DataFrame with course descriptions and compute TF-IDF matrix
    """
    print(f"Total number of users: {df['user_id'].nunique()}")
    print(f"Total number of courses: {df['course_id'].nunique()}")
    print(f"Total number of ratings: {len(df)}")
    
    # Create user-course rating matrix (collaborative filtering input)
    user_course_matrix = df.pivot_table(
        index='user_id',
        columns='course_id',
        values='course_rating',
        aggfunc='mean'
    ).fillna(0)
    
    print(f"\nUser-Course Matrix Shape: {user_course_matrix.shape}")
    print(f"Number of non-zero ratings: {(user_course_matrix != 0).sum().sum()}")
    
    # Build a course DataFrame with descriptions (content-based filtering input)
    if 'course_description' not in df.columns:
        raise ValueError("The input dataframe must include a 'course_description' column for content-based filtering.")
    
    course_df = df[['course_id', 'course_description']].drop_duplicates().set_index('course_id')
    
    # Compute TF-IDF matrix on the course descriptions
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(course_df['course_description'])
    
    return user_course_matrix, course_df, tfidf_matrix

def cf_recommend_courses(target_user_id, user_similarity_df, user_course_matrix, rating_threshold=3.5, top_n=5):
    """
    Collaborative Filtering (CF) recommendation:
      - Identify similar users using cosine similarity on rating vectors
      - Recommend courses that similar users rated highly but the target user hasn't taken
    """
    target_user_id = int(target_user_id)
    if target_user_id not in user_similarity_df.index:
        print(f"User {target_user_id} not found in CF matrix")
        return []
    
    # Get similarity scores for the target user
    sim_scores = user_similarity_df.loc[target_user_id]
    similar_users = sim_scores.drop(target_user_id).sort_values(ascending=False)
    print(f"\nTop 3 similar users for user {target_user_id} (CF):")
    print(similar_users.head(3))
    
    top_sim_users = similar_users.head(3).index
    target_user_courses = user_course_matrix.loc[target_user_id]
    
    # Check if user has taken all courses
    if (target_user_courses > 0).all():
        print("\nUser has taken all available courses!")
        low_rated_courses = target_user_courses[target_user_courses < rating_threshold].index
        recommended_courses = []
        for sim_user in top_sim_users:
            sim_user_ratings = user_course_matrix.loc[sim_user]
            for course in low_rated_courses:
                if sim_user_ratings[course] > rating_threshold:
                    recommended_courses.append(course)
        if recommended_courses:
            final_recommendations = list(set(recommended_courses))[:top_n]
            print(f"CF Retake Recommendations: {final_recommendations}")
            return final_recommendations
        else:
            print("No CF retake recommendations found")
            return []
    
    # Recommend courses not yet taken by the target user
    recommended_courses = []
    for sim_user in top_sim_users:
        sim_user_ratings = user_course_matrix.loc[sim_user]
        high_rated = sim_user_ratings[(sim_user_ratings > rating_threshold) & (target_user_courses == 0)]
        print(f"\nHighly rated courses by similar user {sim_user} (CF):")
        print(high_rated)
        recommended_courses.extend(high_rated.index.tolist())
    
    final_recommendations = list(set(recommended_courses))[:top_n]
    print(f"\nFinal CF Recommendations: {final_recommendations}")
    return final_recommendations

def cb_recommend_courses(target_user_id, user_course_matrix, course_df, tfidf_matrix, rating_threshold=3.5, top_n=5):
    """
    Content-Based (CB) recommendation:
      - Identify courses that the target user rated highly.
      - Compute an average TF-IDF vector for these liked courses.
      - Recommend courses with similar content that the user has not taken.
    """
    target_user_id = int(target_user_id)
    target_user_ratings = user_course_matrix.loc[target_user_id]
    
    # Identify courses the user liked (rated above threshold)
    liked_courses = target_user_ratings[target_user_ratings >= rating_threshold].index.tolist()
    print(f"\nUser {target_user_id} liked courses (CB): {liked_courses}")
    
    if not liked_courses:
        print("No liked courses found for content-based recommendations.")
        return []
    
    # Get indices of liked courses in the course_df/TF-IDF matrix
    liked_indices = []
    for course in liked_courses:
        if course in course_df.index:
            liked_indices.append(course_df.index.get_loc(course))
    
    if not liked_indices:
        print("No liked course descriptions available.")
        return []
    
    # Compute the average TF-IDF vector for liked courses
    liked_tfidf_vectors = tfidf_matrix[liked_indices]
    avg_vector = liked_tfidf_vectors.mean(axis=0)
    
    # Compute cosine similarity between the average vector and all course descriptions
    sim_scores = cosine_similarity(avg_vector, tfidf_matrix)[0]
    
    # Build a series with course IDs and similarity scores
    sim_series = pd.Series(sim_scores, index=course_df.index)
    
    # Exclude courses already taken by the user
    taken_courses = target_user_ratings[target_user_ratings > 0].index
    sim_series = sim_series.drop(taken_courses, errors='ignore')
    
    # Sort and pick top_n recommendations
    cb_recommendations = sim_series.sort_values(ascending=False).head(top_n).index.tolist()
    print(f"\nContent-Based Recommendations for user {target_user_id}: {cb_recommendations}")
    return cb_recommendations

def combine_recommendations(cf_recs, cb_recs, top_n=5):
    """
    Combine CF and CB recommendations:
      - Simple union of both recommendation lists.
      - Optionally, duplicates can be prioritized.
    """
    combined = list(dict.fromkeys(cf_recs + cb_recs))  # preserves order and removes duplicates
    return combined[:top_n]

def test_recommendation_system(df, test_user_id):
    """
    Test the hybrid recommendation system:
      - Preprocess the data
      - Compute user similarity for CF
      - Generate CF and CB recommendations and then combine them
    """
    # Preprocess data
    user_course_matrix, course_df, tfidf_matrix = load_and_preprocess(df)
    
    # Compute user similarity matrix for CF
    user_matrix = user_course_matrix.values
    user_similarity = cosine_similarity(user_matrix)
    user_similarity_df = pd.DataFrame(
        user_similarity,
        index=user_course_matrix.index,
        columns=user_course_matrix.index
    )
    
    # Get recommendations from both methods
    cf_recs = cf_recommend_courses(
        test_user_id,
        user_similarity_df,
        user_course_matrix,
        rating_threshold=3.5,
        top_n=5
    )
    
    cb_recs = cb_recommend_courses(
        test_user_id,
        user_course_matrix,
        course_df,
        tfidf_matrix,
        rating_threshold=3.5,
        top_n=5
    )
    
    # Combine the recommendations
    hybrid_recs = combine_recommendations(cf_recs, cb_recs, top_n=5)
    print(f"\nHybrid (Combined) Recommendations for user {test_user_id}: {hybrid_recs}")
    return hybrid_recs

def main() -> None:
    # Update the file path as needed
    df = pd.read_csv("C:\\Users\\HARSH DADIYA\\Downloads\\enrollments.csv")
    
    # Test the hybrid recommendation system on a sample user_id (e.g., 25)
    recommendations = test_recommendation_system(df, test_user_id=25)
    
if __name__ == "__main__":
    main()
