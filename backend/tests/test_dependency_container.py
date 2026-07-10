"""Unit tests for Tier 1 DependencyContainer service."""

import pytest

from app.services.core.dependency_container import (
    DependencyContainer,
    get_global_container,
)

pytestmark = pytest.mark.unit


class _Dummy:
    def __init__(self, value=None):
        self.value = value
        self.shutdown_called = False

    async def shutdown(self):
        self.shutdown_called = True


class TestDependencyContainer:
    def test_register_and_get_singleton(self, container):
        container.register("dummy", _Dummy, singleton=True, value=1)
        a = container.get("dummy")
        b = container.get("dummy")
        assert a is b  # same instance for singleton
        assert a.value == 1

    def test_register_non_singleton_returns_new_instances(self, container):
        container.register("dummy", _Dummy, singleton=False)
        a = container.get("dummy")
        b = container.get("dummy")
        assert a is not b

    def test_get_unregistered_raises_keyerror(self, container):
        with pytest.raises(KeyError):
            container.get("missing")

    def test_get_merges_kwargs(self, container):
        container.register("dummy", _Dummy, singleton=False, value=1)
        instance = container.get("dummy", value=99)
        assert instance.value == 99

    def test_factory_exception_propagates(self, container):
        def bad_factory():
            raise RuntimeError("cannot build")

        container.register("bad", bad_factory)
        with pytest.raises(RuntimeError, match="cannot build"):
            container.get("bad")

    def test_register_instance_stored_in_singletons(self, container):
        instance = _Dummy(value=42)
        container.register_instance("pre", instance)
        assert container.has("pre")
        assert container._singletons["pre"] is instance

    def test_register_instance_requires_factory_for_get(self, container):
        # Documents current behaviour: register_instance stores only in
        # _singletons, but get() looks in _factories first and raises.
        instance = _Dummy()
        container.register_instance("only_instance", instance)
        assert container.has("only_instance")
        with pytest.raises(KeyError):
            container.get("only_instance")

    def test_has(self, container):
        assert not container.has("x")
        container.register("x", _Dummy)
        assert container.has("x")

    def test_remove(self, container):
        container.register("x", _Dummy)
        container.get("x")
        container.remove("x")
        assert not container.has("x")

    async def test_shutdown_all_calls_shutdown(self, container):
        container.register("dummy", _Dummy, singleton=True)
        instance = container.get("dummy")
        await container.shutdown_all()
        assert instance.shutdown_called is True
        assert container.get_stats()["singleton_instances"] == 0  # singletons cleared

    async def test_shutdown_all_handles_service_without_shutdown(self, container):
        class NoShutdown:
            pass

        container.register("plain", NoShutdown, singleton=True)
        container.get("plain")
        # should not raise
        await container.shutdown_all()

    def test_get_stats(self, container):
        container.register("a", _Dummy)
        container.register("b", _Dummy)
        container.get("a")
        stats = container.get_stats()
        assert stats["registered_services"] == 2
        assert stats["singleton_instances"] == 1
        assert stats["uptime_seconds"] >= 0

    def test_repr(self, container):
        container.register("a", _Dummy)
        assert "DependencyContainer" in repr(container)


class TestGlobalContainer:
    def test_global_container_is_singleton(self):
        c1 = get_global_container()
        c2 = get_global_container()
        assert c1 is c2
        assert isinstance(c1, DependencyContainer)
