from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Student, Degree,BatchYear,LecturerAvailability

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class StudentSignUpForm(UserCreationForm):
    full_name = forms.CharField(max_length=255,required=True)
    degree = forms.ModelChoiceField(queryset=Degree.objects.all(),required=True)
    Batch_Year = forms.ModelChoiceField(queryset=BatchYear.objects.all(), required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('full_name', 'degree','Batch_Year', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        user.username = User.generate_username(is_student=True)
        if commit:
            user.save()
            Student.objects.create(
                user=user,
                full_name=self.cleaned_data.get('full_name'),
                degree=self.cleaned_data.get('degree'),
                Batch_Year=self.cleaned_data.get('Batch_Year')
            )
        return user
    

class LecturerAvailabilityUpdateForm(forms.ModelForm):
    class Meta:
        model = LecturerAvailability
        fields = ['day', 'start_time', 'end_time']