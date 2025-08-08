from django.urls import path , re_path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('report/pdf/<int:disease_id>/<int:consultation_id>/', views.generate_pdf, name='generate_pdf'),
    path('report/pdf/<int:disease_id>/', views.generate_pdf, name='generate_pdf_no_consult'),

    path('admin_ui', views.admin_ui , name='admin_ui'),
    path('admin_panel/registered/patients/', views.view_registered_patients, name='view_registered_patients'),
    path('admin_panel/registered/doctors/', views.view_registered_doctors, name='view_registered_doctors'),
   
    path('admin_panel/view_patients_feedbacks', views.view_patients_feedbacks , name='view_patients_feedbacks'),
    path('delete_patient_feedback/<int:id>/', views.delete_patient_feedback, name='delete_patient_feedback'),
    path('admin_panel/view_doctors_feedbacks', views.view_doctors_feedbacks , name='view_doctors_feedbacks'),
     path('delete_doctor_feedback/<int:id>/', views.delete_doctor_feedback, name='delete_doctor_feedback'),
    path('admin_panel/view_all_rating_reviews', views.view_all_rating_reviews , name='view_all_rating_reviews'),
    path('delete_rating_review/<int:id>/', views.delete_rating_review, name='delete_rating_review'),
    path('admin_panel/view_all_consultations', views.view_all_consultations , name='view_all_consultations'),


    path('patient_ui', views.patient_ui , name='patient_ui'),
    path('checkdisease', views.checkdisease, name="checkdisease"),
    path('view_predicted_diseases/', views.view_predicted_disease, name='view_predicted_disease'),
    path('pviewprofile/<str:patientusername>', views.pviewprofile , name='pviewprofile'),
    path('pconsultation_history', views.pconsultation_history , name='pconsultation_history'),
    path('consult_a_doctor', views.consult_a_doctor , name='consult_a_doctor'),
    path('make_consultation/<str:doctorusername>', views.make_consultation , name='make_consultation'),
    path('rate_review/<int:consultation_id>', views.rate_review , name='rate_review'),


    path('dconsultation_history', views.dconsultation_history , name='dconsultation_history'),
    path('manage_drugs/', views.manage_drug_recommendation, name='manage_drug_recommendation'),
    path('manage_drugs/edit/<int:id>/', views.edit_drug_recommendation, name='edit_drug_recommendation'),
    path('view_patient_reviews/', views.view_ratings_reviews, name='view_ratings_reviews'),
    path('dviewprofile/<str:doctorusername>', views.dviewprofile , name='dviewprofile'),
    path('doctor_ui', views.doctor_ui , name='doctor_ui'),
    
    
    
    path('consultationview/<int:consultation_id>', views.consultationview , name='consultationview'),
    path('consultation/<int:consultation_id>/prescription/', views.add_prescription_view, name='add_prescription'),
    path('submit_prescription/<int:consultation_id>/', views.submit_prescription, name='submit_prescription'),
    path('all_prescriptions/<int:diseaseinfo_id>/<int:patient_id>/<int:cons_id>/', views.view_all_prescriptions, name='view_all_prescriptions'),
    path('prescription/<int:prescription_id>/download/', views.download_prescription_pdf, name='download_prescription_pdf'),
    path('close_consultation/<int:consultation_id>', views.close_consultation , name='close_consultation'),

    
    path('post', views.post, name='post'),
    path('chat_messages', views.chat_messages, name='chat_messages'),
    path('ajax/check_messages/', views.check_messages, name='check_messages'), 
    path('get_consultation_id_from_chat/<int:chat_id>/', views.get_consultation_id_from_chat, name='get_consultation_id_from_chat'),


]  
