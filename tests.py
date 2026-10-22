import shutil
import tempfile
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Post

MEDIA_TEMPORAL = tempfile.mkdtemp()


def crear_imagen_de_prueba():
    buffer = BytesIO()
    Image.new("RGB", (10, 10), "blue").save(buffer, format="PNG")
    return SimpleUploadedFile("prueba.png", buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class PostsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        self.autor = User.objects.create_user("autor", password="clave-segura-123")
        self.otro_usuario = User.objects.create_user("otro", password="clave-segura-123")
        self.post = Post.objects.create(
            titulo="Post de prueba", contenido="Contenido de ejemplo", autor=self.autor
        )

    def test_listado_y_detalle_son_publicos_y_no_fallan_sin_imagen(self):
        self.assertContains(self.client.get(reverse("listado_posts")), "Post de prueba")
        self.assertContains(self.client.get(self.post.get_absolute_url()), "no tiene imagen")

    def test_rutas_protegidas_redirigen_al_login_si_es_anonimo(self):
        rutas = [
            reverse("crear_post"),
            reverse("editar_post", args=[self.post.slug]),
            reverse("eliminar_post", args=[self.post.slug]),
            reverse("perfil"),
            reverse("editar_perfil"),
        ]
        for ruta in rutas:
            respuesta = self.client.get(ruta)
            self.assertEqual(respuesta.status_code, 302)
            self.assertIn(reverse("login"), respuesta.url)

    def test_crear_post_con_imagen(self):
        self.client.login(username="autor", password="clave-segura-123")
        respuesta = self.client.post(
            reverse("crear_post"),
            {"titulo": "Nuevo post con foto", "contenido": "Texto", "imagen": crear_imagen_de_prueba()},
        )
        nuevo_post = Post.objects.get(titulo="Nuevo post con foto")
        self.assertRedirects(respuesta, nuevo_post.get_absolute_url())
        self.assertTrue(nuevo_post.imagen)
        self.assertEqual(nuevo_post.autor, self.autor)

    def test_editar_y_eliminar_siendo_el_autor(self):
        self.client.login(username="autor", password="clave-segura-123")
        self.client.post(
            reverse("editar_post", args=[self.post.slug]),
            {"titulo": "Título editado", "contenido": "Contenido nuevo"},
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.titulo, "Título editado")

        self.client.post(reverse("eliminar_post", args=[self.post.slug]))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_otro_usuario_no_puede_editar_ni_eliminar(self):
        self.client.login(username="otro", password="clave-segura-123")
        self.assertEqual(self.client.get(reverse("editar_post", args=[self.post.slug])).status_code, 403)
        self.assertEqual(self.client.post(reverse("eliminar_post", args=[self.post.slug])).status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_busqueda_con_y_sin_resultados(self):
        con_resultados = self.client.get(reverse("buscar_posts"), {"q": "ejemplo"})
        self.assertContains(con_resultados, "Post de prueba")
        sin_resultados = self.client.get(reverse("buscar_posts"), {"q": "inexistente"})
        self.assertNotContains(sin_resultados, "Post de prueba")
