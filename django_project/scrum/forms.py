from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Membership, Project, Sprint, Ticket


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "code",
            "description",
            "image",
            "board_type",
            "project_type",
            "effort_unit",
            "sprint_duration",
            "start_date",
            "end_date",
        ]
        widgets = {
            "image": forms.FileInput(),
            "project_type": forms.Select(),
            "description": forms.Textarea(attrs={"rows": 3}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]
        self.fields["end_date"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]
        self.fields["name"].widget.attrs.update({"placeholder": "Project Name"})
        self.fields["code"].widget.attrs.update({"placeholder": "Project Code"})
        self.fields["board_type"].disabled = True


class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["user", "role", "team_role"]

    def __init__(self, *args, project=None, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

        User = get_user_model()
        queryset = User.objects.all().select_related("profile").order_by("username")

        if project is not None:
            queryset = queryset.exclude(
                id__in=project.members.values_list("id", flat=True)
            )

        if current_user is not None:
            queryset = queryset.exclude(id=current_user.id)

        self.fields["user"].queryset = queryset
        self.fields["user"].empty_label = "— Select a user —"

    def clean_user(self):
        user = self.cleaned_data.get("user")

        if user is None:
            raise forms.ValidationError("Please select a user.")

        if self.project is not None and self.project.members.filter(pk=user.pk).exists():
            raise forms.ValidationError("This user is already a member of the project.")

        return user


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            "title",
            "description",
            "type",
            "priority",
            "story_points",
            "assignee",
            "parent",
            "labels",
            "start_date",
            "due_date",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe the issue…"}),
            "story_points": forms.NumberInput(attrs={"min": 0, "max": 100, "placeholder": "e.g. 3"}),
            "title": forms.TextInput(attrs={"placeholder": "Issue title…"}),
            "labels": forms.TextInput(attrs={"placeholder": "frontend, auth, bug…"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"placeholder": "What needs to be done?"})
        self.fields["title"].required = True
        self.fields["description"].required = False
        self.fields["story_points"].required = False
        self.fields["assignee"].required = False
        self.fields["parent"].required = False
        self.fields["labels"].required = False
        self.fields["start_date"].required = False
        self.fields["due_date"].required = False
        self.fields["parent"].empty_label = "— None —"
        self.fields["assignee"].empty_label = "— Unassigned —"


class TicketEditForm(TicketForm):
    class Meta(TicketForm.Meta):
        fields = TicketForm.Meta.fields + ["status"]


class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = ["name", "goals", "start_date", "end_date", "sprint_capacity"]
        widgets = {
            "goals": forms.Textarea(attrs={"rows": 3, "placeholder": "Sprint goal…"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "sprint_capacity": forms.NumberInput(attrs={"min": 0, "placeholder": "e.g. 40"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"placeholder": "Sprint 1…"})
        self.fields["name"].required = True
        self.fields["goals"].required = False
        self.fields["end_date"].required = False
        self.fields["sprint_capacity"].required = False


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        labels = {
            "content": "",
        }
        widgets = {
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Ajouter un commentaire ou une réponse...",
                "rows": 3,
                "style": "resize: none;",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)