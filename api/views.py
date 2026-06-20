import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from datetime import date
from django.views.decorators.csrf import csrf_exempt

from .models import Course, Task, UserCourse


def _json_error(message, status=400):
    return JsonResponse({'success': False, 'error': message}, status=status)


def _due_label(due_date):
    if not due_date:
        return ''

    today = timezone.localdate()
    days_left = (due_date - today).days

    if days_left < 0:
        overdue_days = abs(days_left)
        return f'Overdue by {overdue_days} day{"s" if overdue_days != 1 else ""}'
    if days_left == 0:
        return 'Due today'
    if days_left == 1:
        return 'Due tomorrow'
    return f'Due in {days_left} days'


def _is_due_urgent(due_date):
    if not due_date:
        return False

    return (due_date - timezone.localdate()).days <= 1


def _serialize_task(task):
    task_data = {
        'id': task.id,
        'tag': task.tag,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'dueUrgent': _is_due_urgent(task.due_date),
        'progress': task.progress if task.status == 'doing' else None,
        'attachments': task.attachments_count if task.attachments_count > 0 else None,
    }

    if task.due_date:
        task_data['due'] = task.due_date.strftime('%b %d')
        task_data['dueDate'] = task.due_date.isoformat()
        task_data['dueLabel'] = _due_label(task.due_date)

    if task.status == 'doing':
        task_data['active'] = True

    return task_data


def _serialize_deadline(task):
    return {
        'id': task.id,
        'tag': task.tag,
        'title': task.title,
        'status': task.status,
        'dueDate': task.due_date.isoformat() if task.due_date else None,
        'dueLabel': _due_label(task.due_date),
        'urgent': _is_due_urgent(task.due_date),
    }


@csrf_exempt
def register_view(request):
    if request.method != 'POST':
        return _json_error('Method not allowed', status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error('Invalid JSON payload')

    full_name = data.get('fullName', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirmPassword', '')

    if not full_name or not email or not password or not confirm_password:
        return _json_error('All fields are required')
    if password != confirm_password:
        return _json_error('Passwords do not match')
    if User.objects.filter(email=email).exists():
        return _json_error('Email is already registered')

    username = email
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=full_name,
    )

    return JsonResponse({'success': True, 'message': 'User created successfully'})


def _authenticate_by_email_or_username(request, identifier, password):
    user = authenticate(request, username=identifier, password=password)
    if user is not None:
        return user

    try:
        existing_user = User.objects.get(email__iexact=identifier)
    except User.DoesNotExist:
        return None

    return authenticate(request, username=existing_user.username, password=password)


@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return _json_error('Method not allowed', status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error('Invalid JSON payload')

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return _json_error('Email and password are required')

    user = _authenticate_by_email_or_username(request, email, password)
    if user is None:
        return _json_error('Invalid email or password', status=401)

    login(request, user)
    return JsonResponse({'success': True, 'message': 'Login successful'})


@csrf_exempt
def logout_view(request):
    if request.method != 'POST':
        return _json_error('Method not allowed', status=405)

    logout(request)
    return JsonResponse({'success': True, 'message': 'Logout successful'})


def courses_view(request):
    if request.method == 'GET':
        search_query = request.GET.get('search', '').strip()
        courses = Course.objects.all()
        
        if search_query:
            courses = courses.filter(title__icontains=search_query) | courses.filter(description__icontains=search_query) | courses.filter(category__icontains=search_query)
        
        courses_data = list(courses.values('id', 'title', 'category', 'img', 'description'))
        return JsonResponse({'success': True, 'courses': courses_data})
    
    return _json_error('Method not allowed', status=405)


def dashboard_view(request):
    if request.method != 'GET':
        return _json_error('Method not allowed', status=405)

    if not request.user.is_authenticated:
        return _json_error('Unauthorized', status=401)

    # Current user courses
    user_courses = UserCourse.objects.filter(user=request.user).select_related('course')
    courses_data = []
    for uc in user_courses[:3]:
        courses_data.append({
            'category': uc.course.category,
            'title': uc.course.title,
            'current': uc.current_section,
            'total': uc.total_sections,
            'imageUrl': uc.course.img,
        })

    # Task stats
    task_count = Task.objects.filter(user=request.user, status='todo').count()
    completed_tasks = Task.objects.filter(user=request.user, status='done').count()
    total_tasks = Task.objects.filter(user=request.user).count()
    completion_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    deadlines = Task.objects.filter(
        user=request.user,
        due_date__isnull=False,
    ).exclude(status='done').order_by('due_date', 'created_at')[:5]

    return JsonResponse({
        'success': True,
        'data': {
            'name': request.user.first_name or request.user.username,
            'taskCount': task_count,
            'dailyCompletion': {
                'percent': completion_percent,
                'reached': completed_tasks,
                'total': total_tasks,
            },
            'courses': courses_data,
            'deadlines': [_serialize_deadline(task) for task in deadlines],
            'weeklyActivity': {
                'totalHours': 23.5,
                'growthPercent': 12,
            },
        },
    })


def tasks_view(request):
    if request.method != 'GET':
        return _json_error('Method not allowed', status=405)

    if not request.user.is_authenticated:
        return _json_error('Unauthorized', status=401)

    tasks = Task.objects.filter(user=request.user).order_by('-created_at')

    tasks_by_status = {'todo': [], 'doing': [], 'done': []}
    for task in tasks:
        tasks_by_status[task.status].append(_serialize_task(task))

    return JsonResponse({
        'success': True,
        'tasks': tasks_by_status,
    })


def user_courses_view(request):
    if request.method != 'GET':
        return _json_error('Method not allowed', status=405)

    if not request.user.is_authenticated:
        return _json_error('Unauthorized', status=401)

    user_courses = UserCourse.objects.filter(user=request.user).select_related('course')
    courses_data = []

    for uc in user_courses:
        courses_data.append({
            'category': uc.course.category,
            'title': uc.course.title,
            'description': uc.course.description,
            'progress': uc.progress,
            'status': uc.status,
            'imageUrl': uc.course.img,
        })

    return JsonResponse({
        'success': True,
        'courses': courses_data,
    })


@csrf_exempt
def create_task_view(request):
    if request.method != 'POST':
        return _json_error('Method not allowed', status=405)

    if not request.user.is_authenticated:
        return _json_error('Unauthorized', status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error('Invalid JSON payload')

    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    tag = data.get('tag', 'RESEARCH')
    status = data.get('status', 'todo')
    progress = data.get('progress', 0)
    attachments_count = data.get('attachments_count', 0)
    due_date_str = data.get('due_date') or None
    due_date = date.fromisoformat(due_date_str) if due_date_str else None

    if not title:
        return _json_error('Task title is required')

    task = Task.objects.create(
        user=request.user,
        title=title,
        description=description,
        tag=tag,
        status=status,
        progress=progress,
        attachments_count=attachments_count,
        due_date=due_date,
    )

    return JsonResponse({
        'success': True,
        'task': _serialize_task(task),
    })


@csrf_exempt
def update_task_view(request, task_id):
    if request.method != 'PATCH':
        return _json_error('Method not allowed', status=405)

    if not request.user.is_authenticated:
        return _json_error('Unauthorized', status=401)

    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        return _json_error('Task not found', status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error('Invalid JSON payload')

    if 'status' in data:
        task.status = data['status']
    if 'progress' in data:
        task.progress = data['progress']
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'tag' in data:
        task.tag = data['tag']
    if 'attachments_count' in data:
        task.attachments_count = data['attachments_count']
    if 'due_date' in data:
        raw = data['due_date'] or None
        task.due_date = date.fromisoformat(raw) if raw else None

    task.save()

    return JsonResponse({
        'success': True,
        'task': _serialize_task(task),
    })


@csrf_exempt
def delete_task_view(request, task_id):
    if request.method != 'DELETE':
        return _json_error('Method not allowed', status=405)

    if not request.user.is_authenticated:
        return _json_error('Unauthorized', status=401)

    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        return _json_error('Task not found', status=404)

    if task.status == 'done':
        return _json_error('Completed tasks cannot be deleted from this board', status=400)

    task.delete()
    return JsonResponse({'success': True})


@csrf_exempt
def start_course_view(request, course_id):
    if request.method != 'POST':
        return _json_error('Method not allowed', status=405)

    if not request.user.is_authenticated:
        return _json_error('Unauthorized', status=401)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return _json_error('Course not found', status=404)

    user_course, created = UserCourse.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'status': 'in-progress', 'progress': 0}
    )

    return JsonResponse({
        'success': True,
        'message': 'Learning started' if created else 'Already enrolled in this course',
        'userCourse': {
            'id': user_course.id,
            'title': course.title,
            'category': course.category,
            'description': course.description,
            'progress': user_course.progress,
            'status': user_course.status,
            'imageUrl': course.img,
        }
    })
