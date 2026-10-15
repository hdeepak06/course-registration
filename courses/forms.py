from django import forms
from django.core.exceptions import ValidationError
from .models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_code', 'course_title', 'department', 'instructor', 'credits', 'max_seats', 'description']
        widgets = {
            'course_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS101', 'id': 'courseCode', 'style': 'text-transform: uppercase;'}),
            'course_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Introduction to Computer Science', 'id': 'courseTitle'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science', 'id': 'courseDept', 'list': 'departmentList'}),
            'instructor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dr. Alan Turing', 'id': 'courseInstructor'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10, 'id': 'courseCredits'}),
            'max_seats': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 500, 'id': 'maxSeats'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Provide a detailed overview of topics covered...', 'id': 'courseDesc'}),
        }

    def clean_course_code(self):
        code = self.cleaned_data.get('course_code', '').strip().upper()
        if len(code) < 2:
            raise ValidationError("Course code must be at least 2 characters long.")
        qs = Course.objects.filter(course_code__iexact=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Course code '{code}' is already registered.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        new_max = cleaned_data.get('max_seats')
        if new_max:
            if not self.instance.pk:
                self.instance.available_seats = new_max
            else:
                occupied = self.instance.enrolled_count
                if new_max < occupied:
                    self.add_error('max_seats', f"Maximum seats cannot be lower than currently enrolled students ({occupied}).")
                else:
                    self.instance.available_seats = max(0, new_max - occupied)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk:
            # New course: available_seats begins at max_seats
            instance.available_seats = instance.max_seats
        else:
            # Existing course: adjust available_seats based on new max_seats and existing enrollments
            occupied = instance.max_seats - instance.available_seats
            instance.available_seats = max(0, instance.max_seats - occupied)
        if commit:
            instance.save()
        return instance
