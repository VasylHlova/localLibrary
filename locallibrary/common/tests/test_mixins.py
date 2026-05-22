from common.mixins import MultiPermissionMixin, MultiSerializerMixin
from rest_framework.viewsets import GenericViewSet


class DummyViewSet(MultiSerializerMixin, MultiPermissionMixin, GenericViewSet):
    queryset = []
    serializer_class = str
    serializer_classes = {
        "create": int,
        "update": float,
    }

    permission_classes_by_action = {
        "create": [lambda: "create_perm"],
        "update": [lambda: "update_perm"],
    }


def test_multi_serializer_mixin():
    viewset = DummyViewSet()

    viewset.action = "create"
    assert viewset.get_serializer_class() is int

    viewset.action = "update"
    assert viewset.get_serializer_class() is float

    viewset.action = "list"
    assert viewset.get_serializer_class() is str


def test_multi_permission_mixin():
    viewset = DummyViewSet()

    viewset.action = "create"
    assert viewset.get_permissions() == ["create_perm"]

    viewset.action = "update"
    assert viewset.get_permissions() == ["update_perm"]

    viewset.action = "list"
    assert type(viewset.get_permissions()[0]) is type(GenericViewSet().get_permissions()[0])
