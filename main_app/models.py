from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

from datetime import date

# Create your models here.


#user = models.OneToOneField(settings.AUTH_USER_MODEL)

class patient(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    
    is_patient = models.BooleanField(default=True)
    is_doctor = models.BooleanField(default=False)

    name = models.CharField(max_length = 50)
    dob = models.DateField()
    address = models.CharField(max_length = 100)
    mobile_no = models.CharField(max_length = 15)
    gender = models.CharField(max_length = 10)
    
    last_seen = models.DateTimeField(null=True, blank=True)

    
    @property
    def age(self):
        today = date.today()
        db = self.dob
        age = today.year - db.year
        if today.month < db.month or today.month == db.month and today.day < db.day:
            age -= 1
        return age 



class doctor(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    
    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=True)

    name = models.CharField(max_length = 50)
    dob = models.DateField()
    address = models.CharField(max_length = 100)
    mobile_no = models.CharField(max_length = 15)
    gender = models.CharField(max_length = 10)
    languages_known = models.CharField(max_length=100, default='English')

    registration_no = models.CharField(max_length = 20)
    year_of_registration = models.DateField()
    qualification = models.CharField(max_length = 100)
    State_Medical_Council = models.CharField(max_length = 100)

    specialization = models.CharField(max_length = 100)

    rating = models.FloatField(default=0.0)

    last_seen = models.DateTimeField(null=True, blank=True)

    @property
    def age(self):
        today = date.today()
        db = self.dob
        age = today.year - db.year
        if today.month < db.month or today.month == db.month and today.day < db.day:
            age -= 1
        return age
    
    @property
    def experience_display(self):
        if self.year_of_registration:
            today = date.today()
            years = today.year - self.year_of_registration.year
            if (today.month, today.day) < (self.year_of_registration.month, self.year_of_registration.day):
                years -= 1
            if years <= 0:
                return "Less than 1 year experience"
            elif years == 1:
                return "1 year of experience"
            else:
                return f"{years}+ years of experience"
        return "Experience unavailable"




class diseaseinfo(models.Model):
    patient = models.ForeignKey(patient, null=True, on_delete=models.SET_NULL)
    diseasename = models.CharField(max_length=200)
    no_of_symp = models.IntegerField()
    symptomsname = ArrayField(models.CharField(max_length=200))
    confidence = models.DecimalField(max_digits=5, decimal_places=2)
    consultdoctor = models.CharField(max_length=200)


class drugrecommendation(models.Model):
    diseasename = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    precautions = models.TextField(null=True, blank=True)
    medications = models.TextField(null=True, blank=True)
    diet = models.TextField(null=True, blank=True)
    workout = models.TextField(null=True, blank=True)
    
    addedby = models.CharField(max_length=100, default="Healurix")

    updatedby = models.ForeignKey(
        doctor,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_drugrecommendations'
    )

    is_approved = models.BooleanField(default=False)
    approvedby = models.ForeignKey(
        doctor,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_drugrecommendations'
    )




class consultation(models.Model):

    patient = models.ForeignKey(patient ,null=True, on_delete=models.SET_NULL)
    doctor = models.ForeignKey(doctor ,null=True, on_delete=models.SET_NULL)
    diseaseinfo = models.ForeignKey(diseaseinfo, null=True, on_delete=models.SET_NULL)
    consultation_date = models.DateField()
    status = models.CharField(max_length = 20)

    last_consultation_date = models.DateField(blank=True, null=True)
    next_consultation_date = models.DateField(blank=True, null=True)



class prescription(models.Model):
    consultation = models.ForeignKey('consultation', on_delete=models.CASCADE)
    doctor = models.ForeignKey('doctor', null=True, on_delete=models.CASCADE)
    patient = models.ForeignKey('patient', null=True, on_delete=models.CASCADE)

    # Tablets: List of dicts with name, frequency, food, duration
    tablets = models.JSONField(default=list, blank=True)  # e.g. [{name, frequency, food, duration}]

    # Tests selected with food instructions: grouped by type
    tests = models.JSONField(default=dict, blank=True)  # e.g. {"xray": [{"name": "Chest", "food": "after"}]}

    issued_date = models.DateField(auto_now_add=True)

    # Seen status tracking
    patient_seen = models.BooleanField(default=False)
    doctor_seen = models.BooleanField(default=False)

    def __str__(self):
        return f"Prescription - {self.patient.name} ({self.consultation})"
    

    

class rating_review(models.Model):

    patient = models.ForeignKey(patient ,null=True, on_delete=models.SET_NULL)
    doctor = models.ForeignKey(doctor ,null=True, on_delete=models.SET_NULL)
    
    rating = models.FloatField()
    review = models.TextField( blank=True ) 

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.doctor:
            avg = rating_review.get_average_rating(self.doctor)
            self.doctor.rating = avg
            self.doctor.save(update_fields=['rating'])


    @classmethod
    def get_average_rating(cls, doctor_obj):
        reviews = cls.objects.filter(doctor=doctor_obj)
        if reviews.exists():
            total = sum([r.rating for r in reviews])
            return round(total / reviews.count(), 1)
        return 0