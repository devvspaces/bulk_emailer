from django.urls import path
from . import views

app_name = 'mailer'
urlpatterns = [
    path('', views.Dashboard.as_view(), name='home'),
    path('send-sms/', views.SmsDashboard.as_view(), name='phone')
]
