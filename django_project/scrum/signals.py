from django.db.models.signals import post_save
from django.dispatch import receiver

from scrum.models import Project, Board, Column, Membership


@receiver(post_save, sender=Project)
def create_project_board(sender, instance, created, **kwargs):
    if not created:
        return

    board, _ = Board.objects.get_or_create(
        project=instance,
        defaults={"name": f"{instance.name} Board"}
    )

    existing_columns = set(board.columns.values_list("name", flat=True))
    default_columns = [
        ("To Do", 1),
        ("In Progress", 2),
        ("Done", 3),
    ]

    columns_to_create = []
    for column_name, order in default_columns:
        if column_name not in existing_columns:
            columns_to_create.append(
                Column(board=board, name=column_name, order=order)
            )

    if columns_to_create:
        Column.objects.bulk_create(columns_to_create)

    membership, _ = Membership.objects.get_or_create(
        user=instance.created_by,
        project=instance,
        defaults={"role": "admin"},
    )

    if membership.role != "admin":
        membership.role = "admin"
        membership.save(update_fields=["role"])