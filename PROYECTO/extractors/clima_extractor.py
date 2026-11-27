import os
import json
import requests
from datetime import datetime, timedelta

MUNICIPIOS = {
    "tecoman": {"lat": 18.9125, "lon": -103.8753},
    "colima": {"lat": 19.2433, "lon": -103.7250},
    "manzanillo": {"lat": 19.0522, "lon": -104.3158}
}

USER_AGENT = "TDL-ObservatorioClimatico/1.0 (proyecto academico)"

def descargar_historico_bronce():
    fecha_fin = datetime.now() - timedelta(days=2)
    fecha_inicio = fecha_fin - timedelta(days=36 * 30)

    str_inicio = fecha_inicio.strftime("%Y-%m-%d")
    str_fin = fecha_fin.strftime("%Y-%m-%d")

    os.makedirs("data/bronce", exist_ok=True)
    headers = {"User-Agent": USER_AGENT}

    for nombre, coords in MUNICIPIOS.items():
        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={coords['lat']}&longitude={coords['lon']}&"
            f"start_date={str_inicio}&end_date={str_fin}&"
            f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max&"
            f"timezone=auto"
        )
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            filepath = f"data/bronce/clima_historico_{nombre}_{datetime.now().strftime('%Y%m%d')}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[OK] Datos guardados para {nombre} en {filepath}")
        else:
            print(f"[ERROR] No se pudo descargar datos de {nombre}: Status {response.status_code}")

if __name__ == "__main__":
    descargar_historico_bronce()