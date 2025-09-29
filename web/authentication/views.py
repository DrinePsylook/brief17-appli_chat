import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import get_user_model
from django.urls import reverse

from . import forms

ML_API_URL = 'http://ml_service:8000/face'  # URL de l'API de reconnaissance faciale

def login_page(resquest):
    form = forms.LoginForm()
    message = ''
    if resquest.method == 'POST':
        print("=== DEBUG LOGIN ===")
        print(f"POST request reçu")
        
        form = forms.LoginForm(resquest.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            print(f"Email: {email}")
            
            # Debug: vérifier si l'utilisateur existe
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                print(f"Utilisateur trouvé: {user.username} (ID: {user.pk})")
                print(f"face_auth_enabled: {user.face_auth_enabled}")
                print(f"face_image_registered: {user.face_image_registered}")
            except User.DoesNotExist:
                print("❌ Utilisateur non trouvé")
                messages.error(resquest, f'Email ou mot de passe incorrect.')
                return render(resquest, 'authentication/login.html', context={'form': form, 'message': 'Email non trouvé'})
            
            # Essayer l'authentification avec username
            user_auth = authenticate(
                resquest,
                username=user.username,
                password=password,
            )
            
            print(f"Authentification: user_auth = {user_auth}")
            
            if user_auth is not None:
                print(f"✅ Authentification réussie")
                print(f"face_auth_enabled: {user_auth.face_auth_enabled}")
                print(f"face_image_registered: {user_auth.face_image_registered}")
                
                # Vérifier si l'authentification faciale est activée
                if user_auth.face_auth_enabled:
                    if user_auth.face_image_registered:
                        # L'utilisateur a déjà une image, procéder à la vérification
                        print("🔍 Image existante - Redirection vers verify_face")
                        resquest.session['temp_user_id'] = user_auth.pk
                        return redirect('auth:verify_face')
                    else:
                        # L'utilisateur n'a pas d'image, rediriger vers setup
                        print("📸 Aucune image - Redirection vers setup_face_auth")
                        resquest.session['temp_user_id'] = user_auth.pk
                        # Connecter l'utilisateur AVANT de rediriger
                        login(resquest, user_auth)
                        return redirect('auth:setup_face_auth')
                else:
                    print("🔓 Auth faciale désactivée - Connexion directe")
                    login(resquest, user_auth)
                    messages.success(resquest, f'Bonjour {user_auth.username} ! Vous êtes connectés.')
                    return redirect('index') 
            else:
                print("❌ Échec de l'authentification")
                message = 'Email ou mot de passe incorrect.'
                messages.error(resquest, 'Email ou mot de passe incorrect.')
        else:
            print("❌ Formulaire invalide")
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
            
            # Vérifier si l'auth faciale est activée
            if user.face_auth_enabled:
                print(f" Auth faciale activée pour {user.username}")
                # Ne pas connecter l'utilisateur, le rediriger vers setup_face_auth
                request.session['temp_user_id'] = user.pk
                messages.success(request, 'Compte créé avec succès ! Veuillez configurer votre authentification faciale.')
                return redirect('auth:setup_face_auth')
            else:
                print(f"🔓 Auth faciale désactivée pour {user.username}")
                login(request, user)
                messages.success(request, 'Compte créé avec succès !')
                return redirect('index')
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
    return redirect('auth:login')

@login_required
def setup_face_auth(request):
    """
    Vue pour configurer l'authentification faciale
    """
    # Vérifier si l'utilisateur est connecté ou a un temp_user_id
    if not request.user.is_authenticated:
        user_id = request.session.get('temp_user_id')
        if not user_id:
            messages.error(request, "Session expirée. Veuillez vous reconnecter.")
            return redirect('auth:login')
    else:
        user_id = request.user.pk

    if request.method == 'POST':
        image_file = request.FILES.get('image')
        if not image_file:
            return HttpResponseBadRequest('Image non fournie.')
        
        try:
            response = requests.post(
                f"{ML_API_URL}/register/{user_id}",
                files={'image': image_file},
            )
            response.raise_for_status()

            result = response.json()
            if result.get('status') == 'success':
                # Marquer l'utilisateur comme ayant l'authentification faciale activée
                User = get_user_model()
                user = User.objects.get(pk=user_id)
                user.face_auth_enabled = True
                user.face_image_registered = True  # ✅ Marquer l'image comme enregistrée
                user.save()
                
                # Connecter l'utilisateur s'il ne l'était pas déjà
                if not request.user.is_authenticated:
                    login(request, user)
                
                messages.success(request, "Authentification faciale configurée avec succès.")
                return JsonResponse({'status': 'success'})
            else:
                messages.error(request, result.get("message", "Erreur lors de la configuration de l'authentification faciale."))
                return JsonResponse({'status': 'error', 'message': result.get("message")})
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Erreur de connexion au service d'authentification faciale: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return render(request, 'authentication/setup_face_auth.html')

def verify_face(request):
    """
    Vue pour la vérification du visage après la saisie des identifiants
    """
    if request.method == 'POST':
        user_id = request.session.get('temp_user_id')
        if not user_id:
            messages.error(request, "Session expirée. Veuillez vous reconnecter.")
            return JsonResponse({"status": "failure", "redirect": reverse('auth:login')})
        
        image_file = request.FILES.get('image')
        if not image_file:
            return JsonResponse({"status": "error", "message": "Image non fournie."})
        
        try: 
            response = requests.post(
                f"{ML_API_URL}/verify/{user_id}",
                files={'image': image_file},
            )
            response.raise_for_status()

            result = response.json()
            if result.get('status') == 'success' and result.get('match'):
                user = get_user_model().objects.get(pk=user_id)
                login(request, user)
                del request.session['temp_user_id']
                # Ajouter le message de succès avant la redirection
                messages.success(request, "🎉 Authentification faciale réussie ! Bienvenue dans le chat.")
                return JsonResponse({"status": "success", "redirect": reverse('index')})
            else:
                return JsonResponse({"status": "failure", "message": result.get("message", "Vérification faciale échouée.")})
        except requests.exceptions.RequestException as e:
            print(f"Erreur de connexion ML API: {e}")
            return JsonResponse({"status": "error", "message": f"Erreur de connexion au service d'authentification faciale: {str(e)}"})
        except Exception as e:
            print(f"Erreur inattendue: {e}")
            return JsonResponse({"status": "error", "message": f"Erreur inattendue: {str(e)}"})
    
    return render(request, 'authentication/verify_face.html')