from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views 

app_name = 'auth' 

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_page, name="logout"),
    path("register/", views.register_page, name="register"),
    path("setup_face/", views.setup_face_auth, name="setup_face_auth"),
    path("verify_face/", views.verify_face, name="verify_face"),
]
