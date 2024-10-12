from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import BatchYear,Course,Faculty,Degree,Hall,Lecturer,User,LecturerAvailability,Timeslot

class LecturerInline(admin.StackedInline):
    model = Lecturer
    can_delete = False
    verbose_name_plural = 'Lecturer'

class CustomUserAdmin(UserAdmin):
    inlines = (LecturerInline,)
    list_display = ('username', 'get_full_name', 'is_staff', 'is_lecturer','is_student')
    list_filter = ('is_staff','is_lecturer','is_student')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('User Type', {'fields': ('is_lecturer',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('password1', 'password2', 'is_lecturer'),
        }),
    )

    def get_full_name(self, obj):
        if obj.is_lecturer:
            return obj.lecturer.full_name
        elif obj.is_student:
            return obj.student.full_name
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'

    def save_model(self, request, obj, form, change):
        if not change: 
            obj.username = User.generate_username(is_student=obj.is_student, is_lecturer=obj.is_lecturer)
        super().save_model(request, obj, form, change)
        if not change and obj.is_lecturer:
            Lecturer.objects.create(user=obj, full_name=f"{obj.first_name} {obj.last_name}")

class CourseAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'duration':
            formfield.label = 'Duration (Hours)'  
        return formfield
    
admin.site.register(User, CustomUserAdmin)
admin.site.register(Faculty)
admin.site.register(Degree)
admin.site.register(Course, CourseAdmin)
admin.site.register(Hall)
admin.site.register(BatchYear)

