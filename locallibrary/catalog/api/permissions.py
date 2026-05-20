from rest_framework.permissions import BasePermission


class CanMarkReturned(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('catalog.can_mark_returned')


class CanChangeDueBack(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('catalog.can_change_due_back')
