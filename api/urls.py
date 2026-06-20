from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='api-register'),
    path('login/', views.login_view, name='api-login'),
    path('logout/', views.logout_view, name='api-logout'),
    path('courses/', views.courses_view, name='api-courses'),
    path('courses/<int:course_id>/start/', views.start_course_view, name='api-start-course'),
    path('dashboard/', views.dashboard_view, name='api-dashboard'),
    path('tasks/', views.tasks_view, name='api-tasks'),
    path('tasks/create/', views.create_task_view, name='api-create-task'),
    path('tasks/<int:task_id>/update/', views.update_task_view, name='api-update-task'),
    path('tasks/<int:task_id>/delete/', views.delete_task_view, name='api-delete-task'),
    path('user-courses/', views.user_courses_view, name='api-user-courses'),
]
