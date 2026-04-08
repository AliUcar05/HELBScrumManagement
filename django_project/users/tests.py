from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from scrum.models import Membership, Project

from .models import Notification

User = get_user_model()

TEST_DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


@override_settings(DATABASES=TEST_DATABASES)
class UserAdministrationAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.make_user("platform_admin", "admin")
        self.member = self.make_user("regular_member", "member")
        self.other_member = self.make_user("second_member", "member")
        self.outsider = self.make_user("outsider_member", "member")

        self.project = Project.objects.create(
            name="Apollo",
            code="APOLLO",
            description="Project used for notification tests.",
            start_date="2026-04-01",
            created_by=self.admin,
        )
        Membership.objects.create(user=self.admin, project=self.project, role="admin")
        Membership.objects.create(user=self.member, project=self.project, role="contributor")
        Membership.objects.create(user=self.other_member, project=self.project, role="read-only")

    def make_user(self, username, global_role):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="pass1234!",
        )
        user.profile.global_role = global_role
        user.profile.save()
        return user

    def test_admin_can_open_create_user_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("create-user"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create User")

    def test_non_admin_cannot_open_create_user_page(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("create-user"))
        self.assertEqual(response.status_code, 302)

    def test_admin_sees_user_management_links(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("manage-users"))
        self.assertContains(response, reverse("create-user"))

    def test_non_admin_does_not_see_user_management_links(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, reverse("manage-users"))
        self.assertNotContains(response, reverse("create-user"))

    def test_admin_can_send_notification_to_selected_users(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("manage-users"),
            {
                "action": "send_notification",
                "audience": "selected",
                "title": "Sprint update",
                "message": "The sprint review starts at 15:00.",
                "recipients": [self.member.id],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(recipient=self.member).count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.other_member).count(), 0)
        self.assertContains(response, "Notification sent to 1 user.")

    def test_admin_can_send_notification_to_project_team(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("manage-users"),
            {
                "action": "send_notification",
                "audience": "project_team",
                "project": self.project.id,
                "title": "Project announcement",
                "message": "Demo tomorrow at 10:00.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(recipient=self.member, title="Project announcement").count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.other_member, title="Project announcement").count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.outsider, title="Project announcement").count(), 0)
        self.assertContains(response, "Notification sent to 2 users.")

    def test_admin_can_send_notification_to_all_users(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("manage-users"),
            {
                "action": "send_notification",
                "audience": "all_users",
                "title": "Global maintenance",
                "message": "The platform will be unavailable tonight.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(title="Global maintenance").count(), 3)
        self.assertEqual(Notification.objects.filter(recipient=self.member, title="Global maintenance").count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.other_member, title="Global maintenance").count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.outsider, title="Global maintenance").count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.admin, title="Global maintenance").count(), 0)
        self.assertContains(response, "Notification sent to 3 users.")

    def test_user_only_sees_their_own_notifications(self):
        Notification.objects.create(
            sender=self.admin,
            recipient=self.member,
            title="Release deployed",
            message="Production deployment completed.",
        )
        Notification.objects.create(
            sender=self.admin,
            recipient=self.other_member,
            title="Private note",
            message="Only for the second member.",
        )

        self.client.force_login(self.member)
        response = self.client.get(reverse("notifications-list"))

        self.assertContains(response, "Release deployed")
        self.assertNotContains(response, "Private note")

    def test_mark_all_notifications_read(self):
        Notification.objects.create(
            sender=self.admin,
            recipient=self.member,
            title="Reminder",
            message="Daily sync in 10 minutes.",
        )
        Notification.objects.create(
            sender=self.admin,
            recipient=self.member,
            title="Backlog",
            message="Backlog grooming moved to tomorrow.",
        )

        self.client.force_login(self.member)
        response = self.client.post(reverse("notifications-mark-all-read"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(recipient=self.member, is_read=False).count(), 0)
        self.assertContains(response, "All notifications have been marked as read.")