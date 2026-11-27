"""Búsqueda espacial optimizada con scipy.spatial.cKDTree."""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def construir_arbol(coordenadas):
    coordenadas = np.asarray(coordenadas, dtype=float)
    if coordenadas.ndim != 2 or coordenadas.shape[1] != 2:
        raise ValueError("coordenadas debe tener forma (n, 2): latitud, longitud")
    if len(coordenadas) == 0:
        raise ValueError("se necesita al menos una coordenada")
    return cKDTree(coordenadas)


def vecinos_mas_cercanos(arbol, coordenadas, k=1):
    coordenadas = np.asarray(coordenadas, dtype=float)
    if coordenadas.ndim != 2 or coordenadas.shape[1] != 2:
        raise ValueError("coordenadas debe tener forma (n, 2): latitud, longitud")
    distancias, indices = arbol.query(coordenadas, k=k)
    return np.asarray(distancias), np.asarray(indices)
