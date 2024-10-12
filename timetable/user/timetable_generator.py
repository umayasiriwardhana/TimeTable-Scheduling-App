from django.db import transaction
from datetime import datetime, timedelta,time
from .models import LecturerAvailability,Course,Timeslot,Hall,Lecturer
from django.db import transaction
from django.db.models import Q

def generate_timetable(faculty):
    with transaction.atomic():
        # Clear existing timeslots for the given faculty
        Timeslot.objects.filter(hall__Faculty=faculty).delete()

        # Get all courses for the faculty
        courses = Course.objects.filter(degree__Faculty=faculty)

        # Get all halls for the faculty
        halls = Hall.objects.filter(Faculty=faculty)

        # Get all lecturers for the faculty
        lecturers = Lecturer.objects.filter(Faculty=faculty)

        # Define time slots
        time_slots = [
            (datetime.strptime(f"{h:02d}:00", "%H:%M").time(), 
             datetime.strptime(f"{h+1:02d}:00", "%H:%M").time())
            for h in range(9, 17)
        ]

        # Iterate through each course
        for course in courses:
            sessions_scheduled = 0
            while sessions_scheduled < course.sessions_per_week:
                # Find available time slot
                for day in range(7):
                    lecturer_availability = LecturerAvailability.objects.filter(
                        lecturer=course.lecturer,
                        day=day
                    ).first()

                    if not lecturer_availability:
                        continue

                    for start_slot in time_slots:
                        start_time = start_slot[0]
                        end_time = (datetime.combine(datetime.min, start_time) + timedelta(hours=course.duration)).time()

                        if (start_time >= lecturer_availability.start_time and 
                            end_time <= lecturer_availability.end_time and
                            end_time <= time(17, 0)):  # Ensure it doesn't go past 5 PM
                            
                            # Find an available hall
                            available_hall = halls.filter(
                                type=course.required_hall_type
                            ).exclude(
                                Q(timeslot__day=day) &
                                Q(timeslot__start_time__lt=end_time) &
                                Q(timeslot__end_time__gt=start_time)
                            ).first()

                            if available_hall:
                                # Check if the lecturer is not teaching another course at this time
                                lecturer_conflict = Timeslot.objects.filter(
                                    course__lecturer=course.lecturer,
                                    day=day
                                ).filter(
                                    Q(start_time__lt=end_time) &
                                    Q(end_time__gt=start_time)
                                ).exists()

                                # Check for student conflicts (same degree and batch year)
                                student_conflict = Timeslot.objects.filter(
                                    course__degree=course.degree,
                                    course__Batch_Year=course.Batch_Year,
                                    day=day
                                ).filter(
                                    Q(start_time__lt=end_time) &
                                    Q(end_time__gt=start_time)
                                ).exists()

                                if not lecturer_conflict and not student_conflict:
                                    # Create the timeslot
                                    Timeslot.objects.create(
                                        day=day,
                                        start_time=start_time,
                                        end_time=end_time,
                                        hall=available_hall,
                                        course=course
                                    )
                                    sessions_scheduled += 1
                                    if sessions_scheduled == course.sessions_per_week:
                                        break
                    
                    if sessions_scheduled == course.sessions_per_week:
                        break
                
                if sessions_scheduled < course.sessions_per_week:
                    # If we couldn't schedule all sessions, break to avoid infinite loop
                    print(f"Warning: Could not schedule all sessions for course {course}")
                    break

    print("Timetable generation completed.")