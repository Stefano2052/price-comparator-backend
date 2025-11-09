# api/views_auth.py (crea questo file oppure puoi aggiungere in views.py)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import firebase_admin
from firebase_admin import auth, credentials
from django.contrib.auth import get_user_model

User = get_user_model()

# Se non hai ancora inizializzato Firebase Admin, fallo una volta all'avvio del server
if not firebase_admin._apps:
    import os
    from pathlib import Path

    default_path = Path(__file__).resolve().parent.parent / "backend" / "credentials" / "price-comparator-454311-firebase-adminsdk-fbsvc-ceb73ff65f.json"
    cred_path = os.environ.get("FIREBASE_CREDENTIALS", str(default_path))
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin inizializzato correttamente")
    else:
        print(f"⚠️ File credenziali Firebase mancante: {cred_path}")


class FirebaseAuthConvertView(APIView):
    permission_classes = []  # Pubblica questa rotta per ora

    def post(self, request):
        id_token = request.data.get('id_token')

        if not id_token:
            return Response({'detail': 'Missing ID Token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verifica il token
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email')

            # Cerca o crea l'utente in Django
            user, created = User.objects.get_or_create(email=email, defaults={'username': email})

            # Crea Access e Refresh token
            refresh = RefreshToken.for_user(user)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            })

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class CurrentUserMe(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_staff": u.is_staff,
            "is_superuser": u.is_superuser,
            # comodo per il frontend:
            "is_admin": bool(u.is_staff or u.is_superuser),
        })