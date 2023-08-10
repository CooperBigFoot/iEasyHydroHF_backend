class TestUserModelController:
    def test_display_name_for_user_with_first_and_last_name(self, inactive_user):
        assert inactive_user.display_name == "Deleted User"

    def test_display_name_for_user_without_first_or_last_name(self, user_without_first_last_name):
        assert user_without_first_last_name.display_name == "my_display_name"

    def test_display_name_for_user_with_only_first_name(self, user_with_only_first_name):
        assert user_with_only_first_name.display_name == "my_display_name"

    def test_display_name_for_user_with_only_last_name(self, user_with_only_last_name):
        assert user_with_only_last_name.display_name == "my_display_name"

    def test_is_admin_for_regular_user(self, regular_user):
        assert regular_user.is_admin is False

    def test_is_admin_for_organization_admin(self, organization_admin):
        assert organization_admin.is_admin

    def test_is_admin_for_super_admin(self, superadmin):
        assert superadmin.is_admin

    def test_is_organization_admin_for_regular_user(self, regular_user):
        assert regular_user.is_organization_admin is False

    def test_is_organization_admin_for_organization_admin(self, organization_admin):
        assert organization_admin.is_organization_admin

    def test_is_organization_admin_for_super_admin(self, superadmin):
        assert superadmin.is_organization_admin is False

    def test_is_super_admin_for_regular_user(self, regular_user):
        assert regular_user.is_superadmin is False

    def test_is_super_admin_for_organization_admin(self, organization_admin):
        assert organization_admin.is_superadmin is False

    def test_is_super_admin_for_super_admin(self, superadmin):
        assert superadmin.is_superadmin
