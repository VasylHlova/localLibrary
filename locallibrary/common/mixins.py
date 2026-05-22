class MultiSerializerMixin:
    """Return a different serializer class depending on the current viewset action."""

    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, super().get_serializer_class())


class MultiPermissionMixin:
    """Return different permission classes depending on the current viewset action."""

    permission_classes_by_action: dict = {}

    def get_permissions(self):
        perms = self.permission_classes_by_action.get(self.action)
        if perms is not None:
            return [p() for p in perms]
        return super().get_permissions()
