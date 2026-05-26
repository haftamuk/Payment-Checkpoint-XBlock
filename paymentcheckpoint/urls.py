# paymentcheckpoint/paymentcheckpoint/urls.py
from django.urls import path
from . import views

app_name = 'payment_checkpoint'

urlpatterns = [
    path('mark_complete/', views.mark_complete, name='mark_complete'),
]