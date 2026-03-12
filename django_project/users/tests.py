from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserAdministrationAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.make_user("platform_admin", "admin")
        self.member = self.make_user("regular_member", "member")

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