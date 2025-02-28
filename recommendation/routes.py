from flask import Blueprint, jsonify
from services import recommend_courses, update_learning_path

routes = Blueprint("routes", __name__)

@routes.route("/recommend/<int:user_id>", methods=["GET"])
def get_recommendations(user_id):
    recommendations = recommend_courses(user_id)
    return jsonify({"user_id": user_id, "recommended_courses": recommendations})

@routes.route("/update-learning-path/<int:user_id>", methods=["POST"])
def update_path(user_id):
    update_learning_path(user_id)
    return jsonify({"message": f"Learning path updated for user {user_id}"})
