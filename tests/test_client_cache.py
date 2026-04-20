from __future__ import annotations

from types import SimpleNamespace

import tavern_grpc_web.client as client_module
from tavern_grpc_web.client import GRPCWebSession


class _InputMessage:
    pass


class _OutputMessage:
    pass


class _FakeService:
    def __init__(self, method_name: str, method_descriptor: object) -> None:
        self._method_name = method_name
        self._method_descriptor = method_descriptor
        self.find_method_calls = 0

    def FindMethodByName(self, method: str) -> object:
        self.find_method_calls += 1
        assert method == self._method_name
        return self._method_descriptor


class _FakePool:
    def __init__(self, service_name: str, service: _FakeService) -> None:
        self._service_name = service_name
        self._service = service
        self.find_service_calls = 0

    def FindServiceByName(self, service: str) -> _FakeService:
        self.find_service_calls += 1
        assert service == self._service_name
        return self._service


def test_get_method_types_uses_cache(monkeypatch) -> None:
    input_descriptor = object()
    output_descriptor = object()
    method_descriptor = SimpleNamespace(
        input_type=input_descriptor,
        output_type=output_descriptor,
    )
    fake_service = _FakeService("SayHello", method_descriptor)
    fake_pool = _FakePool("helloworld.v1.Greeter", fake_service)

    descriptor_to_cls = {
        input_descriptor: _InputMessage,
        output_descriptor: _OutputMessage,
    }
    monkeypatch.setattr(client_module, "GetMessageClass", lambda descriptor: descriptor_to_cls[descriptor])

    session = object.__new__(GRPCWebSession)
    session.sym_db = SimpleNamespace(pool=fake_pool)
    session._method_type_cache = {}

    first = session.get_method_types("helloworld.v1.Greeter", "SayHello")
    second = session.get_method_types("helloworld.v1.Greeter", "SayHello")

    assert first == (_InputMessage, _OutputMessage)
    assert second == (_InputMessage, _OutputMessage)
    assert second is first
    assert fake_pool.find_service_calls == 1
    assert fake_service.find_method_calls == 1
