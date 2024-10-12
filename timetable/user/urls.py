from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.student_signup, name='student_signup'),
    path('login/', views.user_login, name='login'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('lecturer-dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/update-availability/<int:availability_id>/', views.update_availability, name='update_availability'),
]