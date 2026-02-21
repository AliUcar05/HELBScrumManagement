from django.db import models
from django.contrib.auth.models import User
from PIL import Image


class Profile(models.Model):

    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('scrum_master', 'Scrum Master'),
        ('product_owner', 'Product Owner'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    supervisor = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='subordinates')

    remember_login = models.BooleanField(default=False)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    current_failed_logins = models.IntegerField(default=0)


    def __str__(self):
        return f'{self.user.username} Profile'

    def get_full_name(self):
        return f'{self.user.last_name} {self.user.first_name}'.strip()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)