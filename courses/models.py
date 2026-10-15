from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import F, Q

class Course(models.Model):
    """Academic Course model with seat capacity controls."""
    course_code = models.CharField(max_length=20, unique=True, db_index=True)
    course_title = models.CharField(max_length=150)
    description = models.TextField()
    instructor = models.CharField(max_length=100)
    department = models.CharField(max_length=80, default='Computer Science')
    credits = models.PositiveIntegerField(default=3)
    max_seats = models.PositiveIntegerField(default=30)
    available_seats = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['course_code']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        constraints = [
            models.CheckConstraint(
                check=Q(available_seats__gte=0) & Q(available_seats__lte=F('max_seats')),
                name='valid_seat_capacity'
            )
        ]

    def __str__(self):
        return f"{self.course_code}: {self.course_title}"

    @property
    def enrolled_count(self):
        return max(0, self.max_seats - self.available_seats)

    @property
    def is_full(self):
        return self.available_seats <= 0

    @property
    def progress_pct(self):
        if self.max_seats <= 0:
            return 100
        return int((self.enrolled_count / self.max_seats) * 100)

    def clean(self):
        if self.max_seats <= 0:
            raise ValidationError({'max_seats': 'Maximum capacity must be greater than zero.'})
        if self.available_seats is not None and self.max_seats is not None:
            if self.available_seats > self.max_seats:
                raise ValidationError('Available seats cannot exceed maximum capacity.')

class Enrollment(models.Model):
    """Enrollment junction entity connecting Student and Course."""
    STATUS_CHOICES = (
        ('enrolled', 'Enrolled'),
        ('cancelled', 'Cancelled'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')

    class Meta:
        db_table = 'enrollments'
        ordering = ['-enrollment_date']
        unique_together = ('student', 'course')
        verbose_name = 'Course Enrollment'
        verbose_name_plural = 'Course Enrollments'

    def __str__(self):
        return f"{self.student.username} -> {self.course.course_code} ({self.status})"
