from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Photo


class PhotoUploadForm(forms.Form):
    name = forms.CharField(
        max_length=Photo._meta.get_field('name').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Photo title',
                'maxlength': Photo._meta.get_field('name').max_length,
            }
        ),
    )
    image = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
    )

    def clean_image(self):
        image = self.cleaned_data['image']
        content_type = getattr(image, 'content_type', '') or ''
        if not content_type.startswith('image/'):
            raise forms.ValidationError('Only image uploads are allowed.')
        return image


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose a username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Repeat password'})


class AlbumAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username'}),
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
    )
