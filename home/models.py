from django.conf import settings
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from ckeditor.fields import RichTextField
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import UniqueConstraint

# Create your models here.


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
    


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email



class Students(models.Model):

    name = models.CharField(max_length=100)
    college = models.CharField(max_length=200)
    dept = models.CharField(max_length=200)
    year = models.IntegerField(null=True,blank=True)
    # email = models.EmailField(verbose_name="email", max_length=60)
    email = models.ForeignKey(CustomUser, on_delete=models.CASCADE, unique=True)
    ph_no = PhoneNumberField(null=False, blank=False)
    is_approved = models.BooleanField(default=False)
    id_card = models.ImageField(upload_to='ID_Cards', null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def get_id_card_url(self):
        if self.id_card:
            return settings.MEDIA_URL + str(self.id_card)
        return None



class Events(models.Model):

    CATEGORY_CHOICES = [
        ('Technical', 'Technical'),
        ('Non-Technical', 'Non-Technical'),
        ('Cultural', 'Cultural'),
    ]
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='O')
    cordinator = models.ForeignKey(Students, on_delete=models.SET_NULL, blank=True, null=True)
    date = models.DateField()
    event_time = models.TimeField()
    venue = models.CharField(max_length=50)
    reg_fee = models.CharField(max_length=50)
    is_team = models.BooleanField(default=False)
    banner = models.ImageField(upload_to='Event_Banners', null=True, blank=True)
    poster = models.ImageField(upload_to='Event_Posters', null=True, blank=True)
    rules = RichTextField(blank=True, null=True)


    def __str__(self):
        return self.title



class FacultyIncharge(models.Model):

    fac_name = models.CharField(max_length=100)
    event_incharge = models.ForeignKey(Events, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.fac_name
    


class Registration(models.Model):

    event = models.ForeignKey(Events, on_delete=models.CASCADE, blank=True, null=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now=True) 
    is_reported = models.BooleanField(default=False)

    class Meta:
        # Enforce uniqueness of event-student pairs
        unique_together = ('event', 'student')


    def __str__(self):
        return f"{self.student.name} - {self.event.title}"
    


class Teams(models.Model):

    team_lead = models.ForeignKey(Students, on_delete=models.CASCADE, blank=True, null=True, related_name='lead_teams')
    team_member = models.ManyToManyField(Students, related_name='member_teams')
    event = models.ForeignKey(Events, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.team_lead.name}'s Team for {self.event.title}"
    


class Payment(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    event = models.ForeignKey(Events, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255)
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20)
    datetime = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.student.name} - {self.event.title} - Payment {self.id}"

    class Meta:
        # Add a unique constraint to ensure only one payment per student and event
        constraints = [
            UniqueConstraint(
                fields=['student', 'event'],
                name='unique_payment_for_student_and_event'
            )
        ]