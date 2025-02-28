# recommendation/models.py

import uuid
from sqlalchemy.dialects.postgresql import UUID
from recommendation.database import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = db.Column(db.String)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String)
    role = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    avatar = db.Column(db.String)

    # Example relationship (if needed)
    # enrollments = db.relationship('Enrollment', backref='user', lazy=True)


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String)
    description = db.Column(db.Text)
    instructor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('categories.id'))
    price = db.Column(db.Float)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    banner_image = db.Column(db.String)
    welcome_msg = db.Column(db.String)
    intro_video = db.Column(db.String)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String)


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'))
    enrolled_at = db.Column(db.DateTime)
    progress = db.Column(db.Float)         # e.g., 0 - 100
    course_rating = db.Column(db.Float)    # e.g., 1 - 5
    review_text = db.Column(db.Text)
    liked = db.Column(db.Boolean)
    share_count = db.Column(db.Integer)
    student_score = db.Column(db.Float)    # e.g., quiz score
    updated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)


class Assessment(db.Model):
    __tablename__ = 'assessments'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'))
    assessment_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime)


class Lecture(db.Model):
    __tablename__ = 'lectures'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'))
    title = db.Column(db.String)
    description = db.Column(db.Text)
    video_path = db.Column(db.String)
    pdf_path = db.Column(db.String)
    created_at = db.Column(db.DateTime)
