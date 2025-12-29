import os
import jwt
from django.contrib.auth.models import User

SECRET = os.getenv("JWT_SECRET")

def decode_jwt(token):
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return User.objects.get(id=payload["user_id"])
    except:
        return None
