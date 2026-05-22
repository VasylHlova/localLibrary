from unittest.mock import Mock
from catalog.api.permissions import CanMarkReturned, CanChangeDueBack, CanChangeStatus

class MockUser:
    def __init__(self, perms):
        self.perms = perms

    def has_perm(self, perm):
        return perm in self.perms

class MockRequest:
    def __init__(self, perms):
        self.user = MockUser(perms)

def test_can_mark_returned_has_permission():
    request = MockRequest(["catalog.can_mark_returned"])
    permission = CanMarkReturned()
    assert permission.has_permission(request, Mock()) is True

def test_can_mark_returned_no_permission():
    request = MockRequest([])
    permission = CanMarkReturned()
    assert permission.has_permission(request, Mock()) is False

def test_can_change_due_back_has_permission():
    request = MockRequest(["catalog.can_change_due_back"])
    permission = CanChangeDueBack()
    assert permission.has_permission(request, Mock()) is True

def test_can_change_due_back_no_permission():
    request = MockRequest([])
    permission = CanChangeDueBack()
    assert permission.has_permission(request, Mock()) is False

def test_can_change_status_has_permission():
    request = MockRequest(["catalog.can_change_status"])
    permission = CanChangeStatus()
    assert permission.has_permission(request, Mock()) is True

def test_can_change_status_no_permission():
    request = MockRequest([])
    permission = CanChangeStatus()
    assert permission.has_permission(request, Mock()) is False
