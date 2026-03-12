from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from scrum.models import Membership, Project, Ticket

User = get_user_model()


class ScrumTicketBaseTestCase(TestCase):
    def make_user(self, username, global_role="member"):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="pass1234!",
        )
        user.profile.global_role = global_role
        user.profile.save()
        return user

    def make_project(self, created_by, code="TEST"):
        return Project.objects.create(
            name=f"Project {code}",
            code=code,
            description="",
            board_type="scrum",
            project_type="software",
            start_date=date.today(),
            created_by=created_by,
        )

    def make_membership(self, user, project, role):
        membership, _ = Membership.objects.update_or_create(
            user=user,
            project=project,
            defaults={"role": role},
        )
        return membership

    def make_ticket(self, project, requester, title, backlog_order):
        return Ticket.objects.create(
            project=project,
            requester=requester,
            title=title,
            type="user story",
            status="todo",
            priority="medium",
            backlog_order=backlog_order,
        )


class BacklogReorderTests(ScrumTicketBaseTestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.make_user("admin_user", global_role="admin")
        self.contributor = self.make_user("contributor_user")
        self.read_only = self.make_user("readonly_user")

        self.project = self.make_project(self.admin, code="BLG")
        self.make_membership(self.admin, self.project, "admin")
        self.make_membership(self.contributor, self.project, "contributor")
        self.make_membership(self.read_only, self.project, "read-only")

        self.ticket_1 = self.make_ticket(self.project, self.admin, "First issue", 1)
        self.ticket_2 = self.make_ticket(self.project, self.admin, "Second issue", 2)
        self.ticket_3 = self.make_ticket(self.project, self.admin, "Third issue", 3)

        self.backlog_url = reverse("product-backlog", kwargs={"pk": self.project.pk})

    def ordered_titles(self):
        return list(
            Ticket.objects.filter(project=self.project)
            .order_by("backlog_order", "created_at")
            .values_list("title", flat=True)
        )

    def test_admin_can_move_issue_up(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "ticket-reorder",
                kwargs={"pk": self.project.pk, "ticket_pk": self.ticket_2.pk, "direction": "up"},
            )
        )

        self.assertRedirects(response, self.backlog_url)
        self.assertEqual(self.ordered_titles(), ["Second issue", "First issue", "Third issue"])

    def test_contributor_can_move_issue_down(self):
        self.client.force_login(self.contributor)
        response = self.client.post(
            reverse(
                "ticket-reorder",
                kwargs={"pk": self.project.pk, "ticket_pk": self.ticket_2.pk, "direction": "down"},
            )
        )

        self.assertRedirects(response, self.backlog_url)
        self.assertEqual(self.ordered_titles(), ["First issue", "Third issue", "Second issue"])

    def test_read_only_cannot_reorder_backlog(self):
        self.client.force_login(self.read_only)
        response = self.client.post(
            reverse(
                "ticket-reorder",
                kwargs={"pk": self.project.pk, "ticket_pk": self.ticket_2.pk, "direction": "up"},
            )
        )

        self.assertRedirects(response, self.backlog_url)
        self.assertEqual(self.ordered_titles(), ["First issue", "Second issue", "Third issue"])

    def test_first_issue_cannot_move_up(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "ticket-reorder",
                kwargs={"pk": self.project.pk, "ticket_pk": self.ticket_1.pk, "direction": "up"},
            )
        )

        self.assertRedirects(response, self.backlog_url)
        self.assertEqual(self.ordered_titles(), ["First issue", "Second issue", "Third issue"])

    def test_backlog_page_shows_expected_reorder_buttons(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.backlog_url)

        up_for_first = reverse(
            "ticket-reorder",
            kwargs={"pk": self.project.pk, "ticket_pk": self.ticket_1.pk, "direction": "up"},
        )
        down_for_last = reverse(
            "ticket-reorder",
            kwargs={"pk": self.project.pk, "ticket_pk": self.ticket_3.pk, "direction": "down"},
        )
        up_for_middle = reverse(
            "ticket-reorder",
            kwargs={"pk": self.project.pk, "ticket_pk": self.ticket_2.pk, "direction": "up"},
        )
        down_for_middle = reverse(
            "ticket-reorder",
            kwargs={"pk": self.project.pk, "ticket_pk": self.ticket_2.pk, "direction": "down"},
        )

        self.assertNotContains(response, up_for_first)
        self.assertNotContains(response, down_for_last)
        self.assertContains(response, up_for_middle)
        self.assertContains(response, down_for_middle)

    def test_read_only_backlog_page_does_not_show_reorder_buttons(self):
        self.client.force_login(self.read_only)
        response = self.client.get(self.backlog_url)

        self.assertFalse(response.context["can_reorder"])
        self.assertNotContains(response, "ticket-reorder")

    def test_new_ticket_is_added_at_end_of_backlog(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("ticket-create", kwargs={"pk": self.project.pk}),
            {
                "title": "Newest issue",
                "description": "",
                "type": "user story",
                "priority": "medium",
                "story_points": "",
                "assignee": "",
                "parent": "",
                "labels": "",
                "start_date": "",
                "due_date": "",
                "status": "blocked",
            },
        )

        self.assertRedirects(response, self.backlog_url)
        new_ticket = Ticket.objects.get(title="Newest issue")
        self.assertEqual(new_ticket.backlog_order, 4)
        self.assertEqual(new_ticket.status, "todo")