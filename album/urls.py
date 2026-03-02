from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("photos/upload/", views.upload_photo, name="upload-photo"),
    path("photos/<str:photo_id>/delete/", views.delete_photo, name="delete-photo"),
    path("photos/<str:photo_id>/image/", views.image_content, name="photo-image"),
]
