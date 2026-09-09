"""
Web pública de Salimos.

Es la cara que ve el público: muestra los eventos culturales de Berisso que
ya fueron aprobados en el panel admin. Usa el mismo stack: Flask + htmx.

Flujo de datos:
  panel admin (scraping)  ->  base de datos  ->  este sitio web (solo lectura)
"""

import sys
import os

# Agregamos la raíz al path para poder importar el paquete "backend".
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, abort

from backend.eventos import obtener_eventos_aprobados, obtener_evento_por_id

app = Flask(__name__)


# --- Rutas ---


@app.route("/")
def root():
    """Página principal: layout con la grilla de eventos (se carga sola)."""
    return render_template("index.html", pagina="inicio")


@app.route("/eventos")
def eventos():
    """Parcial: la grilla con los eventos aprobados y futuros."""
    eventos = obtener_eventos_aprobados()
    return render_template("partials/eventos.html", eventos=eventos)


@app.route("/eventos/<int:evento_id>")
def evento_detalle(evento_id: int):
    """
    Parcial: detalle de UN evento. htmx lo carga sin recargar la página.
    Si el evento no existe o no está aprobado, respondemos 404.
    """
    evento = obtener_evento_por_id(evento_id)
    if evento is None:
        abort(404)
    return render_template("partials/evento_detalle.html", evento=evento)


# Si ejecutamos este archivo directamente, corre el servidor de desarrollo.
# Puerto 5001 para poder tener la web y el panel admin (5000) a la vez.
if __name__ == "__main__":
    app.run(port=5001)