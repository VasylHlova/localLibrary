import pytest
from common.permissions import StrictDjangoModelPermissions

def test_strict_django_model_permissions_perms_map():
    permission = StrictDjangoModelPermissions()
    assert permission.perms_map['GET'] == ['%(app_label)s.view_%(model_name)s']
    assert permission.perms_map['HEAD'] == ['%(app_label)s.view_%(model_name)s']
    assert permission.perms_map['OPTIONS'] == ['%(app_label)s.view_%(model_name)s']
