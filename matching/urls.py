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
    path('user/<int:user_id>', views.get_user, name='get_user'),

    path('generate_users/', views.generate_users, name='generate_users'),
    path('match_users/', views.match_users, name='match_users'),
    path('unmatch_users/', views.unmatch_users, name='unmatch_users'),
]