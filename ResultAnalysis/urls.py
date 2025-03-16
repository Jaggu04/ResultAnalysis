"""
URL configuration for ResultAnalysis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Analysis.views import * #to import all the functions from the views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/',home,name='home'),#call to home function
    path('logout/', stafflogout, name='stafflogout'),
    path('stafflogin/',stafflogin,name='stafflogin'),
    path('',upload_and_analyze, name='upload_and_analyze'),
    path('download/full/',download_full_pdf, name='download_full_pdf'),
    path('download/student/<str:student_name>/', download_student_pdf, name='download_student_pdf'),

     path('upload/', upload_file, name='upload_file'),
    path('files/', file_list, name='file_list'),
    path('download/<int:file_id>/', download_file, name='download_file')

]
