from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
from django.core.validators import FileExtensionValidator

from common.file.utils import GeneratePath
from common.validators import validate_file_size
from common.file.mixins import ImageProcessingMixin

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

class UserProfile(ImageProcessingMixin, models.Model):
    IMAGE_SIZE = (300, 300)
    class Role(models.TextChoices):
        STAFF = 'staff', 'персонал'
        CUSTOMER = 'customer', 'клієнт'

    user = models.OneToOneField('user.CustomUser', on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(choices=Role.choices, default=Role.CUSTOMER, max_length=150)
    date_of_birth = models.DateField('born', null=True, blank=True)
    profile_picture = models.ImageField(upload_to=GeneratePath('users'), 
                                        blank=True, null=True, max_length=300, 
                                        validators=[
                                            validate_file_size,
                                            FileExtensionValidator(allowed_extensions=[
                                                'jpeg', 'png', 'webp', 'jpg', 'svg'
                                            ], message='Invalid file extension')
                                            ])
        
    def __str__(self):
        return f'{self.user.username} ({self.role})'
    
