import uuid
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.Enum('Admin', 'Student', 'Instructor', name='role_enum'), nullable=False)

class Course(db.Model):
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructor_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('user.id'))
    price = db.Column(db.Numeric, nullable=False)
    image = db.Column(db.String)
    category = db.Column(db.String)

class LearningPath(db.Model):
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('course.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)

class QuizScore(db.Model):
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    ai_assessment_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('ai_assessment.id'), nullable=False)
    score = db.Column(db.Numeric, nullable=False)
    quiz_date = db.Column(db.DateTime, nullable=False)

class AI_Assessment(db.Model):
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('course.id'), nullable=False)
    content = db.Column(db.JSON, nullable=False)
