import pytest
import io
import requests
from PIL import Image
from unittest.mock import patch, Mock
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse


User = get_user_model()

# Fixture pour créer différents utilisateurs de test
@pytest.fixture
def user_password_ok(db):
    """Créer un utilisateur standars pour les tests"""
    return User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpassword',
        face_auth_enabled=False,
        face_image_registered=False
    )

@pytest.fixture
def user_face_auth_verify(db):
    """Utilisateur : Auth ON, Image OUI -> Vérification."""
    return User.objects.create_user(
        email='verify@example.com', 
        username='verifyuser', 
        password='verify_pwd',
        face_auth_enabled=True,
        face_image_registered=True,
    )

@pytest.fixture
def user_face_auth_required(db):
    """Créer un utilisateur avec l'authentification faciale activée et image enregistrée"""
    return User.objects.create_user(
        email='setup@example.com',
        username='setupuser',
        password='setuppassword',
        face_auth_enabled=True,
        face_image_registered=False
    )

# -------- Tests pour la vue de configuration de l'authentification faciale -------

# Arrange : patchs pour remplacer 'authenticate' et 'login' de Django.contrib.auth
@patch('authentication.views.authenticate')
@patch('authentication.views.login')
@pytest.mark.parametrize(
    "email, password, expected_message",
    [
        ('invalide@example.com', 'pwd', 'Email ou mot de passe incorrect.'),
        ('', 'pwd', 'Formulaire invalide'), # Test d'un formulaire invalide
    ]
)
def test_ligin_page_post_failure(mock_authenticate, mock_login, client, db, email, password, expected_message):
    """Test de l'échec de la connexion (utilisateur non trouvé ou formulaire invalide)."""
    # Act : Utiliser le client de pytest-django pour simuler une requête POST
    response = client.post(
        '/auth/login/',
        data={'email': email, 'password': password}
    )
    # Assert : si l'email est valide, authenticate est appelé et renvoie None
    if email and User.objects.filter(email=email).exists():
        mock_authenticate.assert_called_once()
    else:
        assert not mock_authenticate.called

    assert response.status_code == 200

# Arrange : patchs pour remplacer 'authenticate', 'login' et 'redirect
@patch('authentication.views.authenticate')
@patch('authentication.views.login')
def test_login_page_success_no_face_auth(mock_login, mock_authenticate, client, user_password_ok):
    """Test de la connexion réussie sans authentification faciale."""
    # Arrange
    mock_user = Mock()
    mock_user.pk = user_password_ok.pk
    mock_user.username = user_password_ok.username
    mock_user.face_auth_enabled = False
    mock_user.face_image_registered = False
   
    mock_authenticate.return_value = mock_user
    
    # Act : Utiliser le client de pytest-django pour simuler une requête POST
    response = client.post(
        '/auth/login/',
        data={'email': user_password_ok.email, 'password': 'testpassword'},
    )
    
    # Assert : Vérifier que authenticate et login ont été appelés
    mock_authenticate.assert_called_once()
    mock_login.assert_called_once()
    
    # Vérifier que l'utilisateur mocké a été passé à login
    call_args = mock_login.call_args
    assert call_args[0][1] == mock_user  # Le deuxième argument de login() doit être mock_user
    
    # Vérifier la redirection vers 'index'
    assert response.status_code == 302
    assert response.url == reverse('index')


@patch('authentication.views.login')
@patch('authentication.views.authenticate')
def test_login_page_face_auth_verify(mock_authenticate, mock_login, client, user_face_auth_verify):
    
    mock_authenticate.return_value = user_face_auth_verify 
    
    # 1. Corrigez l'URL pour /auth/login/
    # 2. Utilisez la bonne fixture (user_face_auth_verify si Auth ON, Image OUI)
    response = client.post( 
        '/auth/login/', 
        data={'email': user_face_auth_verify.email, 'password': 'testpassword'},
    )
    
    # Assertions
    assert mock_authenticate.called
    assert not mock_login.called
    
    # Vérifier la redirection vers verify_face
    assert response.status_code == 302
    assert response.url == reverse('auth:verify_face')


@patch('authentication.views.login')
@patch('authentication.views.authenticate')
def test_login_page_face_auth_setup(mock_authenticate, mock_login, client, user_face_auth_required):
    """Test de la connexion réussie avec Face Auth ON et image NON enregistrée (setup)."""
    
    mock_authenticate.return_value = user_face_auth_required 
    
    # Effectuer la requête POST
    response = client.post(
        '/auth/login/', 
        data={'email': user_face_auth_required.email, 'password': 'testpassword'},
    )
    
    # Assertions
    assert mock_authenticate.called
    assert mock_login.called # login est appelé ici (voir votre code)
    
    # Redirection vers 'auth:setup_face_auth'
    assert response.status_code == 302
    assert response.url == reverse('auth:setup_face_auth')



@patch('authentication.views.requests.post')
@patch('authentication.views.login')
def test_setup_face_auth_success(mock_login, mock_post, client, user_face_auth_required):
    """Test de la configuration réussie de l'authentification faciale."""
    
    # Connecter l'utilisateur
    client.force_login(user_face_auth_required)
    
    # Mock de la réponse de l'API ML
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'success'}
    mock_post.return_value = mock_response
    
    # Créer une fausse image
    image = Image.new('RGB', (100, 100), color='red')
    image_file = io.BytesIO()
    image.save(image_file, 'JPEG')
    image_file.seek(0)
    image_file.name = 'test.jpg'
    
    # Effectuer la requête POST
    response = client.post(
        reverse('auth:setup_face_auth'),
        data={'image': image_file},
        format='multipart'
    )
    
    # Assertions
    assert response.status_code == 200
    assert response.json()['status'] == 'success'
    
    # Vérifier que l'API ML a été appelée
    assert mock_post.called
    call_args = mock_post.call_args
    assert f"/register/{user_face_auth_required.pk}" in call_args[0][0]
    
    # Vérifier que l'utilisateur a été mis à jour
    user_face_auth_required.refresh_from_db()
    assert user_face_auth_required.face_auth_enabled is True
    assert user_face_auth_required.face_image_registered is True
    
    # Vérifier le message de succès
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert "succès" in str(messages[0])


@patch('authentication.views.requests.post')
def test_setup_face_auth_no_image(mock_post, client, user_face_auth_required):
    """Test sans image fournie."""
    
    client.force_login(user_face_auth_required)
    
    response = client.post(reverse('auth:setup_face_auth'))
    
    assert response.status_code == 400
    assert not mock_post.called


@patch('authentication.views.requests.post')
def test_setup_face_auth_api_error(mock_post, client, user_face_auth_required):
    """Test d'erreur de l'API ML."""
    
    client.force_login(user_face_auth_required)
    
    # Mock d'une réponse d'erreur
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'status': 'error',
        'message': 'Aucun visage détecté'
    }
    mock_post.return_value = mock_response
    
    # Créer une fausse image
    image = Image.new('RGB', (100, 100), color='red')
    image_file = io.BytesIO()
    image.save(image_file, 'JPEG')
    image_file.seek(0)
    image_file.name = 'test.jpg'
    
    response = client.post(
        reverse('auth:setup_face_auth'),
        data={'image': image_file},
        format='multipart'
    )
    
    assert response.status_code == 200
    assert response.json()['status'] == 'error'
    assert 'Aucun visage détecté' in response.json()['message']
    
    # Vérifier que l'utilisateur n'a pas été mis à jour
    user_face_auth_required.refresh_from_db()
    assert user_face_auth_required.face_image_registered is False


@patch('authentication.views.requests.post')
def test_setup_face_auth_connection_error(mock_post, client, user_face_auth_required):
    """Test d'erreur de connexion à l'API ML."""
    
    client.force_login(user_face_auth_required)
    
    # Mock d'une exception de connexion
    mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    # Créer une fausse image
    image = Image.new('RGB', (100, 100), color='red')
    image_file = io.BytesIO()
    image.save(image_file, 'JPEG')
    image_file.seek(0)
    image_file.name = 'test.jpg'
    
    response = client.post(
        reverse('auth:setup_face_auth'),
        data={'image': image_file},
        format='multipart'
    )
    
    assert response.status_code == 200
    assert response.json()['status'] == 'error'
    assert 'Connection failed' in response.json()['message']


def test_setup_face_auth_get(client, user_face_auth_required):
    """Test d'affichage de la page de configuration."""
    
    client.force_login(user_face_auth_required)
    
    response = client.get(reverse('auth:setup_face_auth'))
    
    assert response.status_code == 200
    assert 'authentication/setup_face_auth.html' in [t.name for t in response.templates]


def test_setup_face_auth_not_authenticated(client):
    """Test sans utilisateur connecté et sans temp_user_id."""
    
    response = client.post(reverse('auth:setup_face_auth'))
    
    assert response.status_code == 302
    # Le décorateur @login_required redirige vers /accounts/login/ avec le paramètre next
    expected_url = f"/accounts/login/?next={reverse('auth:setup_face_auth')}"
    assert response.url == expected_url