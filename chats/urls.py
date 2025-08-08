from django.urls import path , include
from . import views

urlpatterns = [

 path('submit-doctor-feedback/', views.post_doctor_feedback, name='post_doctor_feedback'),
 path('submit-patient-feedback/', views.post_patient_feedback, name='post_patient_feedback'),
   
]