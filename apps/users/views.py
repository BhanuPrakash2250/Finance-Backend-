"""
User Views

Endpoints:
  POST   /api/auth/register/         → Admin creates a new user
  POST   /api/auth/login/            → Any user logs in (returns JWT)
  POST   /api/auth/logout/           → Blacklists refresh token
  GET    /api/auth/me/               → Get own profile
  PUT    /api/auth/me/               → Update own profile (name only)
  POST   /api/auth/me/password/      → Change own password
  GET    /api/auth/users/            → Admin: list all users
  GET    /api/auth/users/<id>/       → Admin: get user detail
  PUT    /api/auth/users/<id>/       → Admin: update user
  DELETE /api/auth/users/<id>/       → Admin: deactivate user
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from .serializers import LoginSerializer

User = get_user_model()

# ✅ Custom Admin Permission
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# ✅ LOGIN API (WORKING)
class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        try:
            email = request.data.get("email")
            password = request.data.get("password")

            if not email or not password:
                return Response(
                    {"success": False, "error": "Email and password required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.filter(email=email).first()

            if not user or not user.check_password(password):
                return Response(
                    {"success": False, "error": "Invalid credentials"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            refresh = RefreshToken.for_user(user)

            return Response({
                "success": True,
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token, effectively logging the user out.
    Body: { "refresh": "<refresh_token>" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'success': False, 'error': {'message': '`refresh` token is required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'success': False, 'error': {'message': 'Invalid or already-expired refresh token.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({'success': True, 'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


# ─── Own Profile ───────────────────────────────────────────────────────────────

class MeView(APIView):
    """
    GET  /api/auth/me/  → Return the authenticated user's profile.
    PUT  /api/auth/me/  → Update own first/last name (role cannot be self-assigned).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response({'success': True, 'data': serializer.data})

    def put(self, request):
        # Users can only update their own name — not role/is_active
        allowed_fields = {'first_name', 'last_name'}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        serializer = UserUpdateSerializer(request.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': 'Profile updated.',
            'data': UserProfileSerializer(request.user).data
        })


class ChangePasswordView(APIView):
    """POST /api/auth/me/password/ — Change own password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'message': 'Password changed successfully.'})


# ─── Admin: User Management ────────────────────────────────────────────────────

class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/auth/users/  → Admin: paginated list of all users
    POST /api/auth/users/  → Admin: create a new user with a specified role
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserRegistrationSerializer
        return UserProfileSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Wrap in our envelope — pagination already wraps 'results'
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'success': True, 'message': 'User created.', 'data': UserProfileSerializer(user).data},
            status=status.HTTP_201_CREATED
        )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/auth/users/<id>/  → Admin: get user detail
    PUT    /api/auth/users/<id>/  → Admin: update role/status
    DELETE /api/auth/users/<id>/  → Admin: soft-delete (deactivate) user
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserProfileSerializer

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        return Response({'success': True, 'data': UserProfileSerializer(user).data})

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True   # Always allow partial updates
        user = self.get_object()
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': 'User updated.',
            'data': UserProfileSerializer(user).data
        })

    def destroy(self, request, *args, **kwargs):
        """Soft delete: deactivate instead of physically removing the user."""
        user = self.get_object()
        if user == request.user:
            return Response(
                {'success': False, 'error': {'message': 'You cannot deactivate your own account.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = False
        user.save()
        return Response({'success': True, 'message': f'User {user.email} has been deactivated.'})
