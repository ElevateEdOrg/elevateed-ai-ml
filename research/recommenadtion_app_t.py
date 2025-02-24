import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def main() -> None:

    df = pd.read_csv("C:\\Users\\HARSH DADIYA\\Downloads\\enrollments.csv")

    def load_and_preprocess(df):
        """
        Preprocesses the data and prints diagnostic information
        """
        print(f"Total number of users: {df['user_id'].nunique()}")
        print(f"Total number of courses: {df['course_id'].nunique()}")
        print(f"Total number of ratings: {len(df)}")
        
        # Create user-course matrix with diagnostic prints
        user_course_matrix = df.pivot_table(
            index='user_id',
            columns='course_id',
            values='course_rating',
            aggfunc='mean'
        ).fillna(0)
        
        print(f"\nUser-Course Matrix Shape: {user_course_matrix.shape}")
        print(f"Number of non-zero ratings: {(user_course_matrix != 0).sum().sum()}")
        
        return user_course_matrix

    # 
    def cf_recommend_courses(target_user_id, user_similarity_df, user_course_matrix, rating_threshold=3.5, top_n=5):
        """
        Modified CF recommendation with handling for users who have taken all courses
        """
        target_user_id = int(target_user_id)
        if target_user_id not in user_similarity_df.index:
            print(f"User {target_user_id} not found in CF matrix")
            return []
        
        # Get similarity scores and print diagnostic info
        sim_scores = user_similarity_df.loc[target_user_id]
        similar_users = sim_scores.drop(target_user_id).sort_values(ascending=False)
        print(f"\nTop 3 similar users for user {target_user_id}:")
        print(similar_users.head(3))
        
        top_sim_users = similar_users.head(3).index
        
        target_user_courses = user_course_matrix.loc[target_user_id]
        
        print(f"\nCourses taken by user {target_user_id}:")
        print(target_user_courses[target_user_courses > 0])
        
        # Check if user has taken all courses
        if (target_user_courses > 0).all():
            print("\nUser has taken all available courses!")
            # Instead of returning nothing, recommend courses they might want to retake
            # based on their low ratings and similar users' high ratings
            low_rated_courses = target_user_courses[target_user_courses < rating_threshold].index
            recommended_courses = []
            
            for sim_user in top_sim_users:
                sim_user_ratings = user_course_matrix.loc[sim_user]
                # Find courses that similar users rated highly but target user rated low
                for course in low_rated_courses:
                    if sim_user_ratings[course] > rating_threshold:
                        recommended_courses.append(course)
            
            if recommended_courses:
                print("\nRecommending courses to retake based on similar users' high ratings:")
                final_recommendations = list(set(recommended_courses))[:top_n]
                print(f"Final recommendations (courses to retake): {final_recommendations}")
                return final_recommendations
            else:
                print("\nNo courses found for retake recommendations")
                return []
        
        recommended_courses = []
        for sim_user in top_sim_users:
            sim_user_ratings = user_course_matrix.loc[sim_user]
            # Find highly rated courses not taken by target user
            high_rated = sim_user_ratings[(sim_user_ratings > rating_threshold) & (target_user_courses == 0)]
            print(f"\nHighly rated courses by similar user {sim_user}:")
            print(high_rated)
            recommended_courses.extend(high_rated.index.tolist())
        
        final_recommendations = list(set(recommended_courses))[:top_n]
        print(f"\nFinal recommendations: {final_recommendations}")
        return final_recommendations

    

    def test_recommendation_system(df, test_user_id):
        """
        Test the recommendation system with detailed diagnostics
        """
        # Preprocess data
        user_course_matrix = load_and_preprocess(df)
        
        # Compute user similarity
        user_matrix = user_course_matrix.values
        user_similarity = cosine_similarity(user_matrix)
        user_similarity_df = pd.DataFrame(
            user_similarity,
            index=user_course_matrix.index,
            columns=user_course_matrix.index
        )
        
        # Get recommendations with lower rating threshold
        recommendations = cf_recommend_courses(
            test_user_id,
            user_similarity_df,
            user_course_matrix,
            rating_threshold=2.5,  # Lower threshold to get more recommendations
            top_n=5
        )
        
        return recommendations
    
    recommendations = test_recommendation_system(df, test_user_id = 25 )

# Example usage:
if __name__ == "__main__":
    main()