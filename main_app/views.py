import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from datetime import date, timedelta, datetime
from django.template.loader import get_template
import pytz, re
from xhtml2pdf import pisa
from django.utils import timezone
from django.utils.timezone import now


from django.contrib import messages
from django.contrib.auth.models import User , auth

from disease_prediction import settings
from django.db.models import Q, Case, When, IntegerField
from .models import patient, doctor, diseaseinfo, drugrecommendation, consultation, rating_review, prescription
from chats.models import Chat, PatientFeedback, DoctorFeedback

import pandas as pd
import numpy as np
import os, base64



if drugrecommendation.objects.count() == 0:
    description_df = pd.read_csv("kaggle_datasets/description_clean.csv")
    precautions_df = pd.read_csv("kaggle_datasets/precautions_clean.csv")
    medications_df = pd.read_csv("kaggle_datasets/medications_clean.csv")
    diet_df = pd.read_csv("kaggle_datasets/diet_clean.csv")
    workout_df = pd.read_csv("kaggle_datasets/workout_clean.csv")

    # Iterate and populate drugrecommendation
    for disease in description_df['Disease'].unique():
        description = description_df[description_df['Disease'] == disease]['Description'].iloc[0]

        precautions = precautions_df[precautions_df['Disease'] == disease].iloc[:, 1:].values.flatten()
        precautions_str = ', '.join(filter(None, precautions))

        medications = medications_df[medications_df['Disease'] == disease].iloc[:, 1:].values.flatten()
        medications_str = ', '.join(filter(None, medications))

        diet = diet_df[diet_df['Disease'] == disease].iloc[:, 1:].values.flatten()
        diet_str = ', '.join(filter(None, diet))

        workout = workout_df[workout_df['Disease'] == disease].iloc[:, 1:].values.flatten()
        workout_str = ', '.join(filter(None, workout))

        drugrecommendation.objects.create(
            diseasename=disease,
            description=description,
            precautions=precautions_str,
            medications=medications_str,
            diet=diet_str,
            workout=workout_str
        )

    print("✅ drugrecommendation data loaded.")
else:
    print("⚠️ drugrecommendation table already populated. Skipping.")



import joblib
from huggingface_hub import hf_hub_download

REPO_ID = "Sharav1312/mutiple_disease_prediction"

try:
    model = joblib.load(
    hf_hub_download(repo_id=REPO_ID, filename="disease_model.pkl")
    )
    
    le = joblib.load(
    hf_hub_download(repo_id=REPO_ID, filename="label_encoder.pkl")
    )
    
    feature_names = joblib.load(
    hf_hub_download(repo_id=REPO_ID, filename="feature_names.pkl")
    )

    print("model loaded successfully")

except Exception as e:
   print("model loading was unsuccessfull", e)




def generate_pdf(request, disease_id, consultation_id = None):
    disease = diseaseinfo.objects.get(id=disease_id)
    patient_user = disease.patient.user

    # Fetch drug recommendation
    try:
        drug = drugrecommendation.objects.get(diseasename=disease.diseasename)
    except drugrecommendation.DoesNotExist:
        drug = None

    # Fetch consultation
    try:
        consult = consultation.objects.get(id = consultation_id, diseaseinfo=disease)
        doctor_name = consult.doctor.name if consult.doctor else "N/A"
        specialization = consult.doctor.specialization
        consultation_date = consult.consultation_date
        status = consult.status
        last_consultation_date = consult.last_consultation_date
        next_consultation_date = consult.next_consultation_date
    except consultation.DoesNotExist:
        consult = None
        specialization = None
        doctor_name = None
        consultation_date = None
        status = None
        next_consultation_date = None
        last_consultation_date = None

    # Load logo
    logo_path = os.path.join(settings.BASE_DIR, 'templates', 'homepage', 'healurix_logo.png')
    with open(logo_path, 'rb') as img:
        logo_base64 = base64.b64encode(img.read()).decode('utf-8')

    context = {
        'disease': disease,
        'patient_id': patient_user.id,
        'patient_name': disease.patient.name,
        'patient_age': disease.patient.age,
        'patient_gender': disease.patient.gender,
        'date_generated': timezone.now(),

        'description': drug.description if drug else "N/A",
        'precautions': ', '.join(part.strip().capitalize() for part in drug.precautions.split(',')) if drug else "N/A",
        'medications':  ', '.join(part.strip().capitalize() for part in drug.medications.split(',')) if drug else "N/A",
        'diet': ', '.join(part.strip().capitalize() for part in drug.diet.split(',')) if drug else "N/A",
        'workout': ', '.join(part.strip().capitalize() for part in drug.workout.split(',')) if drug else "N/A",
        'is_approved' : drug.is_approved,
        'approved_by' : drug.approvedby.name if drug.is_approved else "N/A",
        'approved_doctor_specialization' : drug.approvedby.specialization if drug.approvedby and drug.approvedby.specialization else "Nill",
        'logo_base64': logo_base64,

        # Consultation data
        'has_consultation': consult is not None,
        'doctor_name': doctor_name,
        'specialization' : specialization,
        'consultation_date': consultation_date,
        'status': status,
        'last_consultation_date': last_consultation_date,
        'next_consultation_date': next_consultation_date,
    }

    safe_name = disease.patient.name.replace(' ', '_')

    template_path = 'pdf_template.html'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Healurix_Report_{safe_name}_PID{patient_user.id}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('PDF generation failed')
    return response


def download_prescription_pdf(request, prescription_id):
    try:
        prescription_obj = prescription.objects.get(id=prescription_id)
    except prescription.DoesNotExist:
        return HttpResponse('Prescription not found', status=404)

    patient_user = prescription_obj.patient.user

    # Load logo
    logo_path = os.path.join(settings.BASE_DIR, 'templates', 'homepage', 'healurix_logo.png')
    with open(logo_path, 'rb') as img:
        logo_base64 = base64.b64encode(img.read()).decode('utf-8')

    # ============================
    # Process Tablets (new format)
    # ============================
    tablet_entries = []
    for tab in prescription_obj.tablets:
        tablet_entries.append({
            'name': tab.get('name', ''),
            'frequency': tab.get('frequency', ''),
            'food': tab.get('food', ''),
            'duration': tab.get('duration', '')
        })

    # ============================
    # Process Tests
    # ============================
    test_data = []
    for group_name, tests in prescription_obj.tests.items():  # e.g. "xray", "scan"
        for test in tests:
            test_data.append({
                'group': group_name.title(),  # Optional: Capitalize group name
                'name': test.get('name', ''),
                'food': test.get('food', '')
            })

    # ============================
    # Context Setup
    # ============================
    template_path = 'consultation/prescription_pdf.html'
    context = {
        'prescription': prescription_obj,
        'logo_base64': logo_base64,
        'tablets': tablet_entries,
        'suggested_tests': test_data,
    }

    safe_name = prescription_obj.patient.name.replace(' ', '_')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Healurix_Prescription_{safe_name}_PID{patient_user.id}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response





def home(request):
    
    
    pfeedback_obj = list(PatientFeedback.objects.filter(allow_public = True))  
    return render(request,'homepage/index.html', {'all_feedbacks' : pfeedback_obj} )

    




def admin_ui(request):

    if request.method == 'GET':

      if request.user.is_authenticated:

        auser = request.user
        pfeedback_obj = list(PatientFeedback.objects.filter(allow_public = True)) 

        return render(request,'admin/admin_ui/admin_ui.html' , {"auser":auser, 'pfeedbacks' : pfeedback_obj} )

      else :
        return redirect('home')


def view_registered_patients(request):

    patients = patient.objects.all().order_by('user_id')
    return render(request, 'admin/view_registered_patients/view_registered_patients.html', {'patients': patients})

def view_registered_doctors(request):
    
    doctors = doctor.objects.all().order_by('user_id')
    return render(request, 'admin/view_registered_doctors/view_registered_doctors.html', {'doctors': doctors})


# def delete_patient(request, id):

#     if request.method == 'POST':
#         pat = patient.objects.get(id=id)
#         pat.user.delete()
#         return redirect('view_registered_patients')

# def delete_doctor(request, id):

#     if request.method == 'POST':
#         doc = doctor.objects.get(id=id)
#         doc.user.delete()
#         return redirect('view_registered_doctors')


    

def view_patients_feedbacks(request):

    pfeedback_obj = PatientFeedback.objects.all()

    return render(request, 'admin/view_patients_feedbacks/view_patients_feedbacks.html', {'all_patient_feedbacks' : pfeedback_obj})


def delete_patient_feedback(request, id):
    if request.method == 'POST':
        feedback = PatientFeedback.objects.get(id = id)
        feedback.delete()
        messages.success(request, 'Feedback deleted successfully.')
    return redirect('view_patients_feedbacks')
    

def view_doctors_feedbacks(request):
    dfeedback_obj = DoctorFeedback.objects.all()

    return render(request, 'admin/view_doctors_feedbacks/view_doctors_feedbacks.html', {'all_doctor_feedbacks' : dfeedback_obj})


def delete_doctor_feedback(request, id):
    if request.method == 'POST':
        feedback = DoctorFeedback.objects.get(id = id)
        feedback.delete()
        messages.success(request, 'Doctor feedback deleted successfully.')
    return redirect('view_doctors_feedbacks')


def view_all_rating_reviews(request):

    rating_obj = rating_review.objects.all()

    return render(request, 'admin/all_rating_reviews/view_all_ratings_reviews.html', {'all_ratings_reviews' : rating_obj})


def delete_rating_review(request, id):
    if request.method == "POST":
        review = rating_review.objects.get(id = id)
        review.delete()
        messages.success(request, "Review deleted successfully.")
    return redirect('view_all_rating_reviews')


def view_all_consultations(request):
    
    consultation_obj = consultation.objects.all()

    return render(request, 'admin/view_all_consultations/view_all_consultations.html', {'all_consultations' : consultation_obj})







def patient_ui(request):

    if request.method == 'GET':

      if request.user.is_authenticated:

        patientusername = request.session['patientusername']
        puser = User.objects.get(username=patientusername)

        feedback_obj = PatientFeedback.objects.filter(
            patient_id = request.user.patient,
            allow_public = True
        )

        # chats logic
        Chat.objects.filter(
            consultation_id__patient__user=puser,
            status='sent'
        ).exclude(sender=puser).update(status='delivered')

        return render(request,'patient/patient_ui/profile.html' , {"puser":puser, "allowed_public" : feedback_obj})

      else :
        return redirect('home')



    if request.method == 'POST':

       return render(request,'patient/patient_ui/profile.html')


       


def pviewprofile(request, patientusername):

    if request.method == 'GET':

          puser = User.objects.get(username=patientusername)

          return render(request,'patient/view_profile/view_profile.html', {"puser":puser})
    



def view_predicted_disease(request):
    if request.method == 'GET':
        if request.user.is_authenticated:

            patientusername = request.session['patientusername']
            puser = User.objects.get(username=patientusername)

            patient_obj = puser.patient
            p_patient = patient.objects.get(user=puser)  

            predictions = diseaseinfo.objects.filter(patient=p_patient).order_by('-id')

         
            for pred in predictions:
                related_consult = consultation.objects.filter(patient=patient_obj, diseaseinfo=pred).last()
                if related_consult:
                    pred.consult_status = related_consult.status
                    pred.consultation_id = related_consult.id
                    pred.has_prescription = prescription.objects.filter(consultation_id=related_consult).exists()
                else:
                    pred.consult_status = None
                    pred.consultation_id = None
                    pred.has_prescription = False



            return render(request, 'patient/viewdiseases/view_predicted_diseases.html', {
                "puser": puser,
                "predictions": predictions
            })
        else:
            return redirect('home')


      
      
  
def view_all_prescriptions(request, diseaseinfo_id, patient_id, cons_id):
    patient_user = User.objects.get(id=patient_id)
    patient_obj = patient.objects.get(user=patient_user) 

    # Get all consultations related to this disease and patient
    consultations = consultation.objects.filter(
        id = cons_id,
        patient=patient_obj,
        diseaseinfo_id=diseaseinfo_id
    )

    doctor_obj = consultations.first().doctor if consultations.exists() else None

    # Get all prescriptions linked to those consultations
    prescriptions = prescription.objects.filter(
        consultation__in=consultations
    ).order_by('-issued_date')  # latest first

      # Update the 'seen' flags
    if request.user.is_authenticated:
        if hasattr(request.user, 'patient') and request.user.patient == patient_obj:
            prescriptions.update(patient_seen=True)
        elif hasattr(request.user, 'doctor'):
            prescriptions.update(doctor_seen=True)


    context = {
        'prescriptions': prescriptions,
        'diseaseinfo': diseaseinfo.objects.get(id=diseaseinfo_id),
        'patient_obj' : patient_obj,
        'consulted_doctor': doctor_obj
    }

    return render(request, 'patient/viewdiseases/view_prescriptions.html', context)




def checkdisease(request):

    alphabaticsymptomslist = sorted(feature_names)

    if request.method == 'GET':
        return render(
            request,
            'patient/checkdisease/checkdisease.html',
            {"list2": alphabaticsymptomslist}
        )

    elif request.method == 'POST':

        inputno = int(request.POST["noofsym"])

        if inputno == 0:
            return JsonResponse({
                'predicteddisease': "none",
                'confidencescore': 0
            })

        # Selected symptoms from UI
        psymptoms = request.POST.getlist("symptoms[]")

        # ✅ Build input vector using TRAINING feature order
        testingsymptoms = [0] * len(feature_names)

        for i, symptom in enumerate(feature_names):
            if symptom in psymptoms:
                testingsymptoms[i] = 1

        inputtest = [testingsymptoms]

        # Safety check (prevents silent bugs)
        if len(testingsymptoms) != model.n_features_in_:
            return JsonResponse({
                "error": "Model feature mismatch. Please contact admin."
            })

        # ================= ML PREDICTION =================
        probs = model.predict_proba(inputtest)[0]

        # Top-3 predictions
        top3_idx = np.argsort(probs)[-3:][::-1]

        top3 = []
        for idx in top3_idx:
            top3.append({
                "disease": le.classes_[idx],
                "confidence": round(probs[idx] * 100, 2)
            })

        predicted_disease = top3[0]["disease"]
        confidencescore = round(top3[0]["confidence"], 0)

        CONFIDENCE_THRESHOLD = 40

        if confidencescore < CONFIDENCE_THRESHOLD:
            confidence_status = "low"
            confidence_message = (
                "🚩 Low confidence prediction. "
                "Symptoms are insufficient or overlapping. "
                "Please consult a doctor for proper diagnosis."
            )
        else:
            confidence_status = "high"
            confidence_message = (
                "🚩 Prediction confidence is reasonably high. "
                "This is not a medical diagnosis. "
                "Consult the recommended specialist immediately."
            )


        # ================= DOCTOR ROUTING =================
        General_Physician = [
            'Allergy', 'GERD', 'Adverse Drug Reaction', 'AIDS', 'Diabetes ',
            'Hypertension ', 'Migraine', 'Paralysis (brain hemorrhage)',
            'Jaundice', 'Malaria', 'Chicken pox', 'Dengue',
            'Typhoid', 'Hypoglycemia'
        ]

        Cardiologist = ['Heart attack']

        Hepatologist = [
            'Hepatitis E', 'Alcoholic hepatitis', 'Hepatitis A',
            'Hepatitis B', 'Hepatitis C', 'Hepatitis D'
        ]

        Pulmonologist = [
            'Tuberculosis', 'Bronchial Asthma',
            'Common Cold', 'Pneumonia'
        ]

        Endocrinologist = ['Hypothyroidism', 'Hyperthyroidism']

        Orthopedician = [
            'Osteoarthritis', 'Rheumatoid Arthritis',
            'Cervical spondylosis'
        ]

        General_Surgeon = [
            'Varicose veins', 'Peptic ulcer disease',
            'Chronic Cholecystitis', 'Gastroenteritis',
            'Hemorrhoids(piles)'
        ]

        ENT_Specialist = ['Paroxysmal Positional Vertigo']

        Urologist = ['Urinary tract infection']

        Dermatologist = [
            'Acne', 'Fungal infection',
            'Psoriasis', 'Impetigo'
        ]

        if predicted_disease in General_Physician:
            consultdoctor = "General Physician"
        elif predicted_disease in Cardiologist:
            consultdoctor = "Cardiologist"
        elif predicted_disease in Hepatologist:
            consultdoctor = "Hepatologist"
        elif predicted_disease in Pulmonologist:
            consultdoctor = "Pulmonologist"
        elif predicted_disease in Endocrinologist:
            consultdoctor = "Endocrinologist"
        elif predicted_disease in Orthopedician:
            consultdoctor = "Orthopedician"
        elif predicted_disease in General_Surgeon:
            consultdoctor = "General Surgeon"
        elif predicted_disease in Dermatologist:
            consultdoctor = "Dermatologist"
        elif predicted_disease in ENT_Specialist:
            consultdoctor = "ENT Specialist"
        elif predicted_disease in Urologist:
            consultdoctor = "Urologist"
        else:
            consultdoctor = "Other"

        request.session['doctortype'] = consultdoctor

        # ================= SAVE TO DB =================
        patientusername = request.session['patientusername']
        puser = User.objects.get(username=patientusername)

        diseaseinfo_new = diseaseinfo(
            patient=puser.patient,
            diseasename=predicted_disease,
            no_of_symp=inputno,
            symptomsname=psymptoms,
            confidence=confidencescore,
            consultdoctor=consultdoctor
        )

        diseaseinfo_new.save()
        request.session['diseaseinfo_id'] = diseaseinfo_new.id

        return JsonResponse({
            'predicteddisease': predicted_disease,
            'disease_id': diseaseinfo_new.id,
            'top3': top3,
            'confidencescore': float(confidencescore),
            'consultdoctor': consultdoctor,
            "confidence_status": confidence_status,   # "low" or "high"
            "confidence_message": confidence_message
        })




   
    


def pconsultation_history(request):
    if request.method == 'GET':
        patientusername = request.session['patientusername']
        puser = User.objects.get(username=patientusername)
        patient_obj = puser.patient

        consultationnew = consultation.objects.filter(patient=patient_obj)

       
        today = date.today()

        for c in consultationnew:
            if c.status == 'closed' or c.status == 'active':
                chats = Chat.objects.filter(consultation_id=c.id).order_by('created')
                unread_messages = chats.filter(status='delivered').exclude(sender=puser).count()


                for chat in chats:
                    sender = User.objects.filter(id=chat.sender_id).first()
                    chat.sender_name = sender.username
                    chat.is_patient = (sender == puser)

                c.chat_history = chats
                c.unread_count = unread_messages


                unread_prescriptions = prescription.objects.filter(patient=patient_obj, 
                                                           consultation = c.id,
                                                           patient_seen=False).count()
                
                c.unread_prescriptions = unread_prescriptions
                
                average = c.doctor.rating
                c.average_rating = average
                c.is_top_consultant = average >= 4.5


        

            if c.status == 'closed' and c.next_consultation_date == today:
                c.status = 'active'
                c.last_consultation_date = today
                c.save()
            elif c.status == 'active' and c.next_consultation_date and c.next_consultation_date < today:
                c.status = 'closed'
                c.next_consultation_date = None
                c.save()

        
        
  
        tomorrow = today + timedelta(days=1)

        return render(request, 'patient/consultation_history/consultation_history.html', {
            "consultation": consultationnew,
            'today' : today,
            'tomorrow' : tomorrow
        })



def dconsultation_history(request):
    if request.method == 'GET':
        doctorusername = request.session['doctorusername']
        duser = User.objects.get(username=doctorusername)
        doctor_obj = duser.doctor

        consultationnew = consultation.objects.filter(doctor=doctor_obj)


        today = date.today()

        for c in consultationnew:
            if c.status == 'closed' or c.status == 'active':
                chats = Chat.objects.filter(consultation_id=c.id).order_by('created')
                unread_messages = chats.filter(status='delivered').exclude(sender=duser).count()

                for chat in chats:
                    sender = User.objects.filter(id=chat.sender_id).first()
                    chat.sender_name = sender.username
                    chat.is_doctor = (sender == duser)

                c.chat_history = chats
                c.unread_count = unread_messages 

                unread_prescriptions = prescription.objects.filter(
                                                                doctor=doctor_obj, 
                                                                consultation = c.id,
                                                                doctor_seen=False).count()
                c.unread_prescriptions = unread_prescriptions 




            if c.status == 'closed' and c.next_consultation_date == today:
                c.status = 'active'
                c.last_consultation_date = today
                c.save()
            elif c.status == 'active' and c.next_consultation_date and c.next_consultation_date < today:
                c.status = 'closed'
                c.next_consultation_date = None
                c.save()



        tomorrow = today + timedelta(days=1)

        return render(request, 'doctor/consultation_history/consultation_history.html', {
            "consultation": consultationnew,
            'today' : today,
            'tomorrow' : tomorrow
        })




def doctor_ui(request):

    if request.method == 'GET':

        doctor_username = request.session['doctorusername']
        duser = User.objects.get(username=doctor_username)
        doc_profile = doctor.objects.get(user=duser)


        # chats logic
        Chat.objects.filter(
            consultation_id__doctor__user=duser,
            status='sent'
        ).exclude(sender=duser).update(status='delivered')
    
        return render(request,'doctor/doctor_ui/profile.html',{"duser":doc_profile})



      


def dviewprofile(request, doctorusername):

    if request.method == 'GET':
 
         duser = User.objects.get(username=doctorusername)
         ratings = rating_review.objects.filter(doctor=duser.doctor)
       
         return render(request,'doctor/view_profile/view_profile.html', 
                       {"duser":duser, 
                        "rate":ratings
                        
                        } )
    


def manage_drug_recommendation(request):
    doctor_specialization = request.user.doctor.specialization  # assuming relationship
    specialization_map = {
        "General Physician": ['Allergy', 'GERD', 'Adverse Drug Reaction', 'AIDS', 'Diabetes', 'Hypertension', 'Migraine',
                              'Paralysis (brain hemorrhage)', 'Jaundice', 'Malaria', 'Chicken pox', 'Dengue',
                              'Typhoid', 'Hypoglycemia'],
        "Cardiologist": ['Heart attack'],
        "Hepatologist": ['Hepatitis E', 'Alcoholic hepatitis', 'Hepatitis A', 'Hepatitis B', 'Hepatitis C', 'Hepatitis D'],
        "Pulmonologist": ['Tuberculosis', 'Bronchial Asthma', 'Common Cold', 'Pneumonia'],
        "Endocrinologist": ['Hypothyroidism', 'Hyperthyroidism'],
        "Orthopedician": ['Osteoarthritis', 'Rheumatoid Arthritis', 'Cervical spondylosis'],
        "General Surgeon": ['Varicose veins', 'Peptic ulcer disease', 'Chronic Cholecystitis', 'Gastroenteritis', 'Hemorrhoids(piles)'],
        "ENT Specialist": ['Paroxysmal Positional Vertigo'],
        "Urologist": ['Urinary tract infection'],
        "Dermatologist": ['Acne', 'Fungal infection', 'Psoriasis', 'Impetigo'],
    }

    allowed_diseases = specialization_map.get(doctor_specialization, [])

    if request.method == "POST":

        # if 'create' in request.POST:
        #     disease = request.POST.get('diseasename')
        #     if disease in allowed_diseases:
        #         drugrecommendation.objects.create(
        #             diseasename=disease,
        #             description=request.POST.get('description'),
        #             precautions=request.POST.get('precautions'),
        #             medications=request.POST.get('medications'),
        #             diet=request.POST.get('diet'),
        #             workout=request.POST.get('workout'),
        #             addedby="healurix"
        #         )
        #         messages.success(request, "Recommendation added successfully!")
        #     else:
        #         messages.error(request, "You are not authorized to add recommendation for this disease.")

        if 'delete' in request.POST:
            rec_id = request.POST.get('id')
            rec = drugrecommendation.objects.filter(id=rec_id).first()
            if rec:
                rec.delete()
                messages.success(request, "Recommendation deleted successfully!")

        elif 'approve' in request.POST:
            rec_id = request.POST.get('id')
            rec = drugrecommendation.objects.filter(id=rec_id).first()
            if rec:
                rec.is_approved = True
                rec.approvedby = request.user.doctor
                rec.save()
                messages.success(request, "Recommendation approved")

        return redirect('manage_drug_recommendation')

   

    recommendations = drugrecommendation.objects.filter(
        diseasename__in=allowed_diseases
    ).annotate(
        is_unapproved_first=Case(
            When(is_approved=False, then=0),
            When(is_approved=True, then=1),
            output_field=IntegerField()
        )
    ).order_by('is_unapproved_first')

    return render(request, 'doctor/manage_drugs/manage_drugrecommendations.html', {
        'recommendations': recommendations
    })



def view_ratings_reviews(request):
    duser = request.user.doctor

    rating_obj = rating_review.objects.filter(doctor=duser) 

    return render(request, 'doctor/view_patient_reviews/view_reviews_ratings.html', {
        'duser': duser,
        'all_ratings': rating_obj
        
    })







def edit_drug_recommendation(request, id):
    rec = drugrecommendation.objects.filter(id=id).first()
    if not rec:
        return redirect('manage_drug_recommendation')

    if request.method == "POST":
        if 'update' in request.POST:
            rec.description = request.POST.get('description')
            rec.precautions = request.POST.get('precautions')
            rec.medications = request.POST.get('medications')
            rec.diet = request.POST.get('diet')
            rec.workout = request.POST.get('workout')
            rec.updatedby = request.user.doctor
            rec.save()
            messages.success(request, "Recommendation updated successfully!")


    return render(request, 'doctor/manage_drugs/edit_drugrecommendation.html', {'rec': rec})





def add_prescription_view(request, consultation_id):
   
    consultation_obj = consultation.objects.get(id=consultation_id)

    
    test_groups = ["xray", "blood", "urine", "echo", "ct", "usg", "mri", "doppler"]

    x_ray = ['Chest X-ray', 'Bone X-ray', 'Abdominal X-ray', 'Angiography', 'Barium X-ray', 'Mammography', 
                 'Bone Density Scan (DEXA)']
        
    blood_tests = ['CBC', 'RFT', 'LFT', 'Coagulation profile', 'IV ELISA', 'FBS', 'PPBS', 
                       'MPMF', 'WIDAL', 'Hepatitis A antigen', 'Hepatitis B antigen', 
                       'Hepatitis C antigen', 'Hepatitis D antigen', 'Hepatitis E antigen' 'CRP', 
                       'Rheumatoid factor', 'Thyroid function test']
        
    urine_analysis = ['Urine Routine', 'Urine Culture and Sensitivity']

    echo = ['TTE', 'TEE', 'Stress Echo', 'Fetal Echo', 'Contrast Echo', '3D Echo']

    usg = [ 'Usg Breast', 'Usg Abdomen and Pelvis']

    ct = ['CT Brain', 'CT Chest', 'CT Abdomen', 'C spine', 'Dls spine'] 

    mri = ['Brain', 'Pelvis', 'C Spine With Whole Spine', 'MRI abdomen'] 

    doppler = ['Upper Limb Doppler', 'Lower Limb Doppler', 'Carotid Doppler']
    
    context = {
        'consultation': consultation_obj,

        "test_groups" : test_groups,
        'x_ray': x_ray,
        'blood_tests': blood_tests,
        'urine_analysis': urine_analysis,
        'echo': echo,
        'usg': usg,
        'ct': ct,
        'mri': mri,
        'doppler': doppler,
    }



    return render(request, 'consultation/prescription_form.html', context)






def submit_prescription(request, consultation_id):
    consultation_obj =consultation.objects.get(id=consultation_id)

    if request.method == 'POST':
        tablets = []

        tablet_name_keys = [key for key in request.POST if key.startswith('tablet_name_')]
        for key in tablet_name_keys:
            match = re.search(r'tablet_name_(\d+)', key)
            if not match:
                continue

            index = match.group(1)
            name = request.POST.get(f'tablet_name_{index}', '').strip()
            frequency = request.POST.get(f'frequency_{index}', '').strip()
            duration = request.POST.get(f'duration_{index}', '').strip()
            food = request.POST.getlist(f'food_instruction_{index}')

            if name:
                tablets.append({
                    "name": name,
                    "frequency": frequency,
                    "food": food,
                    "duration": duration
                })


        # Test collection
        # Parse JSON test data
        try:
            tests_json = request.POST.get("tests_json", "{}")
            tests = json.loads(tests_json)
        except json.JSONDecodeError:
            tests = {}


        prescription.objects.create(
            consultation=consultation_obj,
            doctor=request.user.doctor,
            patient=consultation_obj.patient,
            tablets=tablets,
            tests=tests
        )

        messages.success(request, "Prescription submitted successfully.")
        return redirect('consultationview', consultation_id=consultation_id)







def consult_a_doctor(request):
    if request.method == 'GET':
        doctortype = request.GET.get('consultdoctor') or request.session.get('doctortype')
        dobj = doctor.objects.filter(specialization=doctortype).order_by('-rating')
        patientid = request.session.get('patientid')
        diseaseinfo_id = request.GET.get('diseaseinfo_id') or request.session.get('diseaseinfo_id')

        today = date.today()
        tomorrow = today + timedelta(days=1)

        doctors_with_consultation = []

        for doc in dobj:
            consult_qs = consultation.objects.filter(
                doctor=doc,
                patient_id=patientid,
                diseaseinfo_id=diseaseinfo_id
            )

            consult_data = {
                "doctor": doc,
                "has_consultation": False,
                "status": None,
                "consultation_id": None,
                "next_consultation_date": None,
                "top_consultant": False
            }

            if consult_qs.exists():
                consult_obj = consult_qs.latest("consultation_date")  # safer than first()

                # Auto update logic
                if consult_obj.status == 'closed' and consult_obj.next_consultation_date == today:
                    consult_obj.status = 'active'
                    consult_obj.last_consultation_date = today
                    consult_obj.save()
                elif consult_obj.status == 'active' and consult_obj.next_consultation_date and consult_obj.next_consultation_date < today:
                    consult_obj.status = 'closed'
                    consult_obj.next_consultation_date = None
                    consult_obj.save()

                consult_data.update({
                    "has_consultation": True,
                    "status": consult_obj.status,
                    "consultation_id": consult_obj.id,
                    "next_consultation_date": consult_obj.next_consultation_date,
                    "top_consultant": doc.rating and doc.rating >= 4.5
                })

            doctors_with_consultation.append(consult_data)

        return render(request, 'patient/consult_a_doctor/consult_a_doctor.html', {
            "dobj" : dobj,
            "doctors_data": doctors_with_consultation,
            "specialized_name": doctortype,
            "diseaseinfo_id": diseaseinfo_id,
            "today": today,
            "tomorrow": tomorrow
        })






   
def make_consultation(request, doctorusername):
    
    if request.method == 'POST':
            patientusername = request.session['patientusername']
            puser = User.objects.get(username=patientusername)
            patient_obj = puser.patient

            duser = User.objects.get(username=doctorusername)
            doctor_obj = duser.doctor

            diseaseinfo_id = request.POST.get('diseaseinfo_id') or request.session['diseaseinfo_id']
            diseaseinfo_obj = diseaseinfo.objects.get(id=diseaseinfo_id)

            # Check if a consultation already exists
            existing_consult = consultation.objects.filter(
                patient=patient_obj,
                diseaseinfo=diseaseinfo_obj,
                doctor=doctor_obj
             ).first()

            if existing_consult:
                return redirect('consultationview', existing_consult.id)

            consultation_date = date.today() 

            new_consult = consultation.objects.create(
                patient=patient_obj,
                doctor=doctor_obj,
                diseaseinfo=diseaseinfo_obj,
                status='active',
                consultation_date=consultation_date
            )
            return redirect('consultationview', new_consult.id)

    




def  consultationview(request,consultation_id):
    if request.method == 'GET':
        request.session['consultation_id'] = consultation_id
        consultation_obj = consultation.objects.get(id=consultation_id)

        
        
        return render(request,'consultation/consultation.html', {"consultation":consultation_obj})

   #  if request.method == 'POST':
   #    return render(request,'consultation/consultation.html' )





def rate_review(request,consultation_id):
   if request.method == "POST":
         
         consultation_obj = consultation.objects.get(id=consultation_id)
         patient = consultation_obj.patient
         doctor1 = consultation_obj.doctor
         rating = request.POST.get('rating')
         review = request.POST.get('review')

         rating_obj = rating_review(patient=patient,doctor=doctor1,rating=rating,review=review)
         rating_obj.save()

         
         messages.success(request, "Review Submitted Successfully")   
         return redirect('consultationview',consultation_id)
   



def close_consultation(request, consultation_id):
    if request.method == "POST":
        next_date_str = request.POST.get('next_consultation_date', None)

        if next_date_str:
            try:
                next_date = datetime.strptime(next_date_str, '%Y-%m-%d').date()
            except ValueError:
                next_date = None
        else:
            next_date = None

 
        consult = consultation.objects.get(id = consultation_id)

        consult.status = "closed"
        consult.next_consultation_date = next_date
        consult.save()

        patient_name = consult.patient.name if consult.patient else "Unknown Patient"
        messages.info(request, f"Consultation closed successfully for {patient_name}")

        return redirect('dconsultation_history')







#-----------------------------chatting system ---------------------------------------------------


def post(request):
    if request.method == "POST":
        msg = request.POST.get('msgbox', None)

        consultation_id = request.session['consultation_id'] 
        consultation_obj = consultation.objects.get(id=consultation_id)

        c = Chat(consultation_id=consultation_obj,sender=request.user, message=msg)

        #msg = c.user.username+": "+msg

        if msg != '':            
            c.save()  
            return JsonResponse({ 'msg': msg })
    else:
        return HttpResponse('Request must be POST.')





def chat_messages(request):
    if request.method == "GET":
        consultation_id = request.session['consultation_id']
        consultation_obj = consultation.objects.get(id=consultation_id)
        chat_objs = Chat.objects.filter(consultation_id=consultation_id).order_by('created')

        # Mark other user's 'delivered' messages as 'read'
        Chat.objects.filter(
            consultation_id=consultation_id,
            status='delivered'
        ).exclude(sender=request.user).update(status='read')

        # Grouping Logic: Add display_date to each message
        today = datetime.today().date()
        yesterday = today - timedelta(days=1)

        chat_list = []
        last_display_date = None

        for msg in chat_objs:
            created_date = msg.created.date()
            if created_date == today:
                display_date = "Today"
            elif created_date == yesterday:
                display_date = "Yesterday"
            else:
                display_date = created_date.strftime('%d %B %Y') 
            # Add a display_date tag only if the date changes
            show_date = display_date != last_display_date
            last_display_date = display_date

            chat_list.append({
                'obj': msg,
                'display_date': display_date if show_date else None,
                 'time_only': msg.created.strftime('%I:%M %p')   # For bubble time
            })

        return render(request, 'consultation/chat_body.html', {
            'chat': chat_list,
            'consultation': consultation_obj
        })
    

    


def check_messages(request):
    if not request.user.is_authenticated:
        return JsonResponse({"has_new": False})

    user = request.user

    new_messages = Chat.objects.filter(
        Q(consultation_id__doctor__user=user) | Q(consultation_id__patient__user=user),
        ~Q(sender=user),
        status='delivered',
        notified=False
    ).order_by('created')[:8]

    message_list = []

    for msg in new_messages:
       
        message_list.append({
            "id": msg.id,
            "sender": msg.sender.username,
            "preview": msg.message[:500],
            "timestamp": msg.created.isoformat()
        })
        msg.notified = True
        msg.save(update_fields=["notified"])

    # ✅ Always collect read message IDs (even if no new ones)
    read_ids = list(Chat.objects.filter(
        Q(consultation_id__doctor__user=user) | Q(consultation_id__patient__user=user),
        ~Q(sender=user),
        status='read',
        notified=True
    ).values_list('id', flat=True))

    return JsonResponse({
        "has_new": new_messages.exists(),
        "messages": message_list,
        "read_ids": read_ids
    })



def get_consultation_id_from_chat(request, chat_id):
    try:
        chat = Chat.objects.get(id=chat_id)
        consultation_id = chat.consultation_id.id

        related_ids = list(Chat.objects.filter(
            Q(consultation_id=chat.consultation_id) &
            Q(status='delivered') &
            ~Q(sender_id=request.user.id)
        ).values_list('id', flat=True))


        return JsonResponse({
            "consultation_id": consultation_id,
            "related_message_ids": related_ids
        })

    except Chat.DoesNotExist:
        return JsonResponse({"error": "Chat not found"}, status=404)



#-----------------------------chatting system ---------------------------------------------------


