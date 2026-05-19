from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from user.models import CustomUser, UserProfile
from user.api.serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserWriteSerializer,
    UserProfileWriteSerializer,
)
from catalog.api.permissions import StrictDjangoModelPermissions


class UserViewSet(ReadOnlyModelViewSet):
    queryset = CustomUser.objects.select_related("profile").all()
    permission_classes = [StrictDjangoModelPermissions]
    serializer_class = UserListSerializer

    serializer_classes = {
        "list": UserListSerializer,
        "retrieve": UserDetailSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "retrieve":
            return qs.prefetch_related("borrowed_books__book")
        return qs

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        user = (
            CustomUser.objects.select_related("profile")
            .prefetch_related("borrowed_books__book")
            .get(pk=request.user.pk)
        )
        serializer = UserDetailSerializer(user, context={"request": request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["patch"],
        url_path="me/profile",
        permission_classes=[IsAuthenticated],
    )
    def update_my_profile(self, request):
        profile: UserProfile = request.user.profile
        serializer = UserProfileWriteSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["patch"],
        url_path="me/account",
        permission_classes=[IsAuthenticated],
    )
    def update_my_account(self, request):
        serializer = UserWriteSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(request.user, context={"request": request}).data)


class UserRegistrationViewSet(GenericViewSet):
    queryset = CustomUser.objects.none()
    serializer_class = UserWriteSerializer
    permission_classes = []

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserDetailSerializer(user, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
