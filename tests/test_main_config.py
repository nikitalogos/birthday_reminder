import yaml

from birthday_reminder.configs.main_config import DEFAULT_CONFIG_FILE, MainConfig


class TestMainConfig:
    def test_default_config_is_ok(self):
        config = MainConfig()
        config._validate(config.get_public_vars())

    def test_default_config_file_is_ok(self):
        config = MainConfig()
        config.set_file_path(DEFAULT_CONFIG_FILE)
        config.load_from_file()
        config._validate(config.get_public_vars())

    def test_default_config_file_has_same_params(self):
        with open(DEFAULT_CONFIG_FILE, encoding="utf-8") as f:
            file_config = yaml.safe_load(f)

        config = MainConfig()
        code_config = config.get_public_vars()
        del code_config["input_file"]  # it's not in the file because we can't set absolute path dynamically in yaml
        assert file_config == code_config

    CONFIG_YAML_STR = """
        input_file: "Birthdays.txt"
        use_zodiac_signs: true
        use_zodiac_names: true
        title_prefix: "Birthday of "
        title_postfix: " 🎂"
        calendar_name: "Birthdays"
        google_oauth_port: 1025
        use_time: true
        time_zone: "Europe/Moscow"
        event_time: "09:00"
        event_duration: "00:30"
        remind_29_feb_on_1_mar: true
        popup_reminders_minutes: [10, 30]
        email_reminders_minutes: [60, 1440]
        verbose: 0
        """

    def test_configure_from_file_works(self, tmpdir):
        config_file = tmpdir.join("config.yaml")
        config_file.write(self.CONFIG_YAML_STR)

        config = MainConfig()
        config.set_file_path(config_file)
        config.load_from_file()
        assert config.get_public_vars() == yaml.safe_load(self.CONFIG_YAML_STR)

    def test_configure_from_dict_works(self, tmpdir):
        config2 = MainConfig()
        config2.set_public_vars(yaml.safe_load(self.CONFIG_YAML_STR))
        assert config2.get_public_vars() == yaml.safe_load(self.CONFIG_YAML_STR)
