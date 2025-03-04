from flask import Blueprint, jsonify, request
from flasgger.utils import swag_from
from recommendation.services import get_recommendations_for_user

recommendation_blueprint = Blueprint('recommendation', __name__)

@recommendation_blueprint.route('/recommendations', methods=['GET'])
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
            'in': 'query',
            'type': 'string',
            'format': 'uuid',
            'required': True,
            'description': 'UUID of the user'
        }
    ],
    'tags': ['Recommendations']
})
def get_recommendations():
    """
    Get course recommendations for a specific user.

    This endpoint returns a list of course UUIDs that are recommended
    for the given user based on collaborative filtering.

    ---
    produces:
      - "application/json"
    parameters:
      - name: user_id
        in: query
        type: string
        format: uuid
        required: true
        description: UUID of the user
    """
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    recommendations = get_recommendations_for_user(user_id)
    return jsonify({
        'user_id': user_id,
        'recommendations': recommendations
    })
