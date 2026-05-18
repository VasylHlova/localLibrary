from rest_framework.permissions import DjangoModelPermissions, BasePermission


class StrictDjangoModelPermissions(DjangoModelPermissions):
    def __init__(self):
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']
        self.perms_map['HEAD'] = ['%(app_label)s.view_%(model_name)s']
        self.perms_map['OPTIONS'] = ['%(app_label)s.view_%(model_name)s']
        super().__init__()


class CanMarkReturned(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('catalog.can_mark_returned')

class CanChangeDueBack(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('catalog.can_change_due_back')