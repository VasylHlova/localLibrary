from unittest.mock import MagicMock
from catalog.api.permissions import CanMarkReturned, CanChangeDueBack, CanChangeStatus

def create_mock_request(perms):
    request = MagicMock()
    request.user = MagicMock()
    request.user.has_perm.side_effect = lambda perm: perm in perms
    return request

def test_can_mark_returned_has_permission():
    request = create_mock_request(["catalog.can_mark_returned"])
    permission = CanMarkReturned()
    assert permission.has_permission(request, MagicMock()) is True

def test_can_mark_returned_no_permission():
    request = create_mock_request([])
    permission = CanMarkReturned()
    assert permission.has_permission(request, MagicMock()) is False

def test_can_change_due_back_has_permission():
    request = create_mock_request(["catalog.can_change_due_back"])
    permission = CanChangeDueBack()
    assert permission.has_permission(request, MagicMock()) is True

def test_can_change_due_back_no_permission():
    request = create_mock_request([])
    permission = CanChangeDueBack()
    assert permission.has_permission(request, MagicMock()) is False

def test_can_change_status_has_permission():
    request = create_mock_request(["catalog.can_change_status"])
    permission = CanChangeStatus()
    assert permission.has_permission(request, MagicMock()) is True

def test_can_change_status_no_permission():
    request = create_mock_request([])
    permission = CanChangeStatus()
    assert permission.has_permission(request, MagicMock()) is False
