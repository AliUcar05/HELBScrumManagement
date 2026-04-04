from django.db import models
import os
from django.contrib.auth.models import User
from PIL import Image


class Profile(models.Model):

    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('scrum_master', 'Scrum Master'),
        ('product_owner', 'Product Owner'),
    ]


    GLOBAL_ROLES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]
    global_role = models.CharField(
        max_length=20,
        choices=GLOBAL_ROLES,
        default="member",
        help_text="Platform-wide role. Project-level access is managed via Membership."
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)

    role = models.CharField(max_length=20,choices=ROLE_CHOICES,default='developer',help_text="Default Scrum role of this user (can differ per project via Membership).")
    global_role = models.CharField(max_length=20,choices=GLOBAL_ROLES,default="member",help_text="Platform-wide role. Project-level access is managed via Membership.")
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    supervisor = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='subordinates')

    remember_login = models.BooleanField(default=False)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    current_failed_logins = models.IntegerField(default=0)

    last_activity = models.DateTimeField(('last activity'), auto_now=True)


    def __str__(self):
        return f'{self.user.username} ({self.get_global_role_display()})'


    @property
    def is_platform_admin(self):
        return self.global_role == "admin"

    @property
    def display_name(self):
        return self.get_full_name() or self.user.username

    def get_full_name(self):
        return f'{self.user.last_name} {self.user.first_name}'.strip()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

class Notification(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification to {self.recipient.username}: {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            from django.utils import timezone

            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])