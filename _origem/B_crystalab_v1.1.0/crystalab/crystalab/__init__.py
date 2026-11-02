"""CrystaLab — Módulo 1 do Alloy (Fundamentos Estruturais).

Pacote organizado em três camadas independentes:

* ``crystalab.core`` — motor cristalográfico puro (sem FastAPI), dados e exportadores;
* ``crystalab.api``  — aplicação FastAPI (rotas v1, rotas legadas, segurança);
* ``crystalab.web``  — interface (HTML/CSS/JS estáticos e Three.js local).

A versão abaixo é a ÚNICA fonte de versão do módulo (achado EX-07): CIF, OpenAPI,
cabeçalho da UI e manifesto leem daqui.
"""

__version__ = "1.1.0"

__all__ = ["__version__"]
