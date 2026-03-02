from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .store import photo_store


class AlbumViewsTests(TestCase):
    def setUp(self) -> None:
        photo_store.clear()

    def test_upload_and_preview(self) -> None:
        image = SimpleUploadedFile(
            "sample.png",
            b"\x89PNG\r\n\x1a\nfake-image-data",
            content_type="image/png",
        )

        response = self.client.post(
            "/photos/upload/",
            {"name": "Sample", "image": image, "sort": "date", "order": "desc"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("selected=", response["Location"])

        list_response = self.client.get("/")
        self.assertEqual(list_response.status_code, 200)
        photos = list_response.context["photos"]
        self.assertEqual(len(photos), 1)
        photo = photos[0]
        self.assertEqual(photo.name, "Sample")

        image_response = self.client.get(f"/photos/{photo.id}/image/")
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response["Content-Type"], "image/png")

    def test_name_validation(self) -> None:
        too_long_name = "x" * 41
        image = SimpleUploadedFile("sample.png", b"x", content_type="image/png")
        response = self.client.post(
            "/photos/upload/",
            {"name": too_long_name, "image": image, "sort": "date", "order": "desc"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "at most 40 characters", status_code=400)

    def test_sort_by_name_ascending(self) -> None:
        photo_store.add("Zulu", "image/png", b"zulu")
        photo_store.add("Alpha", "image/png", b"alpha")

        response = self.client.get("/?sort=name&order=asc")
        self.assertEqual(response.status_code, 200)
        photos = response.context["photos"]
        self.assertEqual([photo.name for photo in photos], ["Alpha", "Zulu"])

    def test_delete_photo(self) -> None:
        photo = photo_store.add("ToDelete", "image/png", b"delete-me")

        response = self.client.post(
            f"/photos/{photo.id}/delete/",
            {"sort": "date", "order": "desc"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(photo_store.get(photo.id))
