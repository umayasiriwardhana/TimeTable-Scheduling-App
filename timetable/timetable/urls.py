
from django.contrib import admin
from django.urls import path,include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls')),
]

admin.site.index_title = "Timetable Management System"
admin.site.site_header = "Timetable Management System Admin"
admin.site.site_title = "Timetable Management System"

urlpatterns += staticfiles_urlpatterns()