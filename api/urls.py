
from django.urls import path
from .views import RegisterView, LoginView, UserView, PostView, PostDetailView

urlpatterns = [
    path('register', RegisterView.as_view()),
    path('login', LoginView.as_view()),
    path('user', UserView.as_view()),
    path('post', PostView.as_view()),
    path('post/<int:pk>/', PostDetailView.as_view()),
]