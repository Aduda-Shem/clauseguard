from django.urls import path
from knox.views import LogoutView

from accounts.views import LoginView, MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("user/", MeView.as_view()),
]
