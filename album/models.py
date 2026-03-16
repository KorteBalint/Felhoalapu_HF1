from django.conf import settings
from django.db import models


class Photo(models.Model):
    name = models.CharField(max_length=40)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    content_type = models.CharField(max_length=100)
    image_filename = models.CharField(max_length=255)
    image_data = models.BinaryField()
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='photos',
    )

    class Meta:
        ordering = ['-uploaded_at', 'name']

    def __str__(self) -> str:
        return self.name
