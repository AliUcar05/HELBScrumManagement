from django import forms
from django.contrib.auth.models import User

from scrum.models import Project

from .models import Notification, Profile


class AdminCreateUserForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
    )
    global_role = forms.ChoiceField(
        choices=Profile.GLOBAL_ROLES,
        initial="member",
        required=False,
    )
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        initial="developer",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def __init__(self, *args, can_assign_global_role=True, **kwargs):
        self.can_assign_global_role = can_assign_global_role
        super().__init__(*args, **kwargs)

        if not self.can_assign_global_role:
            self.fields["global_role"].initial = "member"
            self.fields["global_role"].widget = forms.HiddenInput()

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username already exists.")
        return username

    def clean_global_role(self):
        if not self.can_assign_global_role:
            return "member"

        value = self.cleaned_data.get("global_role") or "member"
        valid_values = {choice[0] for choice in Profile.GLOBAL_ROLES}
        return value if value in valid_values else "member"

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = (self.cleaned_data.get("username") or "").strip()
        user.email = (self.cleaned_data.get("email") or "").strip()
        user.first_name = (self.cleaned_data.get("first_name") or "").strip()
        user.last_name = (self.cleaned_data.get("last_name") or "").strip()
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            profile = user.profile
            profile.global_role = self.cleaned_data.get("global_role", "member")
            profile.role = self.cleaned_data["role"]
            profile.save()

        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "image",
            "remember_login",
            "phone",
            "location",
            "role",
            "job_title",
            "department",
            "supervisor",
        ]


class NotificationForm(forms.Form):
    AUDIENCE_SELECTED = "selected"
    AUDIENCE_PROJECT = "project_team"
    AUDIENCE_ALL = "all_users"

    AUDIENCE_CHOICES = [
        (AUDIENCE_SELECTED, "Selected users"),
        (AUDIENCE_PROJECT, "Project team members"),
        (AUDIENCE_ALL, "All users"),
    ]

    audience = forms.ChoiceField(
        choices=AUDIENCE_CHOICES,
        initial=AUDIENCE_SELECTED,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Choose who should receive the notification.",
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Required when sending an announcement to a project team.",
        empty_label="Select a project",
    )
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control", "size": 8}),
        help_text="Used only for the 'Selected users' option.",
    )
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Notification title"}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Write your message..."})
    )

    def __init__(self, *args, current_user=None, **kwargs):
        self.current_user = current_user
        super().__init__(*args, **kwargs)

        users_queryset = User.objects.all().select_related("profile").order_by("username")
        if current_user is not None:
            users_queryset = users_queryset.exclude(pk=current_user.pk)
        self.fields["recipients"].queryset = users_queryset

        projects_queryset = Project.objects.all().order_by("name")
        self.fields["project"].queryset = projects_queryset

    def _resolve_recipients(self):
        audience = self.cleaned_data.get("audience")
        selected_recipients = self.cleaned_data.get("recipients")
        project = self.cleaned_data.get("project")

        if audience == self.AUDIENCE_ALL:
            recipients_qs = self.fields["recipients"].queryset
        elif audience == self.AUDIENCE_PROJECT and project is not None:
            recipients_qs = User.objects.filter(memberships__project=project)
            if self.current_user is not None:
                recipients_qs = recipients_qs.exclude(pk=self.current_user.pk)
            recipients_qs = recipients_qs.select_related("profile").distinct().order_by("username")
        else:
            recipients_qs = selected_recipients or User.objects.none()

        return list(recipients_qs)

    def clean(self):
        cleaned_data = super().clean()
        audience = cleaned_data.get("audience")
        project = cleaned_data.get("project")

        if audience == self.AUDIENCE_PROJECT and not project:
            self.add_error("project", "Select a project to notify its team members.")

        if audience == self.AUDIENCE_SELECTED and not cleaned_data.get("recipients"):
            self.add_error("recipients", "Select at least one user.")

        if not self.errors:
            recipients = self._resolve_recipients()
            if not recipients:
                self.add_error(None, "No eligible recipients were found for this notification.")
            else:
                cleaned_data["resolved_recipients"] = recipients

        return cleaned_data

    def save(self, sender):
        recipients = self.cleaned_data.get("resolved_recipients") or self._resolve_recipients()

        notifications = [
            Notification(
                sender=sender,
                recipient=recipient,
                title=self.cleaned_data["title"].strip(),
                message=self.cleaned_data["message"].strip(),
            )
            for recipient in recipients
        ]

        return Notification.objects.bulk_create(notifications)