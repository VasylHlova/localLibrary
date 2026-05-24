from common.mixins import MultiSerializerMixin
from common.permissions import StrictDjangoModelPermissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from user.api.serializers import (
    UserDetailSerializer,
    UserListSerializer,
    UserProfileWriteSerializer,
    UserWriteSerializer,
)
from user.models import CustomUser, UserProfile


class UserViewSet(MultiSerializerMixin, ReadOnlyModelViewSet):
    queryset = CustomUser.objects.select_related("profile").order_by("id")
    permission_classes = [StrictDjangoModelPermissions]
    serializer_class = UserListSerializer

    serializer_classes = {
        "list": UserListSerializer,
        "retrieve": UserDetailSerializer,
    }

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
        from typing import cast

        user_casted = cast(CustomUser, request.user)
        user = (
            CustomUser.objects.select_related("profile")
            .prefetch_related("borrowed_books__book")
            .get(pk=user_casted.pk)
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
        from typing import cast

        user = cast(CustomUser, request.user)
        profile: UserProfile = user.profile
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
        from typing import cast

        user = cast(CustomUser, request.user)
        serializer = UserWriteSerializer(
            user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(user, context={"request": request}).data)
