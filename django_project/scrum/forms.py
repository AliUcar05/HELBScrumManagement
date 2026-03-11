from django import forms

from .models import Project, Membership, Ticket


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
        fields = ["user", "role"]


#Ticket form
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            "title",
            "description",
            "type",
            "priority",
            "status",
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

        self.fields["status"].initial = "todo"



class TicketEditForm(TicketForm):
    class Meta(TicketForm.Meta):
        fields = TicketForm.Meta.fields + ["status"]
