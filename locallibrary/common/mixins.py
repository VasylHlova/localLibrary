from collections.abc import Sequence
from typing import Any

from rest_framework.viewsets import GenericViewSet


class MultiSerializerMixin(GenericViewSet):
    serializer_classes: dict[str, type[Any]] = {}

    def get_serializer_class(self) -> type[Any]:
        return self.serializer_classes.get(self.action, super().get_serializer_class())


class MultiPermissionMixin(GenericViewSet):
    permission_classes_by_action: dict[str, list[Any]] = {}

    def get_permissions(self) -> Sequence[Any]:
        perms = self.permission_classes_by_action.get(self.action)
        if perms is not None:
            return [p() for p in perms]
        return super().get_permissions()
