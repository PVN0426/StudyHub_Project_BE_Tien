from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=120)
    img = models.URLField(max_length=500)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class UserCourse(models.Model):
    STATUS_CHOICES = [
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in-progress')
    progress = models.IntegerField(default=0)  # 0-100
    current_section = models.IntegerField(default=0)
    total_sections = models.IntegerField(default=20)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f'{self.user.username} - {self.course.title}'


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('doing', 'Doing'),
        ('done', 'Done'),
    ]

    TAG_CHOICES = [
        ('RESEARCH', 'Research'),
        ('URGENT', 'Urgent'),
        ('CODING', 'Coding'),
        ('WRITING', 'Writing'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.CharField(max_length=20, choices=TAG_CHOICES, default='RESEARCH')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    due_date = models.DateField(null=True, blank=True)
    progress = models.IntegerField(default=0)  # 0-100, for doing status
    attachments_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
