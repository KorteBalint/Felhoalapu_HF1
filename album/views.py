from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .store import photo_store

MAX_NAME_LENGTH = 40


def _normalize_sort(sort: str | None) -> str:
    return "name" if sort == "name" else "date"


def _normalize_order(order: str | None) -> str:
    return "asc" if order == "asc" else "desc"


@require_GET
def index(request: HttpRequest) -> HttpResponse:
    sort = _normalize_sort(request.GET.get("sort"))
    order = _normalize_order(request.GET.get("order"))
    selected_id = request.GET.get("selected")
    selected_photo = photo_store.get(selected_id) if selected_id else None
    context = {
        "photos": photo_store.list(sort_by=sort, order=order),
        "sort": sort,
        "order": order,
        "selected_photo": selected_photo,
        "error": "",
        "max_name_length": MAX_NAME_LENGTH,
    }
    return render(request, "album/index.html", context)


@require_POST
def upload_photo(request: HttpRequest) -> HttpResponse:
    sort = _normalize_sort(request.POST.get("sort"))
    order = _normalize_order(request.POST.get("order"))
    name = (request.POST.get("name") or "").strip()
    file = request.FILES.get("image")

    error = ""
    if not name:
        error = "Name is required."
    elif len(name) > MAX_NAME_LENGTH:
        error = f"Name must be at most {MAX_NAME_LENGTH} characters."
    elif file is None:
        error = "Image file is required."
    elif not (file.content_type or "").startswith("image/"):
        error = "Only image uploads are allowed."

    if error:
        context = {
            "photos": photo_store.list(sort_by=sort, order=order),
            "sort": sort,
            "order": order,
            "selected_photo": None,
            "error": error,
            "max_name_length": MAX_NAME_LENGTH,
        }
        return render(request, "album/index.html", context, status=400)

    photo = photo_store.add(
        name=name,
        content_type=file.content_type or "application/octet-stream",
        data=file.read(),
    )
    return redirect(f"/?sort={sort}&order={order}&selected={photo.id}")


@require_POST
def delete_photo(request: HttpRequest, photo_id: str) -> HttpResponse:
    sort = _normalize_sort(request.POST.get("sort"))
    order = _normalize_order(request.POST.get("order"))
    photo_store.delete(photo_id)
    return redirect(f"/?sort={sort}&order={order}")


@require_http_methods(["GET"])
def image_content(request: HttpRequest, photo_id: str) -> HttpResponse:
    photo = photo_store.get(photo_id)
    if photo is None:
        raise Http404("Photo not found.")
    return HttpResponse(photo.data, content_type=photo.content_type)
