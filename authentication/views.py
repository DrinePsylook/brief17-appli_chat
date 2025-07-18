from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import get_user_model

from . import forms

def login_page(resquest):
    form = forms.LoginForm()
    message = ''
    if resquest.method == 'POST':
        form = forms.LoginForm(resquest.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Debug: vérifier si l'utilisateur existe
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                # messages.info(resquest, f'Utilisateur trouvé: {user.username}')
            except User.DoesNotExist:
                messages.error(resquest, f'Email ou mot de passe incorrect.')
                return render(resquest, 'authentication/login.html', context={'form': form, 'message': 'Email non trouvé'})
            
            # Essayer l'authentification avec username
            user = authenticate(
                username=user.username,
                password=password,
            )
            
            if user is not None:
                login(resquest, user)
                messages.success(resquest, f'Bonjour {user.username} ! Vous êtes connectés.')
                return redirect('index') 
            else:
                message = 'Email ou mot de passe incorrect.'
                messages.error(resquest, 'Email ou mot de passe incorrect.')
        else:
            messages.error(resquest, 'Formulaire invalide')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(resquest, f'{field}: {error}')
    return render(resquest, 'authentication/login.html', context={'form': form, 'message': message})

def register_page(request):
    """Vue pour l'inscription des utilisateurs"""
    if request.method == 'POST':
        form = forms.SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = user.SUBSCRIBER
            user.save()
            login(request, user)
            messages.success(request, 'Compte créé avec succès !')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = forms.SignupForm()
    
    return render(request, 'authentication/register.html', {'form': form})

def logout_page(request):
    """Vue pour la déconnexion"""
    # Nettoyer tous les messages existants avant la déconnexion
    storage = messages.get_messages(request)
    storage.used = True  # Marquer tous les messages comme utilisés
    
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')