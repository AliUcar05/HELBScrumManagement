from django.contrib import admin

from scrum.models import Project, Membership, Sprint, Ticket, SprintTicket, Column, Board

# Register your models here.
admin.site.register(Project)
admin.site.register(Membership)
admin.site.register(Sprint)
admin.site.register(Ticket)
admin.site.register(SprintTicket)
admin.site.register(Column)
admin.site.register(Board)





