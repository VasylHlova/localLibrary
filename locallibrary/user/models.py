from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
from allauth.account.models import EmailAddress

class CustomUser(AbstractUser):
    email = models.EmailField('email address', unique=True)
    username = models.CharField(
        'username',
        max_length=150,
        unique=True,
        blank=True, 
        null=True,  
        help_text='Optional. 150 characters or fewer.'
    )

    first_name = models.CharField('first name', max_length=150, blank=False)
    last_name = models.CharField('last name', max_length=150, blank=False)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class UserProfile(models.Model):

    class Role(models.TextChoices):
        STAFF = 'staff', 'персонал'
        CUSTOMER = 'customer', 'клієнт'

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(choices=Role.choices, default=Role.CUSTOMER)
    date_of_birth = models.DateField('born', null=True, blank=True)
    email_verified_at = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='users/', blank=True, null=True)

    @property
    def is_verified(self):
        if self.user.is_authenticated:
            return EmailAddress.objects.filter(user=self.user, verified=True).exists()
        return False
        
    def __str__(self):
        return f'{self.user.username} ({self.role})'
