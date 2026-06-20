from django.core.management.base import BaseCommand
from api.models import Course


class Command(BaseCommand):
    help = 'Seed course data into the database'

    def handle(self, *args, **options):
        courses = [
            {
                'title': 'Algorithms & Complexity',
                'category': 'Computer Science',
                'img': 'https://picsum.photos/id/1015/600/380',
                'description': 'Master algorithm design, complexity analysis, and advanced problem-solving techniques.',
            },
            {
                'title': 'Philosophy of Mind',
                'category': 'Humanities',
                'img': 'https://picsum.photos/id/201/600/380',
                'description': 'Explore consciousness, cognition, and the relationship between mind and world.',
            },
            {
                'title': 'Gene Editing Ethics',
                'category': 'Biotechnology',
                'img': 'https://picsum.photos/id/237/600/380',
                'description': 'Understand CRISPR, bioethics, and real-world implications of modern gene editing.',
            },
        ]

        Course.objects.all().delete()

        for course_data in courses:
            Course.objects.create(**course_data)

        self.stdout.write(self.style.SUCCESS('Seeded course data successfully.'))
