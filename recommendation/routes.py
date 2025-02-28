# recommendation/routes.py

from flask import Blueprint, jsonify
from flasgger.utils import swag_from
from recommendation.services import get_recommendations_for_user

recommendation_blueprint = Blueprint('recommendation', __name__)

@recommendation_blueprint.route('/recommendations/<uuid:user_id>', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Return recommended course IDs for the user',
            'examples': {
                'application/json': {
                    'user_id': 'uuid-string',
                    'recommendations': ['course-uuid-1', 'course-uuid-2']
                }
            }
        }
    },
    'parameters': [
        {
            'name': 'user_id',
            'in': 'path',
            'type': 'string',
            'format': 'uuid',
            'required': True,
            'description': 'UUID of the user'
        }
    ],
    'tags': ['Recommendations']
})
def get_recommendations(user_id):
    """
    Get course recommendations for a specific user.

    This endpoint returns a list of course UUIDs that are recommended
    for the given user based on collaborative filtering.

    ---
    produces:
      - "application/json"
    """
    recommendations = get_recommendations_for_user(user_id)
    return jsonify({
        'user_id': str(user_id),
        'recommendations': recommendations
    })
