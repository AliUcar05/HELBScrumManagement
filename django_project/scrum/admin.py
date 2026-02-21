from django.contrib import admin

from scrum.models import Project, Membership, Sprint, Ticket, SprintTicket

# Register your models here.
admin.site.register(Project)
admin.site.register(Membership)
admin.site.register(Sprint)
admin.site.register(Ticket)
admin.site.register(SprintTicket)





