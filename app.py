"""
Web pública de Salimos.

Es la cara que ve el público: muestra los eventos culturales de Berisso que
ya fueron aprobados en el panel admin. Usa el mismo stack: Flask + htmx.

Flujo de datos:
  panel admin (scraping)  ->  base de datos  ->  este sitio web (solo lectura)

Los filtros (categoría, día y búsqueda) se pasan por query string y la ruta
principal se renderiza completa en el servidor. Los eventos se agrupan por
día con su encabezado ('Viernes, 11 de septiembre · 1 evento').
"""

import sys
import os
from datetime import datetime

# Agregamos la raíz al path para poder importar el paquete "backend".
sys.path.insert(0, os.path.dirname(__file__))

from urllib.parse import urlencode

from flask import Flask, render_template, request, abort, Response
from psycopg2 import Binary

from backend.eventos import (
    obtener_categorias,
    obtener_dias,
    obtener_eventos_aprobados,
    obtener_evento_por_id,
    categoria_bonita,
    normalizar_categoria,
)
from backend.formato import (
    nombre_dia_corto,
    nombre_mes_corto,
    encabezado_dia,
    hora_display,
    precio_display,
)
from backend.db import conectar
from backend.solicitudes import solicitudes_habilitadas, crear_solicitud

# Tamaño máximo permitido para la imagen que sube el público (6 MB).
MAX_IMAGEN = 6 * 1024 * 1024

app = Flask(__name__)


def agrupar_por_dia(eventos: list[dict]) -> list[tuple]:
    """
    Agrupa eventos por su fecha (sin hora) y devuelve una lista ordenada
    de tuplas (fecha, [eventos]) para que la plantilla pinte cada grupo.
    """
    grupos: dict = {}
    for evento in eventos:
        fecha = evento["fecha_hora"].date()
        grupos.setdefault(fecha, []).append(evento)
    return sorted(grupos.items())


def misma_categoria(elegida: str | None, categoria: str | None) -> bool:
    """
    True si la categoría seleccionada en la URL es la misma que la de la
    píldora. Compara sin distinguir mayúsculas ni espacios, igual que el
    filtro de la base, para que la píldora activa siempre quede marcada.
    """
    if not normalizar_categoria(elegida):
        return False
    return normalizar_categoria(elegida) == normalizar_categoria(categoria)


# --- Rutas ---


@app.route("/")
def root():
    """Página principal: header, filtros y grilla de eventos (todo server-side)."""
    categoria = request.args.get("categoria", "").strip()
    dia = request.args.get("dia", "").strip()
    busqueda = request.args.get("q", "").strip()

    eventos = obtener_eventos_aprobados(
        categoria=categoria or None,
        dia=dia or None,
        busqueda=busqueda or None,
    )

    return render_template(
        "index.html",
        pagina="inicio",
        agrupados=agrupar_por_dia(eventos),
        categorias=obtener_categorias(),
        dias=obtener_dias(),
        categoria_activa=categoria,
        dia_activo=dia,
        busqueda=busqueda,
        solicitudes_activas=solicitudes_habilitadas(),
    )


@app.route("/mis-recordatorios")
def mis_recordatorios():
    """Página con los eventos guardados en localStorage."""
    return render_template(
        "index.html",
        pagina="recordatorios",
        agrupados=[],
        categorias=obtener_categorias(),
        dias=obtener_dias(),
        categoria_activa="",
        dia_activo="",
        busqueda="",
        solicitudes_activas=solicitudes_habilitadas(),
    )


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


@app.route("/solicitudes", methods=["POST"])
def recibir_solicitud():
    """
    Recibe la solicitud del botón flotante y la guarda para que el admin la
    revise. Solo disponible si el panel prendió el interruptor
    (`solicitudes_habilitadas`), si no es 404.
    """
    if not solicitudes_habilitadas():
        abort(404)

    def respuesta(ok: bool, mensaje: str, codigo: int = 200):
        return (
            render_template(
                "partials/solicitud_respuesta.html",
                ok=ok,
                mensaje=mensaje,
            ),
            codigo,
        )

    # Trampa para bots: este campo lo ve nadie (está oculto). Si viene lleno,
    # es un robot: respondemos igual pero descartamos todo en silencio.
    if request.form.get("website"):
        return respuesta(True, "¡Gracias! Recibimos tu solicitud.")

    titulo = request.form.get("titulo", "").strip()
    fecha = request.form.get("fecha", "").strip()
    hora = request.form.get("hora", "").strip() or "00:00"

    if not titulo or not fecha:
        return respuesta(False, "Completá al menos el título y la fecha.", 400)

    try:
        fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
    except ValueError:
        return respuesta(False, "La fecha o la hora no son válidas.", 400)

    imagen_datos = None
    imagen_mime = None
    archivo = request.files.get("imagen")
    if archivo and archivo.filename:
        contenido = archivo.read()
        if len(contenido) > MAX_IMAGEN:
            return respuesta(False, "La imagen es muy pesada (máximo 6 MB).", 400)
        imagen_datos = Binary(contenido)
        imagen_mime = archivo.mimetype or None

    try:
        crear_solicitud(
            {
                "titulo": titulo,
                "fecha_hora": fecha_hora,
                "lugar": request.form.get("lugar", "").strip() or None,
                "categoria": request.form.get("categoria", "").strip() or None,
                "precio": request.form.get("precio", "").strip() or None,
                "descripcion": request.form.get("descripcion", "").strip() or None,
                "link_fuente": request.form.get("link_fuente", "").strip() or None,
                "contacto": request.form.get("contacto", "").strip() or None,
                "imagen_datos": imagen_datos,
                "imagen_mime": imagen_mime,
            }
        )
    except Exception:
        return respuesta(
            False,
            "No pudimos registrar la solicitud. Probá de nuevo más tarde.",
            500,
        )

    return respuesta(True, "¡Gracias! Recibimos tu solicitud. El equipo de la agenda la va a revisar.")


@app.route("/imagenes/eventos/<int:evento_id>")
def imagen_evento(evento_id: int):
    """
    Sirve la imagen de un evento desde la base de datos (columna imagen_datos).

    La base es la única fuente de verdad para las imágenes: el panel admin las
    sube ahí durante el scraping y esta web las lee y las sirve a los visitantes.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT imagen_datos, imagen_mime FROM eventos WHERE id = %s",
        (evento_id,),
    )
    fila = cursor.fetchone()
    cursor.close()
    conexion.close()

    if fila is None or not fila[0] or len(fila[0]) == 0:
        abort(404)

    return Response(
        bytes(fila[0]),
        mimetype=fila[1] or "image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# --- Helpers disponibles para cualquier plantilla ---


@app.template_filter("categoria_bonita")
def _categoria_bonita(categoria):
    return categoria_bonita(categoria)


@app.template_global()
def url_filtros(**cambios):
    """
    Arma la URL de la home conservando los filtros actuales y aplicando los
    cambios pedidos; los filtros que quedan vacíos se omiten del querystring.

    Es lo que hace reversibles las píldoras: la píldora activa de una categoría
    (o de un día) se enlaza a la MISMA url sin ese filtro, así que un clic la
    desactiva y se vuelve a "Todas". También la usa el buscador.
    """
    filtros = {
        "categoria": request.args.get("categoria", "").strip(),
        "dia": request.args.get("dia", "").strip(),
        "q": request.args.get("q", "").strip(),
    }
    filtros.update(cambios)
    activos = {clave: valor for clave, valor in filtros.items() if valor}
    if not activos:
        return "/"
    return "/?" + urlencode(activos)


@app.context_processor
def utilidades_de_plantilla():
    """Expone los helpers de fechas y categorías a las plantillas."""
    return {
        "nombre_dia_corto": nombre_dia_corto,
        "nombre_mes_corto": nombre_mes_corto,
        "encabezado_dia": encabezado_dia,
        "hora_display": hora_display,
        "precio_display": precio_display,
        "categoria_bonita": categoria_bonita,
        "misma_categoria": misma_categoria,
    }


# Si ejecutamos este archivo directamente, corre el servidor de desarrollo.
# Puerto 5001 para poder tener la web y el panel admin (5000) a la vez.
# En Render el puerto lo inyecta la plataforma en la variable PORT, así que
# ahí el 5001 no se usa. El host 0.0.0.0 permite entrar desde el celular en la
# misma red.
if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5001")),
    )