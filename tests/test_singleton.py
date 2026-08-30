from src.resources import ResourceManager


def test_resource_singleton():
    assert ResourceManager() == ResourceManager()
