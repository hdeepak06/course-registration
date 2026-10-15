from django.contrib import admin
from .models import Course, Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_title', 'department', 'instructor', 'credits', 'available_seats', 'max_seats', 'enrolled_count')
    list_filter = ('department', 'credits', 'created_at')
    search_fields = ('course_code', 'course_title', 'instructor', 'description')
    ordering = ('course_code',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course', 'enrollment_date', 'status')
    list_filter = ('status', 'enrollment_date', 'course__department')
    search_fields = ('student__username', 'student__email', 'course__course_code', 'course__course_title')
    ordering = ('-enrollment_date',)
