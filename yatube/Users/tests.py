from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class TestProfilePage(TestCase):
    """Тест создания персональной страницы пользователя."""
    def setUp(self) -> None:
        self.client = Client()

    def tearDown(self) -> None:
        User.objects.filter(username='alice').delete()

    def test_profile_page_exist(self):
        self.client.post(
            reverse('signup'),
            {'username': 'alice',
             'password1': 'alice123456',
             'password2': 'alice123456'
             },
            follow=True,
        )
        response = self.client.get("/alice/", follow=True)
        self.assertEqual(response.status_code, 200)

