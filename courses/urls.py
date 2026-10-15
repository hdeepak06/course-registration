from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Public views
    path('', views.index, name='index'),
    path('courses/', views.explore, name='explore'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.enroll_course, name='enroll'),
    path('courses/<int:course_id>/cancel/', views.cancel_enrollment, name='cancel'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('about/', views.about, name='about'),

    # Admin Portal views
    path('admin-portal/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/courses/', views.admin_manage_courses, name='admin_manage_courses'),
    path('admin-portal/courses/new/', views.admin_course_create, name='admin_course_create'),
    path('admin-portal/courses/<int:course_id>/edit/', views.admin_course_edit, name='admin_course_edit'),
    path('admin-portal/courses/<int:course_id>/delete/', views.admin_course_delete, name='admin_course_delete'),
    path('admin-portal/enrollments/', views.admin_enrollments, name='admin_enrollments'),
]
