from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework import generics, permissions, viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.settings import api_settings
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.contrib.auth.views import PasswordResetCompleteView
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.db import IntegrityError, transaction
import razorpay
import json

from .models import *
from .serializers import *

# Create your views here.



# # razorpay client
# razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@csrf_exempt
@api_view(['GET'])
@permission_classes([permissions.DjangoModelPermissionsOrAnonReadOnly])
def student_list(request):
    students = Students.objects.all()
    serializer = StudentsSerializer(students, many=True)
    return Response(serializer.data)



class EventsList(APIView):
    queryset = Events.objects.all()
    def get(self, request, format=None):
        events = Events.objects.all()
        serializer = EventsSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request):
    user = request.user
    data = {'username': user.email}
    return Response(data)




class CustomUserCreateView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]




class CustomAuthTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super(CustomAuthTokenView, self).post(request, *args, **kwargs)
        token = response.data['token']
        user = CustomUser.objects.get(auth_token=token)
        return Response({'token': token, 'email': user.email})
    



class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, format=None):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        print(user)
        if user is not None:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            user_obj=CustomUser.objects.get(email=email)
            # student=Students.objects.get(email=user_obj)
            uname = None
            try:
                student=user_obj.students_set.first()
                uname = student.name 
            except:
                print("Student Profile not created") 
            print(student)
            return Response({'token': token.key, 'user_id':user.id,'user_name':uname,'success':True}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)




class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get the user's token
        token = request.auth
        # Delete the token
        token.delete()
        return Response({'message': 'Logged out successfully.'})




class StudentListCreateView(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Students.objects.all()
    serializer_class = StudentsSerializer

    def post(self, request, *args, **kwargs):
        # Print the received authentication token from frontend
        auth_token = request.auth
        print("Received authentication token:",auth_token)
        print(request.data)
        email=request.user
        user=CustomUser.objects.get(email=email)
        print(user)
        data = {
            'name': request.data.get('name'),
            'college': request.data.get('college'),
            'dept': request.data.get('dept'),
            'year': request.data.get('year'),
            'email': user, 
            'ph_no': request.data.get('ph_no'),
            # 'id_card': request.data.get('id_card'),
        }

        # Create a Student object
        student = Students(**data)
        student.save()
        # get id card file
        id_card_image = request.FILES.get('id_card')
        if id_card_image:
            # Save the ID card image
            student.id_card.save(id_card_image.name, id_card_image, save=True)
        student.save()
        return Response({"message": "Student object created successfully."})




class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
    queryset = Students.objects.all()
    serializer_class = StudentsSerializer

    def retrieve(self, request, *args, **kwargs):
        uid=self.kwargs['pk']
        custom_user=CustomUser.objects.get(pk=uid)
        instance=Students.objects.get(email=custom_user)
        print(instance.get_id_card_url())
        serializer = self.get_serializer(instance)
        print("Student Detail Response:", serializer.data)  # Print the response data
        return Response(serializer.data)




class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    queryset = CustomUser.objects.all()
    serializer_class = PasswordResetSerializer
    def post(self, request):
        print(request.data)
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            current_site = get_current_site(request)
            print(current_site, current_site.domain)
            mail_subject = 'Reset your password'
            message = (
                f"Hello {user.email},\n\n"
                f"Click the following link to reset your password:\n\n"
                f"{current_site.domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}\n\n"
                f"If you did not request a password reset, please ignore this email."
            )
            send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [email])
            return Response({'detail': 'Password reset email sent.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



# class CustomPasswordResetCompleteView(PasswordResetCompleteView):
#     def get(self, request, *args, **kwargs):
#         # Customize the success URL
#         nextjs_url = 'https://icon-ptucse.in/login'  # Replace with your Next.js URL
#         return redirect(nextjs_url)
    



class RegistrationCreateView(generics.CreateAPIView):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Access the data from the request here
        event_id = self.request.data.get('event')
        student_id = self.request.data.get('student')
        is_paid = self.request.data.get('is_paid')
        
        print("Received data from frontend:")
        print("Event ID:", event_id)
        print("Student ID:", student_id)
        print("Is Paid:", is_paid)
        
        # Continue with creating the instance using the serializer
        serializer.save()

    def post(self, request, *args, **kwargs):
        print("Received data from frontend:")
        print("Request data:", request.data)
        event = self.request.data.get('event')
        uid = self.request.data.get('student')
        # student_name=self.request.data.get('name')
        is_paid = self.request.data.get('is_paid')

        try:
            user_instance=CustomUser.objects.get(pk=uid)
            student_id=Students.objects.get(email=user_instance)

            event_instance=Events.objects.get(title=event)
            student_instance = Students.objects.get(pk=student_id.id)
            print(student_instance,type(student_instance),type(event_instance))
        except CustomUser.DoesNotExist:
                return JsonResponse({"error": "User and Profile does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Students.DoesNotExist:
                return JsonResponse({"error": "User and Profile does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Events.DoesNotExist:
                return JsonResponse({"error": "Event does not exist."}, status=status.HTTP_403_FORBIDDEN)

        try:
            registration=Registration(event=event_instance,student=student_instance)
            registration.save()
            team_id=None
            team_ld=None
            uname=None
            # Check if the event is a team event
            if event_instance.is_team:
                # Create a Teams instance with the student as team lead
                team_lead = student_instance
                new_team = Teams.objects.create(team_lead=team_lead, event=event_instance)
                new_team.team_member.add(student_instance)  # Add student as a team member
                team_id = new_team.pk   
                serializer_team = TeamsSerializer(new_team)
                team_ld = serializer_team.data.get("team_lead")
                uname = Students.objects.get(pk=team_ld)
                uname=uname.name
            serializer=RegistrationSerializer(registration)
            data = {"serializer": serializer.data, "team_id": team_id, "team_lead": uname}
            return Response(data,status=status.HTTP_201_CREATED)
        except IntegrityError:
        # Handle the case where a registration already exists for the given event and student
            return Response({"error": "Registration already exists for this event and student."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




class RegisteredEventsView(generics.ListAPIView):
    serializer_class = RegisteredEventSerializer

    def get_queryset(self):
        uid = self.kwargs['student_id']
        user_instance=CustomUser.objects.get(pk=uid)
        student_id=Students.objects.get(email=user_instance)
        queryset = Registration.objects.filter(student_id=student_id)
        return queryset




class EventsByCategoryView(generics.ListAPIView):
    serializer_class = EventsSerializer

    def get_queryset(self):
        # Get the category from the URL parameters
        category = self.kwargs['category']
        # Filter events by the category
        queryset = Events.objects.filter(category=category)
        return queryset




class TeamsListCreateView(generics.ListCreateAPIView):
    queryset = Teams.objects.all()
    serializer_class = TeamsSerializer

    def perform_create(self, serializer):
        team = serializer.save()  # Save the team
        # Create registration objects for each team member
        for member in team.team_member.all():
            Registration.objects.create(event=team.event, student=member)
        # If you want to return the created team along with its registrations in the response
        serializer.instance = team




class TeamMemberAddView(generics.UpdateAPIView):
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Teams.objects.get(pk=self.kwargs['pk'])
    

    def get_queryset(self):
        instance = self.get_object()
        event = instance.event
        team_members = instance.team_member.all()  # Existing team members
        lead_team_members = Teams.objects.filter(event=event).values_list('team_member', flat=True)  # Members of other teams
        # Exclude students who are already part of the existing team and other teams
        query_set = Students.objects.filter(
            ~Q(pk__in=team_members) & ~Q(pk__in=lead_team_members)
        )
        print(query_set)
        return query_set
    
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        queryset = self.get_queryset()
        serializer = StudentsSerializer(queryset, many=True)
        return Response(serializer.data)
    

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        print(instance)
        print(request.data)

        team_members_data = request.data.get("team_member", [])
        added_members = []

        for member_data in team_members_data:
            student_name = member_data.get("name")

        # student_name=request.data.get("team_member",{})[0].get("name")
            try:
                team_member=Students.objects.get(name=student_name)
            except Students.DoesNotExist:
                return Response({"message": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
            data_dict={"team_member":team_member.id}
            serializer = self.get_serializer(instance, data=data_dict, context={'instance': instance})
            try:
                serializer.is_valid(raise_exception=True)
                team_member = serializer.validated_data['team_member']
                Registration.objects.create(event=instance.event, student=team_member)
                instance.team_member.add(team_member)
                added_members.append(team_member.id)
            except IntegrityError:
                return Response({"message": "IntegrityError occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"message": f"Team members added successfully: {added_members}"}, status=status.HTTP_200_OK)





class TeamsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Teams.objects.all()
    serializer_class = TeamsSerializer





class EventTeamLeadView(generics.RetrieveAPIView):
    serializer_class = TeamsSerializer

    def get_queryset(self):
        uid = self.kwargs['student_id']
        user_instance=CustomUser.objects.get(pk=uid)
        student_id=Students.objects.get(email=user_instance)    
        event_id = self.kwargs['event_id']
        queryset = Teams.objects.filter(event=event_id, team_lead=student_id)
        return queryset

    def get(self, request, *args, **kwargs):
        uid = self.kwargs['student_id']
        user_instance=CustomUser.objects.get(pk=uid)
        student_id=Students.objects.get(email=user_instance)
        event_id = self.kwargs['event_id']

        try:
            student = Students.objects.get(id=student_id.id)
            event = Events.objects.get(id=event_id)
            team = Teams.objects.get(event=event, team_lead=student)
            serializer = self.get_serializer(team)
            return Response(serializer.data)
        except Students.DoesNotExist:
            return Response({"message": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
        except Events.DoesNotExist:
            return Response({"message": "Event not found or student is not the team lead"}, status=status.HTTP_404_NOT_FOUND)





class EventDetailView(generics.RetrieveAPIView):
    serializer_class = EventsSerializer

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        queryset = Events.objects.filter(id=event_id)
        return queryset

    def get(self, request, *aargs, **kwargs):
        event_id = self.kwargs['event_id']
        try:
            event = Events.objects.get(id=event_id)
            serializer = self.get_serializer(event)
            return Response(serializer.data)
        except Events.DoesNotExist:
            return Response({"message": "Event not found"}, status=status.HTTP_404_NOT_FOUND)





class RegisteredEventDetailView(generics.RetrieveAPIView):
    serializer_class = RegisteredEventSerializer

    def get_queryset(self):
        reg_id = self.kwargs['pk']
        queryset = Registration.objects.filter(id=reg_id)
        return queryset
    
    def get(self, *args, **kwargs):
        reg_id = self.kwargs['pk']
        reg_obj = Registration.objects.get(id=reg_id)
        reg_serializer = RegisteredEventSerializer(reg_obj)
        reg_data = reg_serializer.data
        event_obj = Events.objects.get(id=reg_obj.event.id)
        team_data = None
        if event_obj.is_team:
            team_obj = get_team_for_student_and_event(reg_obj.student, reg_obj.event)
            team_serializer = TeamMembersDetailSerializer(team_obj)
            team_data = team_serializer.data
        response = {"registration": reg_data, "team":team_data}
        return Response(response)

    


def get_team_for_student_and_event(student, event):
    try:
        # Check if the student is a team leader for the given event
        team = Teams.objects.get(event=event, team_lead=student)
        return team
    except Teams.DoesNotExist:
        try:
            # Check if the student is a team member for the given event
            team = Teams.objects.get(event=event, team_member=student)
            return team
        except Teams.DoesNotExist:
            return None


def get_reg_for_lead_and_event(lead, event):
    '''function to get reg id for redirecting to event detail page after adding team'''
    try:
        reg = Registration.objects.get(event=event, student=lead)
        return reg
    except Registration.DoesNotExist:
        return None



@csrf_exempt
@require_POST
def feedback(request):
    print(request)
    try:
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        message = data.get('feedback')
        # Send an email to notify you about the feedback
        subject = 'New Feedback Received'
        message = f'Name: {name}\nEmail: {email}\nMessage: {message}'
        from_email = email
        recipient_list = [settings.EMAIL_HOST_USER]  # Replace with your email address

        send_mail(subject, message, from_email, recipient_list)

        return JsonResponse({'message': 'Feedback submitted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    





# class RazorpayPaymentView(APIView):
#     permission_classes = [permissions.AllowAny]
#     def post(self, request, format=None):
#         print(request.data)
#         student_id = request.data.get('student_id')
#         event_id = request.data.get('event_id')
#         amount = request.data.get('amount')*100  # Amount in paisa
#         # Get the student and event
#         try:
#             student = Students.objects.get(pk=student_id)
#             event = Events.objects.get(pk=event_id)
#         except (Students.DoesNotExist, Events.DoesNotExist):
#             return Response({'error': 'Student or Event not found'}, status=status.HTTP_404_NOT_FOUND)

#         print(razorpay_client)
#         # Create an order
#         response = razorpay_client.order.create({'amount': amount, 'currency': 'INR'})

#         # Construct the Razorpay Gateway URL
#         razorpay_gateway_url = f'https://api.razorpay.com/v1/payment?order_id={response.get("id")}'

#         try:
#             payment = Payment.objects.get(student=student, event=event)
#             payment.order_id = response.get('id')
#             payment.amount = response.get('amount')
#             payment.currency = response.get('currency')
#             payment.status = 'Pending'  # You can set an initial status
#             try:
#                 payment.save()
#             except IntegrityError:
#                 # Handle the case where an IntegrityError occurs (unique constraint violated)
#                 # This could happen if a student retries payment
#                 pass

#         except Payment.DoesNotExist:
#             # If no payment object exists, create a new one
#             # Save payment details to the database
#             payment = Payment.objects.create(
#                 student=student,
#                 event=event,
#                 order_id=response.get('id'),
#                 amount=response.get('amount'),
#                 currency=response.get('currency'),
#                 status='Pending'  # You can set an initial status
#             )

#         event_serializer = EventsSerializer(event)
#         student_serializer = StudentsSerializer(student)
#         event_name = event_serializer.data.get("title")
#         student_name = student_serializer.data.get("name")

#         response_data = {
#                 "razorpay_gateway_url": razorpay_gateway_url,
#                 "callback_url": "https://api.icon-ptucse.in/api/callback",
#                 "razorpay_key": settings.RAZORPAY_KEY_ID,
#                 "order": response,
#                 "event_name": event_name,
#                 "student_name": student_name
#         }

#         print(response_data)
#         return Response(response_data, status=status.HTTP_200_OK)
    



# The data we get from Razorpay is given below:
# {
#   "razorpay_payment_id": "pay_29QQoUBi66xm2f",
#   "razorpay_order_id": "order_9A33XWu170gUtm",
#   "razorpay_signature": "9ef4dffbfd84f1318f6739a3ce19f9d85851857ae648f114332d8401e0949a3d"
# }


# @csrf_exempt
# def order_callback(request):
#     if request.method == "POST":
#         try:
#             body_data = request.body.decode('utf-8')
#             res_data = json.loads(body_data)['response']
#             data = json.loads(res_data)
#             if "razorpay_signature" in data:
#                 payment_verification = razorpay_client.utility.verify_payment_signature(data)
#                 if payment_verification:
#                     order_id = data['razorpay_order_id']
#                     payment_inst = Payment.objects.get(order_id=order_id)
#                     payment_inst.status="Success"
#                     payment_inst.save()
#                     event = payment_inst.event
#                     student = payment_inst.student
#                     reg_obj = Registration.objects.get(event=event.id, student=student.id)
#                     reg_obj.is_paid = True
#                     reg_obj.save()

#                     if event.is_team:
#                         team_member_ids = []
#                         # Check if the paying student is a team member
#                         team = Teams.objects.filter(event=event.id, team_member=student.id).first()
#                         print("team member pay", team)
#                         if team:
#                             # Include the team lead in the list of team members
#                             team_member_ids = team.team_member.values_list('id', flat=True)
#                             team_member_ids = list(team_member_ids)
#                             team_member_ids.append(team.team_lead.id)

#                         else:
#                             # Check if the paying student is a team lead
#                             team = Teams.objects.filter(event=event.id, team_lead=student.id).first()
#                             print("team lead pay", team)
#                             if team:
#                                 # Include all team members in the list, including the team lead
#                                 team_member_ids = team.team_member.values_list('id', flat=True)
#                                 team_member_ids = list(team_member_ids)
#                                 team_member_ids.append(student.id)  # Append the team lead's ID

#                          # Update the registration status for all team members
#                         if team_member_ids:
#                             with transaction.atomic():
#                                 Registration.objects.filter(event=event.id, student__in=team_member_ids).update(is_paid=True)

#                     return JsonResponse({"res":"success"})
#                     # Logic to perform is payment is successful
#                 else:
#                     return JsonResponse({"res":"failed"})
#                         # Logic to perform is payment is unsuccessful
#         except Exception as e:
#             # Handle exceptions (e.g., log the error)
#             return JsonResponse({"status": "error", "message": str(e)})

#     return JsonResponse({"status": "invalid_method"})




class TeamLeadRegDetailView(generics.RetrieveAPIView):
    '''Class for retriving reg detail of a team after adding team member for redirecting to event detail page'''
    queryset = Teams.objects.all()
    serializer_class = RegisteredEventSerializer  # Create this serializer

    def retrieve(self, request, *args, **kwargs):
        team_id = kwargs.get('pk')
        try:
            team = Teams.objects.get(pk=team_id)
        except Teams.DoesNotExist:
            return Response({"error": "Team not found"}, status=404)
        reg_obj = get_reg_for_lead_and_event(team.team_lead, team.event)
        serializer = self.get_serializer(reg_obj)
        return Response(serializer.data)


