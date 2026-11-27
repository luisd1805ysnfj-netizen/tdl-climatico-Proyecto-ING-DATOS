"""Pruebas OFFLINE: si algo intenta abrir una conexión, la prueba falla. Fixtures compartidos."""
import json
import socket

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    def _bloqueado(*args, **kwargs):
        raise RuntimeError("Prueba offline: no se permite acceso a la red")
    monkeypatch.setattr(socket.socket, "connect", _bloqueado)


def escribir_json_open_meteo(ruta, dias=60, lat=19.2267, lon=-103.7092, semilla=1):
    """Archivo sintético con la MISMA estructura que devuelve Open-Meteo."""
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2025-01-01", periods=dias, freq="D").strftime("%Y-%m-%d").tolist()
    ruta.write_text(json.dumps({
        "latitude": lat, "longitude": lon, "elevation": 100.0, "timezone": "America/Mexico_City",
        "daily_units": {"time": "iso8601", "temperature_2m_max": "°C", "temperature_2m_min": "°C",
                        "precipitation_sum": "mm", "wind_speed_10m_max": "km/h"},
        "daily": {
            "time": fechas,
            "temperature_2m_max": (31 + rng.normal(0, 1.5, dias)).round(1).tolist(),
            "temperature_2m_min": (21 + rng.normal(0, 1.5, dias)).round(1).tolist(),
            "precipitation_sum": np.where(rng.random(dias) < 0.4, rng.gamma(1.2, 6, dias), 0).round(1).tolist(),
            "wind_speed_10m_max": (14 + rng.normal(0, 3, dias)).round(1).tolist(),
        }}), encoding="utf-8")


@pytest.fixture()
def bronce_linaje(tmp_path):
    carpeta = tmp_path / "bronce"
    carpeta.mkdir()
    for i, mun in enumerate(["tecoman", "colima", "manzanillo"]):
        escribir_json_open_meteo(carpeta / f"clima_historico_{mun}_20261109.json", semilla=i)
    return carpeta
