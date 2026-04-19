from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import Photo


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDAT\x08\x99c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xa6\x1d\xb6"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AlbumViewsTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='alice', password='Secretpass123')

    def _image(self, name: str = 'sample.png') -> SimpleUploadedFile:
        return SimpleUploadedFile(name, PNG_BYTES, content_type='image/png')

    def _create_photo(self, *, name: str, owner: User | None = None) -> Photo:
        return Photo.objects.create(
            name=name,
            uploaded_by=owner or self.user,
            content_type='image/png',
            image_filename=f'{name.lower()}.png',
            image_data=PNG_BYTES,
        )

    def test_register_creates_user_and_logs_them_in(self) -> None:
        response = self.client.post(
            '/register/',
            {
                'username': 'newuser',
                'password1': 'Anotherpass123',
                'password2': 'Anotherpass123',
                'next': '/',
            },
        )

        self.assertRedirects(response, '/')
        self.assertTrue(User.objects.filter(username='newuser').exists())
        index_response = self.client.get('/')
        self.assertEqual(index_response.context['user'].username, 'newuser')

    def test_login_and_logout_flow(self) -> None:
        response = self.client.post(
            '/login/',
            {'username': 'alice', 'password': 'Secretpass123', 'next': '/'},
        )
        self.assertRedirects(response, '/')

        logout_response = self.client.post('/logout/')
        self.assertRedirects(logout_response, '/')
        index_response = self.client.get('/')
        self.assertFalse(index_response.context['user'].is_authenticated)

    def test_livez_returns_ok(self) -> None:
        response = self.client.get('/healthz/live/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')

    def test_readyz_returns_ok_when_database_is_available(self) -> None:
        response = self.client.get('/healthz/ready/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')

    def test_readyz_returns_503_when_database_is_unavailable(self) -> None:
        with patch('album.views.connection.cursor', side_effect=Exception('database unavailable')):
            response = self.client.get('/healthz/ready/')

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.content, b'database unavailable')

    def test_upload_requires_authentication(self) -> None:
        response = self.client.post(
            '/photos/upload/',
            {'name': 'Sample', 'image': self._image(), 'sort': 'date', 'order': 'desc'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])
        self.assertEqual(Photo.objects.count(), 0)

    def test_authenticated_upload_and_preview(self) -> None:
        self.client.login(username='alice', password='Secretpass123')

        response = self.client.post(
            '/photos/upload/',
            {'name': 'Sample', 'image': self._image(), 'sort': 'date', 'order': 'desc'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('selected=', response['Location'])

        photo = Photo.objects.get(name='Sample')
        self.assertEqual(photo.uploaded_by, self.user)

        list_response = self.client.get('/')
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.context['photos'].count(), 1)

        image_response = self.client.get(f'/photos/{photo.pk}/image/')
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response['Content-Type'], 'image/png')
        self.assertEqual(image_response.content, PNG_BYTES)

    def test_name_validation(self) -> None:
        self.client.login(username='alice', password='Secretpass123')

        response = self.client.post(
            '/photos/upload/',
            {
                'name': 'x' * 41,
                'image': self._image(),
                'sort': 'date',
                'order': 'desc',
            },
        )

        self.assertContains(response, 'Ensure this value has at most 40 characters', status_code=400)

    def test_sort_by_name_ascending(self) -> None:
        self._create_photo(name='Zulu')
        self._create_photo(name='Alpha')

        response = self.client.get('/?sort=name&order=asc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([photo.name for photo in response.context['photos']], ['Alpha', 'Zulu'])

    def test_delete_requires_authentication_and_authenticated_delete_works(self) -> None:
        photo = self._create_photo(name='ToDelete')

        anonymous_response = self.client.post(
            f'/photos/{photo.pk}/delete/',
            {'sort': 'date', 'order': 'desc'},
        )
        self.assertEqual(anonymous_response.status_code, 302)
        self.assertTrue(Photo.objects.filter(pk=photo.pk).exists())

        self.client.login(username='alice', password='Secretpass123')
        delete_response = self.client.post(
            f'/photos/{photo.pk}/delete/',
            {'sort': 'date', 'order': 'desc'},
        )
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Photo.objects.filter(pk=photo.pk).exists())
