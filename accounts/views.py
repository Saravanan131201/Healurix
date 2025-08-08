from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required

from main_app.models import patient , doctor
from chats.models import Chat
from datetime import datetime

# Create your views here.


   


def logout(request):

    auth_logout(request)
    request.session.pop('patientid', None)
    request.session.pop('doctorid', None)
    request.session.pop('adminid', None)
    
    return redirect('home')


@login_required
def update_last_seen(request):
    user = request.user
    if hasattr(user, 'patient'):
        user.patient.last_seen = now()
        user.patient.save()
    elif hasattr(user, 'doctor'):
        user.doctor.last_seen = now()
        user.doctor.save()
    return JsonResponse({'status': 'updated'})

 



def sign_in_admin(request):
  

    if request.method == 'POST':

          username =  request.POST.get('username')
          password =  request.POST.get('password')
 
          user = auth.authenticate(username=username,password=password)

          if user is not None :
             
              try:
                 if ( user.is_superuser == True ) :
                     auth.login(request,user)

                     return redirect('admin_ui')
               
              except :
                  messages.info(request,'Please enter the correct username and password for a admin account.')
                  return redirect('sign_in_admin')


          else :
             messages.info(request,'Please enter the correct username and password for a admin account.')
             return redirect('sign_in_admin')


    else :
      return render(request,'admin/signin/signin.html')



def signup_patient(request):


    if request.method == 'POST':
      
      if request.POST['username'] and request.POST['email'] and  request.POST['name'] and request.POST['dob'] and request.POST['gender'] and request.POST['address']and request.POST['mobile']and request.POST['password']and request.POST['password1'] :

          username =  request.POST['username']
          email =  request.POST['email']

          name =  request.POST['name']
          dob =  request.POST['dob']
          gender =  request.POST['gender']
          address =  request.POST['address']
          mobile_no = request.POST['mobile']
          password =  request.POST.get('password')
          password1 =  request.POST.get('password1')

          if password == password1:
              if User.objects.filter(username = username).exists():
                messages.info(request,'Username already taken')
                return redirect('signup_patient')

              elif User.objects.filter(email = email).exists():
                messages.info(request,'Email already taken')
                return redirect('signup_patient')
                
              else :
                user = User.objects.create_user(username=username,password=password,email=email)   
                user.save()
                
                patientnew = patient(user=user,name=name,dob=dob,gender=gender,address=address,mobile_no=mobile_no)
                patientnew.save()
                messages.success(request,'User created sucessfully')

                
              return redirect('sign_in_patient')

          else:
            messages.info(request,'Password not matching, please try again')
            return redirect('signup_patient')

      else :
        messages.info(request,'Please make sure all required fields are filled out correctly')
        return redirect('signup_patient') 


    
    else :
      return render(request,'patient/signup_Form/signup.html')


def sign_in_patient(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            try:
                if user.patient.is_patient == True:
                    auth.login(request, user)

                    # chats logic
                    Chat.objects.filter(
                        consultation_id__patient__user=user,
                        status='sent'
                    ).exclude(sender=user).update(status='delivered')

                    request.session['patientusername'] = user.username
                    request.session['patientid'] = user.id

                    return redirect('patient_ui')
            except:
                messages.info(request, 'Invalid credentials')
                return redirect('sign_in_patient')
        else:
            messages.info(request, 'Invalid credentials')
            return redirect('sign_in_patient')
    else:
        return render(request, 'patient/signin_page/index.html')



def savepdata(request,patientusername):

  if request.method == 'POST':
    name =  request.POST['name']
    dob =  request.POST['dob']
    gender =  request.POST['gender']
    address =  request.POST['address']
    mobile_no = request.POST['mobile_no']

    dobdate = datetime.strptime(dob,'%Y-%m-%d')

    puser = User.objects.get(username=patientusername)

    patient.objects.filter(pk=puser.patient).update(name=name,dob=dobdate,gender=gender,address=address,mobile_no=mobile_no)

    return redirect('pviewprofile',patientusername)





#doctors account...........operations......
    

def signup_doctor(request):

    if request.method == 'GET':
    
       return render(request,'doctor/signup_Form/signup.html')


    if request.method == 'POST':
      
      if request.POST['username'] and request.POST['email'] and  request.POST['name'] and request.POST['dob'] and request.POST['gender'] and request.POST['address']and request.POST['mobile'] and request.POST['languages_known'] and request.POST['password']and request.POST['password1']  and  request.POST['registration_no'] and  request.POST['year_of_registration'] and  request.POST['qualification'] and  request.POST['State_Medical_Council'] and  request.POST['specialization'] :

          username =  request.POST['username']
          email =  request.POST['email']

          name =  request.POST['name']
          dob =  request.POST['dob']
          gender =  request.POST['gender']
          address =  request.POST['address']
          mobile_no = request.POST['mobile']
          languages_known = request.POST['languages_known']
          registration_no =  request.POST['registration_no']
          year_of_registration =  request.POST['year_of_registration']
          qualification =  request.POST['qualification']
          State_Medical_Council =  request.POST['State_Medical_Council']
          specialization =  request.POST['specialization']
          
          password =  request.POST.get('password')
          password1 =  request.POST.get('password1')

          if password == password1:
              if User.objects.filter(username = username).exists():
                messages.info(request,'Username already taken')
                return redirect('signup_doctor')

              elif User.objects.filter(email = email).exists():
                messages.info(request,'Email already taken')
                return redirect('signup_doctor')
                
              else :
                user = User.objects.create_user(username=username,password=password,email=email)   
                user.save()
                
                doctornew = doctor( 
                   user=user, 
                   name=name, 
                   dob=dob,
                   gender=gender, 
                   address=address, 
                   mobile_no=mobile_no, 
                   languages_known = languages_known,
                   registration_no=registration_no, 
                   year_of_registration=year_of_registration, 
                   qualification=qualification, 
                   State_Medical_Council=State_Medical_Council, 
                   specialization=specialization )
                
                doctornew.save()

                messages.success(request,'User created sucessfully')
                print("doctorcreated")
                
              return redirect('sign_in_doctor')

          else:
            messages.info(request,'password not matching, please try again')
            return redirect('signup_doctor')

      else :
        messages.info(request,'Please make sure all required fields are filled out correctly')
        return redirect('signup_doctor') 





def sign_in_doctor(request):
    if request.method == 'GET':
        return render(request, 'doctor/signin_page/index.html')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            try:
                if user.doctor.is_doctor == True:
                    auth.login(request, user)

                    # chats logic
                    Chat.objects.filter(
                        consultation_id__doctor__user=user,
                        status='sent'
                    ).exclude(sender=user).update(status='delivered')


                    request.session['doctorusername'] = user.username
                    request.session['doctorid'] = user.id

                    return redirect('doctor_ui')
            except:
                messages.info(request, 'Invalid credentials')
                return redirect('sign_in_doctor')
        else:
            messages.info(request, 'Invalid credentials')
            return redirect('sign_in_doctor')




def saveddata(request,doctorusername):

  if request.method == 'POST':

    name =  request.POST['name']
    languages_known = request.POST['languages_known']
    dob =  request.POST['dob']
    gender =  request.POST['gender']
    address =  request.POST['address']
    mobile_no = request.POST['mobile_no']
    registration_no =  request.POST['registration_no']
    year_of_registration =  request.POST['year_of_registration']
    qualification =  request.POST['qualification']
    State_Medical_Council =  request.POST['State_Medical_Council']
    specialization =  request.POST['specialization']
    

    
    dobdate = datetime.strptime(dob,'%Y-%m-%d')
    yor = datetime.strptime(year_of_registration,'%Y-%m-%d')

    duser = User.objects.get(username=doctorusername)

    doctor.objects.filter(pk=duser.doctor).update( name=name, dob=dob, gender=gender, address=address, mobile_no=mobile_no, registration_no=registration_no, year_of_registration=yor, qualification=qualification, State_Medical_Council=State_Medical_Council, specialization=specialization, languages_known = languages_known )

    return redirect('dviewprofile',doctorusername)



def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            return redirect('reset_password', username=username)
        except User.DoesNotExist:
            messages.error(request, 'Invalid username')
    return render(request, 'forgot_password.html')


def reset_password(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'Invalid reset attempt')
        return redirect('forgot_password')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password == confirm_password:
            user.set_password(password)
            user.save()
            messages.success(request, "Password updated. Please log in.")
            return redirect('sign_in_patient')
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, 'reset_password.html', {'username': username})

