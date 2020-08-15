import tempfile
import io
from unittest import mock
from PIL import Image

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.base import ContentFile
from django.core.files.base import File

from .models import Post, Group, Follow, Comment


class TestStringMethods(TestCase):
    def test_length(self):
        self.assertEqual(len('yatube'), 6)

    def test_show_msg(self):
        self.assertTrue(False, msg="Важная проверка на истинность")


class PostTestList(TestCase):
    def setUp(self) -> None:
        # Авторизованный пользователь:
        self.client = Client()
        self.authorized_user = User.objects.create_user(
            username='alice',
            email='alice@gmail.com',
            password='alice123'
        )
        self.authorized_user.save()
        self.client.force_login(self.authorized_user)
        # Неавторизованный пользователь:
        self.unauthorized_client = Client()
        self.unauthorized_user = User.objects.create_user(
            username='rick',
            email='rick@gmail.com',
            password='rick123'
        )
        self.unauthorized_user.save()
        # Создаем тестовую группу:
        self.group = Group.objects.create(
            title='test_group',
            slug='test_group',
            description='test_description'
        )
        # Создаем пост для авторизованного пользователя:
        self.client.post(
            reverse('new_post'),
            data={'text': 'original test text', 'group': self.group.id},
            follow=True
        )
        # Создаем список адресов, по которым доступен созданный пост:
        self.urls_list = []
        self.post_id = Post.objects.get(text='original test text', group=self.group.id).id
        url_index = reverse('index')
        self.urls_list.append(url_index)
        url_profile = reverse('profile', kwargs={'username': self.authorized_user.username})
        self.urls_list.append(url_profile)
        url_group = reverse('group_posts', kwargs={'slug': self.group.slug})
        self.urls_list.append(url_group)
        url_post = reverse(
            'post',
            kwargs={
                'username': self.authorized_user.username,
                'post_id': self.post_id
            }
        )
        self.urls_list.append(url_post)

    def tearDown(self) -> None:
        Group.objects.filter(
            title='test_group',
            slug='test_group',
            description='test_description'
        ).delete()
        User.objects.filter(username='alice').delete()
        User.objects.filter(username='rick').delete()
        Post.objects.filter(text='test_text').delete()
        Post.objects.filter(text='original test text').delete()
        Post.objects.filter(text='edit test text').delete()
        Post.objects.filter(text='test image text').delete()
        Post.objects.filter(text='test not image').delete()
        Post.objects.filter(text='test index cache').delete()

    def test_post_create(self):
        """Тест: авторизованный пользователь может создать пост."""
        cache.clear()
        response = self.client.post(
            reverse('new_post'),
            data={'text': 'test_text', 'group': self.group.id},
            follow=True
        )
        post = Post.objects.get(text='test_text')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.filter(text='test_text').count(), 1)
        self.assertEqual(post.author, self.authorized_user)
        self.assertEqual(post.group, self.group)

    def test_post_create_without_auth(self):
        """Тест: неавторизованный пользователь не может создать пост.

        При попытке - редирект на страницу входа.
        """
        self.unauthorized_client.post(
            reverse('new_post'),
            data={'text': 'test_text', 'group': self.group.id},
            follow=True
        )
        self.assertEqual(Post.objects.filter(text='test_text').count(), 0)
        cache.clear()
        response = self.unauthorized_client.get(reverse('new_post'), follow=True)
        login = reverse('login')
        new = reverse('new_post')
        self.assertRedirects(
            response,
            f'{login}?next={new}',
            status_code=302,
            target_status_code=200,
            msg_prefix='',
            fetch_redirect_response=True
        )

    def test_new_post(self):
        """Тест на отображение созданного поста.

        Пост создается авторизованным пользователем
        После создания, пост должен отображаться на страницах:
        главная(index), страница пользователя(profile), страница поста(post).
        """
        cache.clear()
        # Проверим пост по списку URLs:
        for url in self.urls_list:
            response = self.client.get(url)
            self.assertContains(
                response,
                'original test text',
                count=1,
                status_code=200
            )

    def test_edit_post(self):
        """Авторизованный пользователь может изменить свой пост.

        Содержимое поста изменится на всех связанных страницах.
        """
        # Вызываем страницу редактирования поста:
        url_post_edit = reverse('post_edit',
                                kwargs={
                                    'username': self.authorized_user.username,
                                    'post_id': self.post_id
                                }
                                )
        self.client.post(
            url_post_edit,
            data={'text': 'edit test text', 'group': self.group.id},
            follow=True
        )
        cache.clear()
        # Проверим пост по списку URLs:
        for url in self.urls_list:
            response = self.client.get(url)
            self.assertContains(
                response,
                'edit test text',
                count=1,
                status_code=200
            )
            self.assertNotContains(
                response,
                'original test text',
                status_code=200
            )

    def test_check_404(self):
        """Проверка 404 ошибки."""
        response = self.client.get('smturl')
        self.assertEqual(response.status_code, 404)
        response = self.unauthorized_client.get('sdfaq')
        self.assertEqual(response.status_code, 404)

    def test_image_add(self):
        """Проверка добавления изображения по списку URLs"""
        with tempfile.TemporaryDirectory() as temp_directory:
            with override_settings(MEDIA_ROOT=temp_directory):
                byte_image = io.BytesIO()
                im = Image.new("RGB", size=(500, 500), color=(255, 0, 0, 0))
                im.save(byte_image, format='jpeg')
                byte_image.seek(0)
                payload = {'text': 'test image text',
                           'group': self.group.id,
                           'image': ContentFile(byte_image.read(), name='test.jpeg'),
                           }
                self.client.post(
                    reverse('new_post'),
                    data=payload,
                    follow=True
                )
                # Создадим новый список URLs для нового поста:
                self.urls_list_for_image = [i for i in self.urls_list]
                self.post_id = Post.objects.get(text='test image text', group=self.group.id).id
                url_post = reverse(
                    'post',
                    kwargs={
                        'username': self.authorized_user.username,
                        'post_id': self.post_id
                        }
                )
                self.urls_list_for_image[3] = url_post
                cache.clear()
                for url in self.urls_list_for_image:
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    # Проверка на вхождение тега:
                    self.assertContains(response, '<img', status_code=200)
                    # Проверка по уникальному id:
                    self.assertContains(response, 'unique_id', status_code=200)

    def test_not_image_not_add(self):
        """Файлы иных форматов не добавляются на сайт вместо изображения."""
        file_mock = mock.MagicMock(spec=File, name='wrong.txt')
        payload = {'text': 'test image text',
                   'group': self.group.id,
                   'image': file_mock,
                   }
        response = self.client.post(
            reverse('new_post'),
            data=payload,
            follow=True
        )
        error = 'Upload a valid image. ' \
                'The file you uploaded was either not an image or a corrupted image.'
        self.assertFormError(response, form='form', field='image', errors=error)

    def test_index_cache(self):
        """Проверка работы кэша."""
        self.client.post(
            reverse('new_post'),
            data={
                'text': 'test index cache',
                'group': self.group.id,
            },
            follow=True
        )
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, 'test index cache', status_code=200)
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'test index cache', count=1, status_code=200)


class TestFollowComment(TestCase):
    def setUp(self) -> None:
        # Авторизованный пользователь:
        self.client = Client()
        self.user = User.objects.create_user(
            username='alice',
            email='alice@gmail.com',
            password='alice123'
        )
        self.user.save()
        self.client.force_login(self.user)
        # Неавторизованный пользователь:
        self.unauthorized_client = Client()
        self.unauthorized_user = User.objects.create_user(
            username='django',
            email='django@gmail.com',
            password='django123'
        )
        self.unauthorized_user.save()
        # Автор:
        self.author_client = Client()
        self.author_user = User.objects.create_user(
            username='rick',
            email='rick@gmail.com',
            password='rick123'
        )
        self.author_user.save()
        self.author_client.force_login(self.author_user)
        # Не подписанный ни на кого пользователь:
        self.free_client = Client()
        self.free_user = User.objects.create_user(
            username='luke',
            email='luke@gmail.com',
            password='luke123'
        )
        self.free_user.save()
        self.free_client.force_login(self.free_user)
        # Создаем тестовую группу:
        self.group = Group.objects.create(
            title='test_group',
            slug='test_group',
            description='test_description'
        )
        # Новая запись автора.
        self.author_client.post(
            reverse('new_post'),
            data={'text': 'original test text', 'group': self.group.id},
            follow=True
        )
        self.post_id = Post.objects.get(text='original test text', group=self.group.id).id

    def tearDown(self) -> None:
        User.objects.filter(username='alice').delete()
        User.objects.filter(username='rick').delete()
        User.objects.filter(username='luke').delete()
        User.objects.filter(username='django').delete()
        Follow.objects.filter(author=self.author_user, user=self.user).delete()
        Group.objects.filter(
            title='test_group',
            slug='test_group',
            description='test_description'
        ).delete()
        Post.objects.filter(text='original test text').delete()
        Comment.objects.filter(text='Such a good post!').delete()
        Comment.objects.filter(text='Very strange post!').delete()

    def test_aut_user_can_follow(self):
        """Авторизованный пользователь может подписываться/отписывать на авторов."""
        count = Follow.objects.filter(author=self.author_user, user=self.user).count()
        self.assertEqual(count, 0)
        self.client.get(
            reverse('profile_follow', kwargs={'username': self.author_user.username})
        )
        count = Follow.objects.filter(author=self.author_user, user=self.user).count()
        self.assertEqual(count, 1)
        self.client.get(
            reverse('profile_unfollow', kwargs={'username': self.author_user.username})
        )
        count = Follow.objects.filter(author=self.author_user, user=self.user).count()
        self.assertEqual(count, 0)

    def test_view_new_follow_post(self):
        """Новая запись отображается у подписчиков."""
        self.client.get(
            reverse('profile_follow', kwargs={'username': self.author_user.username})
        )
        response = self.client.get(reverse('follow_index'))
        self.assertContains(response, 'original test text', status_code=200)
        response = self.free_client.get(reverse('follow_index'))
        self.assertNotContains(response, 'original test text', status_code=200)

    def test_only_aut_user_comment(self):
        """Только авторизированный пользователь может комментировать посты."""
        self.client.post(
            reverse('add_comment',
                    kwargs={
                        'username': self.author_user.username,
                        'post_id': self.post_id
                    }),
            data={'text': 'Such a good post!'},
            follow=True,
        )
        count_comment = Comment.objects.filter(text='Such a good post!').count()
        self.assertEqual(count_comment, 1)

        self.unauthorized_client.post(
            reverse('add_comment',
                    kwargs={
                        'username': self.author_user.username,
                        'post_id': self.post_id
                    }),
            data={'text': 'Very strange post!'},
            follow=True,
        )
        count_new_comment = Comment.objects.filter(text='Very strange post!').count()
        self.assertEqual(count_new_comment, 0)

