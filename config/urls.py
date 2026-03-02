from django.urls import include, path

urlpatterns = [
    path('', include('album.urls')),
]
