from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Twilio URLs
    path('add_user/', views.add_user, name='add_user'),
    path('sms_reply/', views.sms_reply, name='sms_reply'),
    path('call_answer/', views.call_answer, name='call_answer'),
    path('test_sms/', views.test_sms, name='test_sms'),
    path('test_call/', views.test_call, name='test_call'),
]