"""
tests_ticket.py
===============
Tests pour TicketForm, TicketEditForm et les views Ticket (CRUD).

Structure :
  1. Factories / helpers
  2. TicketFormTest          — tests du formulaire de création
  3. TicketEditFormTest      — tests du formulaire d'édition
  4. TicketCreateViewTest    — tests de la vue de création (GET / POST)
  5. TicketListViewTest      — tests de la vue liste
  6. TicketDetailViewTest    — tests de la vue détail
  7. TicketUpdateViewTest    — tests de la vue mise à jour
  8. TicketDeleteViewTest    — tests de la vue suppression

Lancer les tests :
    python manage.py test yourapp.tests_ticket
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# ── Adapte ces imports à ton app ────────────────────────────────────────────
from yourapp.models import Project, Membership, Ticket, Sprint
from yourapp.forms import TicketForm, TicketEditForm
# ────────────────────────────────────────────────────────────────────────────

User = get_user_model()


# ===========================================================================
# 1. HELPERS
# ===========================================================================

def make_user(username="user", password="pass1234!"):
    """Crée un utilisateur simple."""
    return User.objects.create_user(username=username, password=password)


def make_project(created_by, name="Test Project", code="TEST"):
    """Crée un projet minimal."""
    from datetime import date
    return Project.objects.create(
        name=name,
        code=code,
        created_by=created_by,
        start_date=date.today(),
    )


def make_membership(user, project, role="contributor"):
    """Ajoute un membre au projet avec le rôle donné."""
    return Membership.objects.create(user=user, project=project, role=role)


def make_ticket(project, requester, title="A ticket", ticket_type="user story", **kwargs):
    """Crée un ticket minimal."""
    return Ticket.objects.create(
        project=project,
        requester=requester,
        title=title,
        type=ticket_type,
        status="todo",
        **kwargs,
    )


# ===========================================================================
# 2. TICKETFORM — tests du formulaire de création
# ===========================================================================

class TicketFormTest(TestCase):

    def setUp(self):
        self.owner = make_user("owner")
        self.project = make_project(self.owner)
        make_membership(self.owner, self.project, role="admin")

    def _base_data(self, **overrides):
        data = {
            "title": "Mon ticket",
            "description": "",
            "type": "user story",
            "priority": "medium",
            "story_points": "",
            "assignee": "",
            "parent": "",
        }
        data.update(overrides)
        return data

    # ── Validité ────────────────────────────────────────────────────────────

    def test_form_valid_minimal(self):
        """Seul le titre est obligatoire."""
        form = TicketForm(data=self._base_data())
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_valid_full(self):
        """Formulaire valide avec tous les champs remplis."""
        member = make_user("member")
        make_membership(member, self.project)
        parent_ticket = make_ticket(self.project, self.owner, title="Parent Epic", ticket_type="epic")

        form = TicketForm(data=self._base_data(
            title="Sous-ticket",
            description="Une description",
            type="task",
            priority="high",
            story_points=5,
            assignee=member.pk,
            parent=parent_ticket.pk,
        ))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertTrue(form.is_valid(), form.errors)

    # ── Champ title ─────────────────────────────────────────────────────────

    def test_form_invalid_without_title(self):
        """Le titre est requis."""
        form = TicketForm(data=self._base_data(title=""))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    # ── Champs optionnels ────────────────────────────────────────────────────

    def test_form_description_optional(self):
        """description est optionnelle."""
        form = TicketForm(data=self._base_data(description=""))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_story_points_optional(self):
        """story_points est optionnel."""
        form = TicketForm(data=self._base_data(story_points=""))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_assignee_optional(self):
        """assignee est optionnel."""
        form = TicketForm(data=self._base_data(assignee=""))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_parent_optional(self):
        """parent est optionnel."""
        form = TicketForm(data=self._base_data(parent=""))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertTrue(form.is_valid(), form.errors)

    # ── Choix invalides ──────────────────────────────────────────────────────

    def test_form_invalid_type(self):
        """Un type inconnu doit être rejeté."""
        form = TicketForm(data=self._base_data(type="unknowntype"))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertFalse(form.is_valid())
        self.assertIn("type", form.errors)

    def test_form_invalid_priority(self):
        """Une priorité inconnue doit être rejetée."""
        form = TicketForm(data=self._base_data(priority="critical"))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertFalse(form.is_valid())
        self.assertIn("priority", form.errors)

    # ── Queryset sécurité ────────────────────────────────────────────────────

    def test_form_rejects_assignee_outside_project(self):
        """Un user non membre ne peut pas être assigné."""
        outsider = make_user("outsider")
        form = TicketForm(data=self._base_data(assignee=outsider.pk))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertFalse(form.is_valid())
        self.assertIn("assignee", form.errors)

    def test_form_rejects_parent_outside_project(self):
        """Un ticket d'un autre projet ne peut pas être parent."""
        other_user = make_user("other")
        other_project = make_project(other_user, name="Other", code="OTH")
        alien_ticket = make_ticket(other_project, other_user, title="Alien ticket")

        form = TicketForm(data=self._base_data(parent=alien_ticket.pk))
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertFalse(form.is_valid())
        self.assertIn("parent", form.errors)

    # ── Labels vides ─────────────────────────────────────────────────────────

    def test_empty_label_assignee(self):
        """Le label vide pour assignee doit être '— Unassigned —'."""
        form = TicketForm()
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertEqual(form.fields["assignee"].empty_label, "— Unassigned —")

    def test_empty_label_parent(self):
        """Le label vide pour parent doit être '— None —'."""
        form = TicketForm()
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.all()
        self.assertEqual(form.fields["parent"].empty_label, "— None —")


# ===========================================================================
# 3. TICKETEDITFORM — tests du formulaire d'édition
# ===========================================================================

class TicketEditFormTest(TestCase):

    def setUp(self):
        self.owner = make_user("owner_edit")
        self.project = make_project(self.owner, code="EDIT")
        make_membership(self.owner, self.project, role="admin")
        self.ticket = make_ticket(self.project, self.owner)

    def _base_data(self, **overrides):
        data = {
            "title": "Ticket édité",
            "description": "",
            "type": "task",
            "priority": "low",
            "story_points": "",
            "assignee": "",
            "parent": "",
            "status": "in_progress",
        }
        data.update(overrides)
        return data

    def test_edit_form_has_status_field(self):
        """TicketEditForm doit contenir le champ status."""
        form = TicketEditForm()
        self.assertIn("status", form.fields)

    def test_create_form_has_no_status_field(self):
        """TicketForm (création) ne doit PAS contenir le champ status."""
        form = TicketForm()
        self.assertNotIn("status", form.fields)

    def test_edit_form_valid(self):
        """TicketEditForm est valide avec status renseigné."""
        form = TicketEditForm(data=self._base_data(), instance=self.ticket)
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.exclude(pk=self.ticket.pk)
        self.assertTrue(form.is_valid(), form.errors)

    def test_edit_form_invalid_status(self):
        """Un statut inconnu doit être rejeté."""
        form = TicketEditForm(data=self._base_data(status="flying"), instance=self.ticket)
        form.fields["assignee"].queryset = self.project.members.all()
        form.fields["parent"].queryset = self.project.tickets.exclude(pk=self.ticket.pk)
        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)

    def test_edit_form_parent_excludes_self(self):
        """Un ticket ne peut pas être son propre parent."""
        form = TicketEditForm(
            data=self._base_data(parent=self.ticket.pk),
            instance=self.ticket,
        )
        form.fields["assignee"].queryset = self.project.members.all()
        # La view exclut le ticket lui-même du queryset parent
        form.fields["parent"].queryset = self.project.tickets.exclude(pk=self.ticket.pk)
        self.assertFalse(form.is_valid())
        self.assertIn("parent", form.errors)


# ===========================================================================
# 4. TICKETCREATEVIEW — tests de la vue de création
# ===========================================================================

class TicketCreateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.owner = make_user("creator")
        self.project = make_project(self.owner, code="CRE")
        make_membership(self.owner, self.project, role="admin")
        self.url = reverse("ticket-create", kwargs={"pk": self.project.pk})

    def _post_data(self, **overrides):
        data = {
            "title": "Nouveau ticket",
            "description": "",
            "type": "user story",
            "priority": "medium",
            "story_points": "",
            "assignee": "",
            "parent": "",
        }
        data.update(overrides)
        return data

    # ── Accès ────────────────────────────────────────────────────────────────

    def test_redirect_if_not_logged_in(self):
        """Un anonyme est redirigé vers la page de connexion."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_get_returns_200_for_member(self):
        """Un membre (contributor) peut accéder au formulaire."""
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_forbidden_for_readonly(self):
        """Un membre read-only est redirigé (pas de permission)."""
        reader = make_user("reader")
        make_membership(reader, self.project, role="read-only")
        self.client.force_login(reader)
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("product-backlog", kwargs={"pk": self.project.pk}),
        )

    def test_get_forbidden_for_outsider(self):
        """Un utilisateur non membre est bloqué."""
        outsider = make_user("outsider_create")
        self.client.force_login(outsider)
        response = self.client.get(self.url)
        # Redirigé selon handle_no_permission
        self.assertIn(response.status_code, [302, 403])

    # ── POST valide ──────────────────────────────────────────────────────────

    def test_post_creates_ticket(self):
        """Un POST valide crée le ticket et redirige vers le backlog."""
        self.client.force_login(self.owner)
        response = self.client.post(self.url, self._post_data())
        self.assertRedirects(
            response,
            reverse("product-backlog", kwargs={"pk": self.project.pk}),
        )
        self.assertTrue(Ticket.objects.filter(title="Nouveau ticket").exists())

    def test_post_sets_reporter_and_project(self):
        """La view affecte automatiquement project et reporter."""
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data(title="Auto fields"))
        ticket = Ticket.objects.get(title="Auto fields")
        self.assertEqual(ticket.project, self.project)
        self.assertEqual(ticket.reporter, self.owner)

    def test_post_sets_status_todo(self):
        """La view impose status='todo' à la création."""
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data(title="Status check"))
        ticket = Ticket.objects.get(title="Status check")
        self.assertEqual(ticket.status, "todo")

    # ── POST invalide ────────────────────────────────────────────────────────

    def test_post_invalid_shows_form_again(self):
        """Un POST sans titre réaffiche le formulaire avec les erreurs."""
        self.client.force_login(self.owner)
        response = self.client.post(self.url, self._post_data(title=""))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket.objects.filter(title="").exists())

    # ── AJAX ─────────────────────────────────────────────────────────────────

    def test_ajax_post_valid_returns_json_success(self):
        """Un POST AJAX valide renvoie {"success": True}."""
        self.client.force_login(self.owner)
        response = self.client.post(
            self.url,
            self._post_data(title="AJAX ticket"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("ticket_id", data)

    def test_ajax_post_invalid_returns_json_errors(self):
        """Un POST AJAX invalide renvoie {"success": False, "errors": ...}."""
        self.client.force_login(self.owner)
        response = self.client.post(
            self.url,
            self._post_data(title=""),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("errors", data)

    # ── Contexte ─────────────────────────────────────────────────────────────

    def test_context_contains_project(self):
        """Le contexte contient le projet."""
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.context["project"], self.project)

    def test_context_form_title(self):
        """form_title doit valoir 'Create Issue'."""
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.context["form_title"], "Create Issue")


# ===========================================================================
# 5. TICKETLISTVIEW
# ===========================================================================

class TicketListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.owner = make_user("list_owner")
        self.project = make_project(self.owner, code="LST")
        make_membership(self.owner, self.project, role="admin")
        self.url = reverse("product-backlog", kwargs={"pk": self.project.pk})

    def test_redirect_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_member_can_access_list(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_outsider_cannot_access_list(self):
        outsider = make_user("outsider_list")
        self.client.force_login(outsider)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_tickets_appear_in_list(self):
        """Les tickets du projet apparaissent dans la liste."""
        make_ticket(self.project, self.owner, title="Ticket visible")
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertContains(response, "Ticket visible")

    def test_context_has_can_create_true_for_admin(self):
        """Un admin a can_create=True."""
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertTrue(response.context["can_create"])

    def test_context_has_can_create_false_for_readonly(self):
        """Un read-only a can_create=False."""
        reader = make_user("reader_list")
        make_membership(reader, self.project, role="read-only")
        self.client.force_login(reader)
        response = self.client.get(self.url)
        self.assertFalse(response.context["can_create"])

    def test_context_has_can_delete_true_for_admin(self):
        """Un admin a can_delete=True."""
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertTrue(response.context["can_delete"])

    def test_create_form_in_context(self):
        """Le contexte contient create_form pour la modal."""
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertIn("create_form", response.context)


# ===========================================================================
# 6. TICKETDETAILVIEW
# ===========================================================================

class TicketDetailViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.owner = make_user("detail_owner")
        self.project = make_project(self.owner, code="DET")
        make_membership(self.owner, self.project, role="admin")
        self.ticket = make_ticket(self.project, self.owner, title="Ticket détail")
        self.url = reverse(
            "ticket-detail",
            kwargs={"pk": self.project.pk, "ticket_pk": self.ticket.pk},
        )

    def test_redirect_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_member_can_view_detail(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_outsider_cannot_view_detail(self):
        outsider = make_user("outsider_detail")
        self.client.force_login(outsider)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_context_has_ticket(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.context["ticket"], self.ticket)

    def test_context_has_edit_form(self):
        """La view prépare le formulaire d'édition dans le contexte."""
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertIn("edit_form", response.context)
        self.assertIsInstance(response.context["edit_form"], TicketEditForm)

    def test_context_can_edit_for_admin(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertTrue(response.context["can_edit"])

    def test_context_cannot_edit_for_readonly(self):
        reader = make_user("reader_detail")
        make_membership(reader, self.project, role="read-only")
        self.client.force_login(reader)
        response = self.client.get(self.url)
        self.assertFalse(response.context["can_edit"])

    def test_children_in_context(self):
        """Les sous-tickets apparaissent dans children."""
        child = make_ticket(self.project, self.owner, title="Child ticket", parent=self.ticket)
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertIn(child, response.context["children"])


# ===========================================================================
# 7. TICKETUPDATEVIEW
# ===========================================================================

class TicketUpdateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.owner = make_user("update_owner")
        self.project = make_project(self.owner, code="UPD")
        make_membership(self.owner, self.project, role="admin")
        self.ticket = make_ticket(self.project, self.owner, title="Ticket à modifier")
        self.url = reverse(
            "ticket-update",
            kwargs={"pk": self.project.pk, "ticket_pk": self.ticket.pk},
        )

    def _post_data(self, **overrides):
        data = {
            "title": "Ticket modifié",
            "description": "Mise à jour",
            "type": "task",
            "priority": "high",
            "story_points": 3,
            "assignee": "",
            "parent": "",
            "status": "in_progress",
        }
        data.update(overrides)
        return data

    def test_redirect_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_readonly_cannot_edit(self):
        reader = make_user("reader_upd")
        make_membership(reader, self.project, role="read-only")
        self.client.force_login(reader)
        response = self.client.post(self.url, self._post_data())
        self.assertIn(response.status_code, [302, 403])
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.title, "Ticket à modifier")  # pas changé

    def test_contributor_can_update(self):
        """Un contributor peut modifier un ticket."""
        contrib = make_user("contrib_upd")
        make_membership(contrib, self.project, role="contributor")
        self.client.force_login(contrib)
        response = self.client.post(self.url, self._post_data(title="Modifié par contrib"))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.title, "Modifié par contrib")

    def test_post_valid_redirects_to_detail(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url, self._post_data())
        expected = reverse(
            "ticket-detail",
            kwargs={"pk": self.project.pk, "ticket_pk": self.ticket.pk},
        )
        self.assertRedirects(response, expected)

    def test_post_invalid_returns_form(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url, self._post_data(title=""))
        self.assertEqual(response.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.title, "Ticket à modifier")  # pas changé

    def test_ajax_update_valid(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            self.url,
            self._post_data(title="AJAX update"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_ajax_update_invalid(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            self.url,
            self._post_data(title=""),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_story_points_updated(self):
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data(story_points=8))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.story_points, 8)

    def test_status_updated(self):
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data(status="done"))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "done")


# ===========================================================================
# 8. TICKETDELETEVIEW
# ===========================================================================

class TicketDeleteViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.owner = make_user("delete_owner")
        self.project = make_project(self.owner, code="DEL")
        make_membership(self.owner, self.project, role="admin")
        self.ticket = make_ticket(self.project, self.owner, title="Ticket à supprimer")
        self.url = reverse(
            "ticket-delete",
            kwargs={"pk": self.project.pk, "ticket_pk": self.ticket.pk},
        )

    def test_redirect_anonymous(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_readonly_cannot_delete(self):
        reader = make_user("reader_del")
        make_membership(reader, self.project, role="read-only")
        self.client.force_login(reader)
        self.client.post(self.url)
        self.assertTrue(Ticket.objects.filter(pk=self.ticket.pk).exists())

    def test_admin_can_delete(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse("product-backlog", kwargs={"pk": self.project.pk}),
        )
        self.assertFalse(Ticket.objects.filter(pk=self.ticket.pk).exists())

    def test_delete_detaches_children(self):
        """Supprimer un ticket parent ne supprime pas ses enfants — ils perdent leur parent."""
        child = make_ticket(self.project, self.owner, title="Enfant", parent=self.ticket)
        self.client.force_login(self.owner)
        self.client.post(self.url)
        child.refresh_from_db()
        self.assertIsNone(child.parent)
        self.assertTrue(Ticket.objects.filter(pk=child.pk).exists())

    def test_delete_shows_confirmation_on_get(self):
        """Un GET affiche la page de confirmation."""
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ticket à supprimer")