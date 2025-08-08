from django.urls import path
from . import views

urlpatterns = [


    path('sign_in_admin', views.sign_in_admin , name='sign_in_admin'),

    path('signup_patient', views.signup_patient, name="signup_patient"),
    path('sign_in_patient', views.sign_in_patient , name='sign_in_patient'),
    
    path('savepdata/<str:patientusername>', views.savepdata , name='savepdata'),
    

    path('signup_doctor', views.signup_doctor , name="signup_doctor"),
    path('sign_in_doctor', views.sign_in_doctor , name='sign_in_doctor'),
    path('saveddata/<str:doctorusername>', views.saveddata , name='saveddata'),

    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<str:username>/', views.reset_password, name='reset_password'),

    path("update-last-seen/", views.update_last_seen, name="update_last_seen"),
    path('logout', views.logout , name='logout'),
]