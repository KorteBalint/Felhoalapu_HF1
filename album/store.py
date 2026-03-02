from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from uuid import uuid4


@dataclass(slots=True)
class Photo:
    id: str
    name: str
    uploaded_at: datetime
    content_type: str
    data: bytes


class InMemoryPhotoStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._photos: dict[str, Photo] = {}

    def add(self, name: str, content_type: str, data: bytes) -> Photo:
        with self._lock:
            photo = Photo(
                id=str(uuid4()),
                name=name,
                uploaded_at=datetime.now(),
                content_type=content_type,
                data=data,
            )
            self._photos[photo.id] = photo
            return photo

    def get(self, photo_id: str) -> Photo | None:
        with self._lock:
            return self._photos.get(photo_id)

    def delete(self, photo_id: str) -> bool:
        with self._lock:
            return self._photos.pop(photo_id, None) is not None

    def list(self, sort_by: str = "date", order: str = "desc") -> list[Photo]:
        with self._lock:
            photos = list(self._photos.values())

        sort_key = "name" if sort_by == "name" else "date"
        descending = order != "asc"

        if sort_key == "name":
            photos.sort(key=lambda p: (p.name.lower(), p.uploaded_at), reverse=descending)
        else:
            photos.sort(key=lambda p: p.uploaded_at, reverse=descending)

        return photos

    def clear(self) -> None:
        with self._lock:
            self._photos.clear()


photo_store = InMemoryPhotoStore()
