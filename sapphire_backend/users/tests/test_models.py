class TestUserModelController:
    def test_display_name_for_user_with_first_and_last_name(self, inactive_user):
        assert inactive_user.display_name == "Deleted User"

    def test_display_name_for_user_without_first_or_last_name(self, user_without_first_last_name):
        assert user_without_first_last_name.display_name == "my_display_name"

    def test_display_name_for_user_with_only_first_name(self, user_with_only_first_name):
        assert user_with_only_first_name.display_name == "my_display_name"

    def test_display_name_for_user_with_only_last_name(self, user_with_only_last_name):
        assert user_with_only_last_name.display_name == "my_display_name"
