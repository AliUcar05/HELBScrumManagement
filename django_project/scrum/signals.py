# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from scrum.models import Project, Board, Column, Membership


# =====================================================
# CREATE BOARD AUTOMATICALLY WHEN PROJECT IS CREATED
# =====================================================
@receiver(post_save, sender=Project)
def create_project_board(sender, instance, created, **kwargs):

    if created:
        board = Board.objects.create(
            project=instance,
            name=f"{instance.name} Board"
        )

        Column.objects.bulk_create([
            Column(board=board, name="To Do", order=1),
            Column(board=board, name="In Progress", order=2),
            Column(board=board, name="Done", order=3),
        ])

        Membership.objects.create(
            user=instance.created_by,
            project=instance,
            role="admin",
        )