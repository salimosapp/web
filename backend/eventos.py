"""
Consultas de eventos para la web pública.

La regla de oro: acá SOLO se muestran eventos que ya fueron APROBADOS en el
panel admin. Los que estén con aprobado=false no se ven en la web.
"""

from backend.db import conectar


def obtener_eventos_aprobados() -> list[dict]:
    """
    Devuelve los eventos aprobados que aún NO pasaron, ordenados por fecha
    (el más próximo primero). Es lo que ve un visitante de la web.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT id, titulo, fecha_hora, lugar, categoria, precio,
               descripcion, imagen_url
        FROM eventos
        WHERE aprobado = true
          AND fecha_hora >= NOW()
        ORDER BY fecha_hora ASC
        """
    )
    columnas = [desc[0] for desc in cursor.description]
    eventos = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    cursor.close()
    conexion.close()

    # La fecha llega como datetime de Python; la pasamos a texto legible.
    for evento in eventos:
        evento["fecha_hora"] = evento["fecha_hora"].strftime("%d/%m/%Y %H:%M")

    return eventos


def obtener_evento_por_id(evento_id: int) -> dict | None:
    """
    Devuelve UN evento por su id, pero solo si es aprobado y futuro.
    Si no existe (o está pendiente), devuelve None.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT id, titulo, fecha_hora, lugar, categoria, precio,
               descripcion, link_fuente, imagen_url
        FROM eventos
        WHERE id = %s AND aprobado = true AND fecha_hora >= NOW()
        """,
        (evento_id,),
    )
    columnas = [desc[0] for desc in cursor.description]
    fila = cursor.fetchone()
    cursor.close()
    conexion.close()

    if fila is None:
        return None

    evento = dict(zip(columnas, fila))
    evento["fecha_hora"] = evento["fecha_hora"].strftime("%d/%m/%Y %H:%M")
    return evento