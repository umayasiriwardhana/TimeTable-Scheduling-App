from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import Max,Q
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import time


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_lecturer = models.BooleanField(default=False)

    @classmethod
    def generate_username(cls, is_student=False, is_lecturer=False):
        if is_student:
            prefix = 'S'
        elif is_lecturer:
            prefix = 'L'
        else:
            prefix = 'A'
        
        max_id = cls.objects.filter(username__startswith=prefix).aggregate(Max('username'))['username__max']
        
        if max_id:
            try:
                next_id = int(max_id[1:]) + 1
            except ValueError:
                next_id = 1
        else:
            next_id = 1
        
        return f"{prefix}{next_id:05d}"

class Faculty(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Faculties"
    
    def __str__(self):
        return self.name


class Degree(models.Model):
    name = models.CharField(max_length=255)
    Faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"

class BatchYear(models.Model):
    year = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"Batch {self.year}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=255)
    degree = models.ForeignKey(Degree, on_delete=models.SET_NULL, null=True)
    Batch_Year = models.ForeignKey(BatchYear, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.Batch_Year})"

class Lecturer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=255)
    Faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.full_name

class LecturerAvailability(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='availabilities')
    day = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField(default=time(9, 0))  
    end_time = models.TimeField(default=time(17, 0))  

    def clean(self):
        if self.start_time < time(9, 0) or self.end_time > time(17, 0):
            raise ValidationError(_("Start and end times must be between 9:00 AM and 5:00 PM."))
        
        if self.start_time >= self.end_time:
            raise ValidationError(_("End time must be after start time."))

    def __str__(self):
        return f"{self.lecturer} - {self.get_day_display()} {self.start_time}-{self.end_time}"

    class Meta:
        unique_together = ['lecturer', 'day']

@receiver(post_save, sender=Lecturer)
def create_lecturer_availability(sender, instance, created, **kwargs):
    if created:
        for day in range(7):
            LecturerAvailability.objects.create(
                lecturer=instance,
                day=day,
                start_time=time(9, 0),
                end_time=time(17, 0)
            )

class Hall(models.Model):
    HALL_TYPE_CHOICES = [
        ('LECTURE_ROOM', 'Lecture Room'),
        ('LAB', 'Lab'),
    ]
    name = models.CharField(max_length=255)
    Faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=HALL_TYPE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class Course(models.Model):
    name = models.CharField(max_length=255)
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE)
    Batch_Year = models.ForeignKey(BatchYear, on_delete=models.SET_NULL, null=True)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.SET_NULL, null=True)
    required_hall_type = models.CharField(max_length=20, choices=Hall.HALL_TYPE_CHOICES)
    duration = models.PositiveIntegerField() 
    sessions_per_week = models.PositiveIntegerField()


    def __str__(self):
        return f"{self.name} ({self.Batch_Year})"
    

class Timeslot(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    day = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField(default=time(9, 0))
    end_time = models.TimeField(default=time(17, 0))
    hall = models.ForeignKey('Hall', on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)

    def clean(self):
        if self.start_time < time(9, 0) or self.end_time > time(17, 0):
            raise ValidationError(_("Start and end times must be between 9:00 AM and 5:00 PM."))
        
        if self.start_time >= self.end_time:
            raise ValidationError(_("End time must be after start time."))

        if self.hall.type != self.course.required_hall_type:
            raise ValidationError(_("The hall type does not match the course's required hall type."))

        lecturer_availability = LecturerAvailability.objects.filter(
            lecturer=self.course.lecturer,
            day=self.day,
            start_time__lte=self.start_time,
            end_time__gte=self.end_time
        )

        if not lecturer_availability.exists():
            raise ValidationError(_("The lecturer is not available during this timeslot."))

    def __str__(self):
        return f"{self.get_day_display()} ({self.start_time} - {self.end_time}) - {self.course.name} in {self.hall.name}"
    

