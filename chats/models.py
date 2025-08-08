from django.db import models
from django.contrib.auth.models import User
from main_app.models import consultation,patient, doctor

# Create your models here.

class Chat(models.Model):

    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]

    created = models.DateTimeField(auto_now_add=True)
    consultation_id =  models.ForeignKey(consultation, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    notified = models.BooleanField(default=False)


    def __unicode__(self):
        return self.message



class DoctorFeedback(models.Model):
    doctor = models.ForeignKey(doctor, on_delete=models.CASCADE)
    consultation = models.ForeignKey(consultation, on_delete=models.CASCADE)

    was_patient_clear = models.BooleanField(null=True)
    was_prediction_accurate = models.BooleanField(null=True)
    patient_followed_advice = models.BooleanField(null=True)

    suggestions = models.TextField(blank=True, null=True)
    comment = models.TextField()
    rating = models.FloatField()  
    
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Consultation #{self.consultation.id}"

    

class PatientFeedback(models.Model):
    patient = models.ForeignKey(patient, on_delete=models.CASCADE)
    consultation = models.ForeignKey(consultation, on_delete=models.CASCADE)

    was_chat_help = models.BooleanField(null=True)
    was_prediction_useful = models.BooleanField(null=True)
    patient_followed_advice = models.BooleanField(null=True)
    felt_more_confident = models.BooleanField(null=True)
    recommend_others = models.BooleanField(null=True)

    suggestions = models.TextField(blank=True, null=True)
    allow_public = models.BooleanField(default=False)
    rating = models.FloatField()  
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.patient} on consultation #{self.consultation.id}"
