from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

class LoginForm(forms.Form):
    email = forms.CharField(max_length=63, label='Email')
    password = forms.CharField(max_length=63, widget=forms.PasswordInput, label='Mot de passe')

class SignupForm(UserCreationForm):
    # Rendre l'email obligatoire
    email = forms.EmailField(required=True, label='Email')
    
    # Rendre la photo de profil optionnelle
    profile_photo = forms.ImageField(required=False, label='Photo de profil')
    
    # Ajouter la case à cocher pour l'authentification faciale
    enable_face_auth = forms.BooleanField(
        required=False, 
        label="Activer l'authentification faciale",
        help_text="Vous pourrez configurer votre visage après l'inscription"
    )
    
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2', 'profile_photo', 'enable_face_auth')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if self.cleaned_data.get('profile_photo'):
            user.profile_photo = self.cleaned_data['profile_photo']
        user.role = user.SUBSCRIBER  # Valeur par défaut
        
        # Activer l'auth faciale si coché
        user.face_auth_enabled = self.cleaned_data.get('enable_face_auth', False)
        
        if commit:
            user.save()
        return user