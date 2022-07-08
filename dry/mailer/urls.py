from django.urls import path
from .views import Dashboard

app_name = 'mailer'
urlpatterns = [
    path('', Dashboard.as_view())
]
