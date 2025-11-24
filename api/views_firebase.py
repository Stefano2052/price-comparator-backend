from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

import firebase_admin
from firebase_admin import auth as firebase_auth


class FirebaseAuthConvertView(APIView):
    """
    Riceve idToken Firebase, lo valida tramite Firebase Admin,
    crea o recupera l'utente Django e ritorna JWT (refresh + access).
    """

    def post(self, request):
        id_token = request.data.get("id_token")

        if not id_token:
            return Response({"detail": "id_token mancante"}, status=400)

        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except Exception as e:
            return Response({"detail": str(e)}, status=401)

        firebase_uid = decoded.get("uid")
        email = decoded.get("email")

        if not email:
            return Response({"detail": "Email non disponibile nel token Firebase"}, status=400)

        # Recupera o crea utente Django
        user, _ = User.objects.get_or_create(
            username=email,
            defaults={"email": email}
        )

        # Genera JWT SimpleJWT
        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "email": email,
            "uid": firebase_uid,
        })


class CurrentUserMe(APIView):
    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
        })
