from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [ 
    path('', student_list),
    path('get_user_data/', get_user_data, name='get-user'),

    path('signup/', CustomUserCreateView.as_view(), name='user-register'),
    # path('login/', CustomAuthTokenView.as_view(), name='user-login'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('logout/', LogoutView.as_view(), name='user-logout'),

    path('student/', StudentListCreateView.as_view(), name='student-list'),
    path('student/<int:pk>/', StudentDetailView.as_view(), name='student-detail'),

    path('api/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('password-reset-complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('register/', RegistrationCreateView.as_view(), name='register-event'),
    path('students/<int:student_id>/events/', RegisteredEventsView.as_view(), name='registered-events'),
    path('add-team-member/<int:pk>/', TeamMemberAddView.as_view(), name='add-team-member'),
    path('event-team-lead/<int:student_id>/<int:event_id>/', EventTeamLeadView.as_view(), name='event-team-lead'),

    path('teams/', TeamsListCreateView.as_view(), name='teams-list'),
    path('teams/<int:pk>/', TeamsDetailView.as_view(), name='teams-detail'),

    path('events/', EventsList.as_view(), name='event-names'),
    path('event-detail/<int:event_id>/', EventDetailView.as_view(), name='event-detail'),
    path('reg-detail/<int:pk>/', RegisteredEventDetailView.as_view(), name='reg-detail'),

    path('feedback/', feedback, name='feedback'),

    # path('api/razorpay/', RazorpayPaymentView.as_view(), name='razorpay'),
    # path('api/callback/', order_callback, name='razorpay_callback'),

    path('api/instamojo-payment/', InstamojoPaymentView.as_view(), name='instamojo-payment'),
    path('api/instamojo-callback/', instamojo_callback, name='instamojo-callback'),

    path('team-reg-detail/<int:pk>/', TeamLeadRegDetailView.as_view(), name='team-reg-detail'),
]