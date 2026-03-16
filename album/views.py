from urllib.parse import urlencode

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import AlbumAuthenticationForm, PhotoUploadForm, SignUpForm
from .models import Photo

MAX_NAME_LENGTH = Photo._meta.get_field("name").max_length


def _normalize_sort(sort: str | None) -> str:
    return "name" if sort == "name" else "date"


def _normalize_order(order: str | None) -> str:
    return "asc" if order == "asc" else "desc"


def _query_string(sort: str, order: str, selected: int | None = None) -> str:
    params: dict[str, str | int] = {"sort": sort, "order": order}
    if selected is not None:
        params["selected"] = selected
    return urlencode(params)


def _list_photos(sort: str, order: str):
    photos = Photo.objects.select_related("uploaded_by")
    descending = order != "asc"

    if sort == "name":
        direction = Lower("name").desc() if descending else Lower("name").asc()
        secondary = "-uploaded_at" if descending else "uploaded_at"
        return photos.order_by(direction, secondary)

    return photos.order_by("-uploaded_at" if descending else "uploaded_at")


def _render_index(
    request: HttpRequest,
    *,
    sort: str,
    order: str,
    upload_form: PhotoUploadForm | None = None,
    selected_photo: Photo | None = None,
    status: int = 200,
) -> HttpResponse:
    if selected_photo is None:
        selected_id = request.GET.get("selected")
        if selected_id:
            selected_photo = Photo.objects.select_related("uploaded_by").filter(pk=selected_id).first()

    context = {
        "photos": _list_photos(sort, order),
        "sort": sort,
        "order": order,
        "selected_photo": selected_photo,
        "upload_form": upload_form or PhotoUploadForm(),
        "max_name_length": MAX_NAME_LENGTH,
    }
    return render(request, "album/index.html", context, status=status)


@require_GET
def index(request: HttpRequest) -> HttpResponse:
    sort = _normalize_sort(request.GET.get("sort"))
    order = _normalize_order(request.GET.get("order"))
    return _render_index(request, sort=sort, order=order)


@login_required
@require_POST
def upload_photo(request: HttpRequest) -> HttpResponse:
    sort = _normalize_sort(request.POST.get("sort"))
    order = _normalize_order(request.POST.get("order"))
    upload_form = PhotoUploadForm(request.POST, request.FILES)

    if not upload_form.is_valid():
        return _render_index(
            request,
            sort=sort,
            order=order,
            upload_form=upload_form,
            status=400,
        )

    uploaded_image = upload_form.cleaned_data["image"]
    photo = Photo.objects.create(
        name=upload_form.cleaned_data["name"],
        uploaded_by=request.user,
        content_type=uploaded_image.content_type or "application/octet-stream",
        image_filename=uploaded_image.name or "upload.bin",
        image_data=uploaded_image.read(),
    )
    return redirect(f"{reverse('index')}?{_query_string(sort, order, selected=photo.pk)}")


@login_required
@require_POST
def delete_photo(request: HttpRequest, photo_id: str) -> HttpResponse:
    sort = _normalize_sort(request.POST.get("sort"))
    order = _normalize_order(request.POST.get("order"))
    photo = get_object_or_404(Photo, pk=photo_id)
    photo.delete()
    return redirect(f"{reverse('index')}?{_query_string(sort, order)}")


@require_http_methods(["GET", "POST"])
def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("index")

    redirect_to = request.GET.get("next") or request.POST.get("next") or reverse("index")
    form = SignUpForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect(redirect_to)

    return render(
        request,
        "album/auth.html",
        {
            "page_title": "Create account",
            "heading": "Start your archive",
            "subheading": "Create an account to upload and manage photos.",
            "form": form,
            "submit_label": "Create account",
            "alternate_label": "Already have an account?",
            "alternate_url": f"{reverse('login')}?{urlencode({'next': redirect_to})}",
            "alternate_cta": "Sign in",
            "next_value": redirect_to,
        },
        status=400 if request.method == "POST" else 200,
    )


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("index")

    redirect_to = request.GET.get("next") or request.POST.get("next") or reverse("index")
    form = AlbumAuthenticationForm(request=request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(redirect_to)

    return render(
        request,
        "album/auth.html",
        {
            "page_title": "Sign in",
            "heading": "Return to your archive",
            "subheading": "Sign in to upload new shots or remove existing ones.",
            "form": form,
            "submit_label": "Sign in",
            "alternate_label": "Need an account?",
            "alternate_url": f"{reverse('register')}?{urlencode({'next': redirect_to})}",
            "alternate_cta": "Create account",
            "next_value": redirect_to,
        },
        status=400 if request.method == "POST" else 200,
    )


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("index")


@require_http_methods(["GET"])
def image_content(request: HttpRequest, photo_id: str) -> HttpResponse:
    photo = Photo.objects.filter(pk=photo_id).first()
    if photo is None:
        raise Http404("Photo not found.")
    image_bytes = bytes(photo.image_data or b"")
    if not image_bytes:
        raise Http404("Photo content not found.")
    return HttpResponse(
        image_bytes,
        content_type=photo.content_type,
        headers={
            "Content-Length": str(len(image_bytes)),
            "Content-Disposition": content_disposition_header(
                as_attachment=False,
                filename=photo.image_filename,
            ),
        },
    )
