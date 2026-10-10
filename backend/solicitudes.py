"""
Solicitudes de eventos enviadas por el público.

Esta web NO escribe en la tabla `eventos` (eso lo sigue haciendo, con
exclusividad, el panel admin). Lo único que agrega acá es una fila en
`solicitudes_eventos`: una propuesta que el panel revisa y, si quiere, aprueba.

El botón "Solicitar un evento" de la home depende de un interruptor que vive en
la tabla `configuracion` (clave `solicitudes_habilitadas`). Así el panel puede
prenderlo y apagarlo sin tocar esta app.

Ambas tablas las crea el panel admin en su primer arranque (acá solo se leen o
se insertan filas). Si no existen todavía, `solicitudes_habilitadas()` devuelve
False y el botón no aparece.
"""

from backend.db import conectar


def solicitudes_habilitadas() -> bool:
    """
    True solo si el panel admin prendió el interruptor de solicitudes.

    Es defensiva a propósito: si la tabla `configuracion` no existe o la base
    no responde, NO rompe la home (devuelve False y no se muestra el botón).
    La home es la prioridad; el formulario es un extra.
    """
    try:
        conexion = conectar()
        try:
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT valor FROM configuracion WHERE clave = %s",
                ("solicitudes_habilitadas",),
            )
            fila = cursor.fetchone()
            cursor.close()
        finally:
            conexion.close()
    except Exception:
        return False

    if not fila:
        return False
    return str(fila[0]).strip().lower() in {"true", "1", "on", "si", "sí"}


def crear_solicitud(datos: dict) -> None:
    """
    Inserta una solicitud del público en `solicitudes_eventos`.

    `datos` ya viene validado y normalizado desde la ruta. La imagen es
    opcional: si no hay, se guardan NULL en imagen_datos/imagen_mime.
    """
    conexion = conectar()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO solicitudes_eventos
                (titulo, fecha_hora, lugar, categoria, precio, descripcion,
                 link_fuente, contacto, imagen_datos, imagen_mime)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                datos["titulo"],
                datos["fecha_hora"],
                datos.get("lugar"),
                datos.get("categoria"),
                datos.get("precio"),
                datos.get("descripcion"),
                datos.get("link_fuente"),
                datos.get("contacto"),
                datos.get("imagen_datos"),
                datos.get("imagen_mime"),
            ),
        )
        conexion.commit()
        cursor.close()
    finally:
        conexion.close()
