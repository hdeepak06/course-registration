from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class StudentProfile(models.Model):
    """Profile model extending Django's built-in User model."""
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('administrator', 'Administrator'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_profiles'
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'administrator' or self.user.is_superuser or self.user.is_staff

@receiver(post_save, sender=User)
def create_or_update_student_profile(sender, instance, created, **kwargs):
    """Automatically create or update StudentProfile upon User creation."""
    if created:
        role = 'administrator' if instance.is_superuser or instance.is_staff else 'student'
        StudentProfile.objects.create(user=instance, role=role)
    else:
        if hasattr(instance, 'student_profile'):
            instance.student_profile.save()
