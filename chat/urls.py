from django.urls import path
from .views import chat_index, RegisterView, LoginView, MessageHistoryView

urlpatterns = [
    path("", chat_index, name="chat_home"), 
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/login/", LoginView.as_view(), name="login"),
    path("api/messages/<str:room>/", MessageHistoryView.as_view(), name="history"),
]