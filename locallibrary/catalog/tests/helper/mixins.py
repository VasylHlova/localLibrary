from http import HTTPStatus

class PermissionViewTestMixin:
    url = None

    def test_redirects_to_login_if_anonymous(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_returns_403_without_permissions(self):
        self.client.force_login(self.user_no_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_returns_200_with_permissions(self):
        self.client.force_login(self.user_with_perms)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)