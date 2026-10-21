from django.urls import path
from . import views

app_name = 'mailer'
urlpatterns = [
    path('', views.Dashboard.as_view(), name='home'),
    path('send-sms/', views.SmsDashboard.as_view(), name='phone'),
    path('settings/', views.Settings.as_view(), name='settings'),
    path('help/', views.Help.as_view(), name='help'),
    path('jobs/', views.JobsView.as_view(), name='jobs'),
    path('jobs/data/', views.jobs_data, name='jobs_data'),
    path('jobs/<int:pk>/stop/', views.job_stop, name='job_stop'),
    path('jobs/stop-all/', views.job_stop_all, name='job_stop_all'),
    path('jobs/clear/', views.job_clear, name='job_clear'),
    path('jobs/clear-all/', views.job_clear_all, name='job_clear_all'),
]
