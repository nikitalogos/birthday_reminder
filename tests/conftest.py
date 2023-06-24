import os.path

import pytest


class Utils:
    @staticmethod
    def test_resource(path):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_resources", path)


@pytest.fixture(scope="session")
def utils():
    return Utils
