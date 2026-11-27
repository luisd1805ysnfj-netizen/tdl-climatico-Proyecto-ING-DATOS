"""Todas las pruebas corren OFFLINE: si algo intenta abrir una conexión, la prueba falla."""
import socket

import pytest


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    def _bloqueado(*args, **kwargs):
        raise RuntimeError("Prueba offline: no se permite acceso a la red")
    monkeypatch.setattr(socket.socket, "connect", _bloqueado)
