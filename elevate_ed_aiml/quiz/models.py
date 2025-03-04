import uuid
from django.db import models

# ------------------- User Model -------------------
class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    avatar = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.full_name

# ------------------- Category Model -------------------
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# ------------------- Course Model -------------------
class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    price = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    banner_image = models.CharField(max_length=500, blank=True, null=True)
    welcome_msg = models.CharField(max_length=500, blank=True, null=True)
    intro_video = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title

# ------------------- Enrollment Model -------------------
class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress = models.FloatField(default=0.0)  # Percentage from 0 to 100
    course_rating = models.FloatField(null=True, blank=True)  # Rating 1-5
    review_text = models.TextField(blank=True, null=True)
    liked = models.BooleanField(default=False)
    share_count = models.IntegerField(default=0)
    student_score = models.FloatField(null=True, blank=True)  # Quiz Score
    updated_at = models.DateTimeField(auto_now=True)

# ------------------- Lecture Model -------------------
class Lecture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video_path = models.CharField(max_length=500, blank=True, null=True)
    pdf_path = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# ------------------- Assessment Model (Storing Quizzes) -------------------
class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, null=True, blank=True)  # Allow NULL  # ✅ Added lecture_id
    assessment_data = models.JSONField()  # Stores MCQ data in JSON format
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assessment for {self.course.title} - Lecture {self.lecture.title}"
