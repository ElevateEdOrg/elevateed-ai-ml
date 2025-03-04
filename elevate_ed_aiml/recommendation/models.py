from django.db import models

# Create your models here.
# recommendation/models.py

import uuid
from django.db import models

class User(models.Model):
    """
    Represents a user in the system.
    
    Fields:
      - id: UUID primary key.
      - full_name: The user's full name.
      - email: The user's email address (unique).
      - password: The user's password (store securely in production).
      - role: The user's role (e.g., student, instructor).
      - created_at: Timestamp of creation.
      - avatar: Path or URL to the user's avatar image.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    avatar = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.full_name or self.email

class Category(models.Model):
    """
    Represents a course category.
    
    Fields:
      - id: UUID primary key.
      - name: Name of the category.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Course(models.Model):
    """
    Represents a course in the system.
    
    Fields:
      - id: UUID primary key.
      - title: Title of the course.
      - description: Detailed description of the course.
      - instructor: ForeignKey to the User model.
      - category: ForeignKey to the Category model.
      - price: Course price.
      - created_at: Timestamp when the course was created.
      - updated_at: Timestamp when the course was last updated.
      - banner_image: Path or URL to the course banner image.
      - welcome_msg: Welcome message for the course.
      - intro_video: Path or URL to the introductory video.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    banner_image = models.CharField(max_length=255, blank=True, null=True)
    welcome_msg = models.CharField(max_length=255, blank=True, null=True)
    intro_video = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

class Enrollment(models.Model):
    """
    Represents an enrollment of a user in a course.
    
    Fields:
      - id: UUID primary key.
      - user: ForeignKey to User.
      - course: ForeignKey to Course.
      - enrolled_at: Timestamp when enrolled.
      - progress: Course progress (0 to 100).
      - course_rating: Rating given to the course (e.g., 1 to 5).
      - review_text: Optional review text.
      - liked: Boolean flag indicating if the course was liked.
      - share_count: Number of shares.
      - student_score: Quiz score or similar metric.
      - updated_at: Timestamp when record was last updated.
      - created_at: Timestamp when the record was created.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(blank=True, null=True)
    progress = models.FloatField(default=0.0)
    course_rating = models.FloatField(default=0.0)
    review_text = models.TextField(blank=True, null=True)
    liked = models.BooleanField(default=False)
    share_count = models.IntegerField(default=0)
    student_score = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} enrolled in {self.course}"


class Lecture(models.Model):
    """
    Represents a lecture in a course.
    
    Fields:
      - id: UUID primary key.
      - course: ForeignKey to Course.
      - title: Lecture title.
      - description: Description of the lecture.
      - video_path: Path or URL to the lecture video.
      - pdf_path: Optional path or URL to supplementary PDF.
      - created_at: Timestamp when the lecture was created.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lectures')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video_path = models.CharField(max_length=255, blank=True, null=True)
    pdf_path = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Assessment(models.Model):
    """
    Represents an assessment (quiz) for a course.
    
    Fields:
      - id: UUID primary key.
      - course: ForeignKey to Course.
      - assessment_data: JSON data containing the quiz details.
      - created_at: Timestamp when the assessment was created.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    assessment_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    lecture_id = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='assessments')


    def __str__(self):
        return f"Assessment for {self.course.title}"

