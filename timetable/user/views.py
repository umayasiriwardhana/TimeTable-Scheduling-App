from django.contrib import messages
from .models import LecturerAvailability,Course,BatchYear,Degree,Timeslot
from .timetable_generator import generate_timetable
from django.shortcuts import render,redirect, get_object_or_404
from .forms import StudentSignUpForm, LoginForm,LecturerAvailabilityUpdateForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required


def student_signup(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            message = f'Your username is {user.username}'
            return render(request, 'auth/signup.html', {
                'form': StudentSignUpForm(),
                'show_modal': True,
                'message': message
            })
    else:
        form = StudentSignUpForm()
    return render(request, 'auth/signup.html', {'form': form, 'show_modal': False})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_student:
                    return redirect('student_dashboard')
                elif user.is_lecturer:
                    return redirect('lecturer_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'auth/signin.html', {'form': form})

@login_required
def lecturer_dashboard(request):
    if not request.user.is_lecturer:
        return redirect('login')
    
    lecturer = request.user.lecturer
    courses = Course.objects.filter(lecturer=lecturer)
    availabilities = LecturerAvailability.objects.filter(lecturer=lecturer).order_by('day', 'start_time')
    
    return render(request, 'lecturer/dashboard.html', {
        'lecturer': lecturer,
        'courses': courses,
        'availabilities': availabilities
    })

@login_required
def student_dashboard(request):
    if not request.user.is_student:
        return redirect('login')
    
    student = request.user.student
    timeslots = Timeslot.objects.filter(
        course__Batch_Year=student.Batch_Year,
        course__degree=student.degree
    ).order_by('day', 'start_time')
    
    time_slots = ['09', '10', '11', '12', '13', '14', '15', '16']
    days_of_week = range(7)  
    
    return render(request, 'student/dashboard.html', {
        'student': student,
        'timeslots': timeslots,
        'time_slots': time_slots,
        'days_of_week': days_of_week,
    })

@login_required
def update_availability(request, availability_id):
    availability = get_object_or_404(LecturerAvailability, id=availability_id, lecturer=request.user.lecturer)
    
    if request.method == 'POST':
        form = LecturerAvailabilityUpdateForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            generate_timetable(request.user.lecturer.Faculty)  
            return redirect('lecturer_dashboard')
    else:
        form = LecturerAvailabilityUpdateForm(instance=availability)
    
    return render(request, 'lecturer/update_availability.html', {
        'form': form,
        'availability': availability
    })

def home(request):
    return render(request, 'home.html')