import numpy as np

from pipeline.vecinos import construir_arbol, vecinos_mas_cercanos


def test_ckdtree_encuentra_el_vecino_mas_cercano():
    puntos = np.array([[19.2433, -103.725], [19.2452, -104.299]])
    arbol = construir_arbol(puntos)
    distancias, indices = vecinos_mas_cercanos(arbol, [[19.2440, -103.724]])
    assert indices[0] == 0
    assert distancias[0] >= 0


def test_ckdtree_rechaza_coordenadas_invalidas():
    try:
        construir_arbol([[19.0]])
    except ValueError:
        return
    raise AssertionError("debería rechazar coordenadas sin longitud")
