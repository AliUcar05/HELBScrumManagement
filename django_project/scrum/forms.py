from django import forms
from django.contrib.auth.models import User

from .models import Project, Membership


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'code',
            'description',
            'image',
            'board_type',
            'project_type',
            'effort_unit',
            'sprint_duration',
            'global_capacity',
            'start_date',
            'end_date',
        ]
        widgets = {
            "image": forms.FileInput(),
            "board_type": forms.Select(),
            "project_type": forms.Select(),
            "description": forms.Textarea(attrs={"rows": 3}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Autoriser aussi la saisie manuelle en FR (dd/mm/yyyy)
        self.fields["start_date"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]
        self.fields["end_date"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]
        self.fields["name"].widget.attrs.update({"placeholder": "Project Name"})
        self.fields["code"].widget.attrs.update({"placeholder": "Project Code"})

#===============================================
#                   MEMBERSHIP FORM
#===============================================
class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["user", "role", "capacity_per_sprint"]