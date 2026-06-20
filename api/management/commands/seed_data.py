from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import UserCourse, Task, Course
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Seed user courses and tasks data'

    def handle(self, *args, **options):
        # Get or create a demo user by email so email login works for seeded data
        user = User.objects.filter(email__iexact='test@example.com').first()
        if not user:
            user = User.objects.create_user(
                username='test@example.com',
                email='test@example.com',
                first_name='Alex',
                password='test123',
            )
        elif user.username != 'test@example.com':
            user.username = 'test@example.com'
            user.save()

        # Clear existing data
        UserCourse.objects.filter(user=user).delete()
        Task.objects.filter(user=user).delete()

        # Get courses or create defaults
        courses = Course.objects.all()
        if not courses.exists():
            courses = []
            courses_data = [
                {
                    'title': 'Advanced Calculus II',
                    'category': 'Mathematics',
                    'img': 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=400&q=80',
                    'description': 'Advanced mathematics course',
                },
                {
                    'title': 'Molecular Biology',
                    'category': 'Science',
                    'img': 'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=400&q=80',
                    'description': 'Biology fundamentals',
                },
                {
                    'title': 'Algorithm Design',
                    'category': 'Technology',
                    'img': 'https://images.unsplash.com/photo-1555066931-4365d14431b9?w=400&q=80',
                    'description': 'Learn algorithms',
                },
            ]
            for course_data in courses_data:
                course, _ = Course.objects.get_or_create(
                    title=course_data['title'],
                    defaults={
                        'category': course_data['category'],
                        'img': course_data['img'],
                        'description': course_data['description'],
                    }
                )
                courses.append(course)
        else:
            courses = list(courses[:3])

        # Create UserCourses
        progress_values = [12, 8, 18]
        for i, course in enumerate(courses):
            UserCourse.objects.create(
                user=user,
                course=course,
                status='in-progress',
                progress=progress_values[i] if i < len(progress_values) else 50,
                current_section=progress_values[i] if i < len(progress_values) else 10,
                total_sections=20,
            )

        # Create Tasks
        tasks_data = [
            {
                'tag': 'RESEARCH',
                'title': 'Literature Review: AI Ethics',
                'description': 'Annotate 5 primary sources for the semester thesis.',
                'status': 'todo',
                'due_date': datetime.now().date() + timedelta(days=5),
            },
            {
                'tag': 'URGENT',
                'title': 'Statistics Quiz Prep',
                'description': 'Complete practice modules for Hypothesis Testing.',
                'status': 'todo',
                'due_date': datetime.now().date() + timedelta(days=1),
            },
            {
                'tag': 'CODING',
                'title': 'Database Schema Design',
                'description': 'Design and implement database schema.',
                'status': 'doing',
                'progress': 65,
                'due_date': datetime.now().date() + timedelta(days=9),
            },
            {
                'tag': 'WRITING',
                'title': 'Introduction to Psychology Essay',
                'description': 'Submitted to LMS yesterday.',
                'status': 'done',
            },
        ]

        for task_data in tasks_data:
            progress = task_data.pop('progress', 0)
            Task.objects.create(
                user=user,
                progress=progress,
                **task_data,
            )

        self.stdout.write(self.style.SUCCESS('Seeded user courses and tasks successfully.'))
