from onboarding.ui.pages import GRAPH_MAX_WIDTH, GRAPH_MIN_WIDTH, GRAPH_WIDTH, graph_width


def test_el_ancho_guardado_del_grafo_se_respeta_dentro_de_los_limites() -> None:
    assert graph_width(800) == 800
    assert graph_width(812.6) == 812
    assert graph_width(100) == GRAPH_MIN_WIDTH
    assert graph_width(9999) == GRAPH_MAX_WIDTH


def test_sin_un_ancho_valido_usa_el_de_siempre() -> None:
    assert graph_width(None) == GRAPH_WIDTH
    assert graph_width("ancho") == GRAPH_WIDTH
    assert graph_width(True) == GRAPH_WIDTH
