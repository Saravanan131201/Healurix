from django.shortcuts import render , redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from .models import Chat , DoctorFeedback, PatientFeedback
from main_app.views import patient_ui, doctor_ui
from main_app.models import patient , doctor, consultation

from django.contrib.auth.models import User 

from django.contrib import messages

# Create your views here.


def parse_boolean(value):
    if value == "yes":
        return True
    elif value == "no":
        return False
    return None



def post_patient_feedback(request):
    if request.method == "POST":
        try:
            consultation_id = request.POST.get("consultation_id")
            consultation_obj = consultation.objects.get(id=consultation_id)

            was_chat_help = parse_boolean(request.POST.get("was_chat_help"))
            was_prediction_useful = parse_boolean(request.POST.get("was_prediction_useful"))
            patient_followed_advice = parse_boolean(request.POST.get("patient_followed_advice"))
            felt_more_confident = parse_boolean(request.POST.get("felt_more_confident"))
            recommend_others = parse_boolean(request.POST.get("recommend_others"))
            allow_public = request.POST.get("allow_public") == "on" 

            suggestions = request.POST.get("suggestions", "").strip()
            rating = request.POST.get("rating")

            PatientFeedback.objects.create(
                patient=request.user.patient,
                consultation=consultation_obj,
                was_chat_help=was_chat_help,
                was_prediction_useful=was_prediction_useful,
                patient_followed_advice=patient_followed_advice,
                felt_more_confident=felt_more_confident,
                recommend_others=recommend_others,
                suggestions=suggestions,
                allow_public=allow_public,
                rating=rating
            )

            messages.success(request, "Feedback submitted successfully.")
            return JsonResponse({'message': 'Feedback submitted successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)



def post_doctor_feedback(request):
    if request.method == "POST":
        try:
            consultation_id = request.POST.get("consultation_id")
            consultation_obj = consultation.objects.get(id=consultation_id)

            if not consultation_id:
                return JsonResponse({'error': 'Consultation ID is missing.'}, status=400)

            was_patient_clear = parse_boolean(request.POST.get("was_patient_clear"))
            was_prediction_accurate = parse_boolean(request.POST.get("was_prediction_accurate"))
            patient_followed_advice = parse_boolean(request.POST.get("patient_followed_advice"))

            suggestions = request.POST.get("suggestions", "").strip()
            comment = request.POST.get("comment", "").strip()
            rating = request.POST.get("rating")

            DoctorFeedback.objects.create(
                consultation=consultation_obj,
                doctor=request.user.doctor,
                was_patient_clear=was_patient_clear,
                was_prediction_accurate=was_prediction_accurate,
                patient_followed_advice=patient_followed_advice,
                suggestions=suggestions or None,
                comment=comment,
                rating=rating
            )

            messages.success(request, "Feedback submitted successfully.")
            return JsonResponse({'message': 'Feedback submitted successfully.'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)








#-----------------------------chatting system ---------------------------------------------------


# def post(request):
#     if request.method == "POST":
#         msg = request.POST.get('msgbox', None)

#         consultation_id = request.session['consultation_id'] 
#         consultation_obj = consultation.objects.get(id=consultation_id)

#         c = Chat(consultation_id=consultation_obj,sender=request.user, message=msg)

#         #msg = c.user.username+": "+msg

#         if msg != '':            
#             c.save()
#             print("msg saved"+ msg )
#             return JsonResponse({ 'msg': msg })
#     else:
#         return HttpResponse('Request must be POST.')



# def messages(request):
#    if request.method == "GET":

#          consultation_id = request.session['consultation_id'] 

#          c = Chat.objects.filter(consultation_id=consultation_id)
#          return render(request, 'consultation/chat_body.html', {'chat': c})
