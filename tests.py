from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import PerfilUsuario


class UsuariosTests(TestCase):
    def test_registro_crea_usuario_y_perfil(self):
        respuesta = self.client.post(
            reverse("registro"),
            {
                "username": "nuevo",
                "email": "nuevo@example.com",
                "password1": "clave-segura-123",
                "password2": "clave-segura-123",
            },
        )
        self.assertRedirects(respuesta, reverse("login"))
        usuario = User.objects.get(username="nuevo")
        self.assertTrue(PerfilUsuario.objects.filter(user=usuario).exists())

    def test_login_y_logout(self):
        User.objects.create_user("usuario", password="clave-segura-123")
        self.client.post(reverse("login"), {"username": "usuario", "password": "clave-segura-123"})
        self.assertIn("_auth_user_id", self.client.session)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_editar_perfil_autenticado(self):
        User.objects.create_user("usuario", password="clave-segura-123")
        self.client.login(username="usuario", password="clave-segura-123")
        self.client.post(reverse("editar_perfil"), {"bio": "Mi bio"})
        self.assertEqual(PerfilUsuario.objects.get(user__username="usuario").bio, "Mi bio")
