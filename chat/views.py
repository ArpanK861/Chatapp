import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
import jwt
from .models import Message
from .serializers import MessageSerializer
from django.shortcuts import render
from rest_framework import status

SECRET = os.getenv("JWT_SECRET")

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)
        user = User.objects.create_user(username=username, password=password)
        token = jwt.encode({"user_id": user.id}, os.getenv("JWT_SECRET"), algorithm="HS256")
        return Response({"token": token, "username": user.username}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        user = User.objects.filter(username=request.data["username"]).first()
        if not user or not user.check_password(request.data["password"]):
            return Response({"error": "Invalid credentials"}, status=401)
        token = jwt.encode({"user_id": user.id}, os.getenv("JWT_SECRET"), algorithm="HS256")
        return Response({"token": token, "username": user.username})

class MessagePagination(PageNumberPagination):
    page_size = 25

class MessageHistoryView(ListAPIView):
    serializer_class = MessageSerializer
    pagination_class = MessagePagination

    def get_queryset(self):
        room = self.kwargs["room"]
        return Message.objects.filter(room=room).order_by("-timestamp")

def chat_index(request):
    return render(request, "chat/index.html")