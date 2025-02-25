import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def main():
    df = pd.read_csv("C:\\Users\\HARSH DADIYA\\Downloads\\enrollments (1).csv")

    def load_and_preprocess(df):
        print(f"Total number of users: {df['user_id'].nunique()}")
        print(f"Total number of courses: {df['course_id'].nunique()}")
        print(f"Total number of records: {len(df)}")

        # Normalize quiz scores and progress (0-1 scale)
        df['normalized_student_score'] = df['student_score'] / 50  # Assuming quiz scores are out of 50
        df['normalized_progress'] = df['progress'] / 100  # Assuming progress is out of 100

        # Calculate final rating
        df['final_rating'] = (0.5 * df['course_rating'] + 
                              0.3 * df['normalized_student_score'] + 
                              0.2 * df['normalized_progress'])

        # Create user-course matrix
        user_course_matrix = df.pivot_table(
            index='user_id',
            columns='course_id',
            values='final_rating',
            aggfunc='mean'
        ).fillna(0)

        print(f"\nUser-Course Matrix Shape: {user_course_matrix.shape}")
        print(f"Number of non-zero ratings: {(user_course_matrix != 0).sum().sum()}")
        
        return user_course_matrix, df

    def evaluate_quiz_performance(df, user_id):
        """Identify if user has low quiz scores (<40%)"""
        low_score_courses = df[(df['user_id'] == user_id) & (df['student_score'] < 20)]['course_id'].tolist()  # 40% of 50
        return low_score_courses

    def cf_recommend_courses(target_user_id, user_similarity_df, user_course_matrix, df, rating_threshold=3.5, top_n=5):
        target_user_id = int(target_user_id)
        if target_user_id not in user_similarity_df.index:
            print(f"User {target_user_id} not found in CF matrix")
            return []
        
        # Step 1: Show Similar Users
        sim_scores = user_similarity_df.loc[target_user_id]
        similar_users = sim_scores.drop(target_user_id).sort_values(ascending=False)
        top_sim_users = similar_users.head(3).index

        print(f"\nTop 3 similar users for user {target_user_id}:")
        print(similar_users.head(3))

        target_user_courses = user_course_matrix.loc[target_user_id]

        print(f"\nCourses taken by user {target_user_id}:")
        print(target_user_courses[target_user_courses > 0])

        # Step 2: Check Low Quiz Scores (Remedial Courses)
        remedial_courses = evaluate_quiz_performance(df, target_user_id)
        if remedial_courses:
            print(f"User {target_user_id} has low scores in courses: {remedial_courses}")
            print("Recommending remedial courses...")

        # Step 3: Recommend High-Rated Courses by Similar Users
        recommended_courses = []
        for sim_user in top_sim_users:
            sim_user_ratings = user_course_matrix.loc[sim_user]
            high_rated = sim_user_ratings[(sim_user_ratings > rating_threshold) & (target_user_courses == 0)]
            
            print(f"\nHighly rated courses by similar user {sim_user}:")
            print(high_rated)
            
            recommended_courses.extend(high_rated.index.tolist())

        # Merge Remedial Courses + Recommended Courses (Avoid Duplicates)
        final_recommendations = list(set(remedial_courses + recommended_courses))[:top_n]

        print(f"\nFinal recommendations for User {target_user_id}: {final_recommendations}")
        return final_recommendations

    def test_recommendation_system(df, test_user_id):
        user_course_matrix, df = load_and_preprocess(df)
        user_matrix = user_course_matrix.values
        user_similarity = cosine_similarity(user_matrix)
        user_similarity_df = pd.DataFrame(user_similarity, index=user_course_matrix.index, columns=user_course_matrix.index)

        recommendations = cf_recommend_courses(
            test_user_id, user_similarity_df, user_course_matrix, df, rating_threshold=2.5, top_n=5
        )
        return recommendations
    
    recommendations = test_recommendation_system(df, test_user_id=2)

if __name__ == "__main__":
    main()
