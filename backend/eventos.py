"""
Consultas de eventos para la web pública.

La regla de oro: acá SOLO se muestran eventos que ya fueron APROBADOS en el
panel admin. Los que estén con aprobado=false no se ven en la web.
"""

from backend.db import conectar


def _resolver_imagen(eventos):
    """
    Convierte la presencia de imagen en la BD a una URL servible.

    La imagen vive en la columna imagen_datos (BYTEA). La "URL" que se pasa a
    las plantillas es una ruta interna (/imagenes/eventos/<id>) que ESTA app
    sirve desde la base. Si el evento no tiene imagen, queda None y la tarjeta
    muestra el placeholder en lugar de una foto rota.
    """
    for evento in eventos:
        if evento.get("tiene_imagen"):
            evento["imagen_url"] = f"/imagenes/eventos/{evento['id']}"
        else:
            evento["imagen_url"] = None


def categoria_bonita(categoria: str | None) -> str | None:
    """'cine' -> 'Cine'; 'academia de danza' -> 'Academia De Danza'."""
    if not categoria:
        return categoria
    return " ".join(palabra.capitalize() for palabra in categoria.split())


def normalizar_categoria(categoria: str | None) -> str:
    """
    Deja una categoría en una forma comparable: sin espacios sobrantes y en
    minúsculas. La usan el filtro de la web y la plantilla para que elegir una
    categoría siempre encuentre eventos y la píldora quede marcada como activa
    (si no, no hay forma de volver a "Todas").
    """
    return str(categoria or "").strip().casefold()


def obtener_categorias() -> list[str]:
    """Categorías de los eventos aprobados y futuros (para las píldoras)."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT DISTINCT categoria
        FROM eventos
        WHERE aprobado = true
          AND fecha_hora >= NOW()
          AND categoria IS NOT NULL
          AND categoria != ''
        ORDER BY categoria ASC
        """
    )
    categorias = [fila[0] for fila in cursor.fetchall()]
    cursor.close()
    conexion.close()
    return categorias


def obtener_dias() -> list:
    """Días (fechas) con eventos aprobados y futuros, ordenados de más próximo a más lejano."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT DISTINCT fecha_hora::date AS dia
        FROM eventos
        WHERE aprobado = true
          AND fecha_hora >= NOW()
        ORDER BY dia ASC
        """
    )
    dias = [fila[0] for fila in cursor.fetchall()]
    cursor.close()
    conexion.close()
    return dias


def obtener_eventos_aprobados(
    categoria: str | None = None,
    dia: str | None = None,
    busqueda: str | None = None,
) -> list[dict]:
    """
    Devuelve los eventos aprobados que aún NO pasaron, ordenados por fecha
    (el más próximo primero). Acepta filtros opcionales:

      - categoria: nombre de categoría (se compara sin distinguir mayúsculas).
      - dia:       fecha "YYYY-MM-DD" para filtrar por día puntual.
      - busqueda:  texto libre que se busca en título, lugar y descripción.
    """
    condiciones = ["aprobado = true", "fecha_hora >= NOW()"]
    parametros: list = []

    if categoria:
        condiciones.append("lower(btrim(categoria)) = %s")
        parametros.append(normalizar_categoria(categoria))

    if dia:
        condiciones.append("fecha_hora::date = %s")
        parametros.append(dia)

    if busqueda:
        condiciones.append(
            "(titulo ILIKE %s OR lugar ILIKE %s OR descripcion ILIKE %s OR categoria ILIKE %s)"
        )
        patron = f"%{busqueda}%"
        parametros += [patron, patron, patron, patron]

    consulta = f"""
        SELECT id, titulo, fecha_hora, lugar, categoria, precio,
               descripcion, imagen_url, link_fuente,
               (imagen_datos IS NOT NULL AND octet_length(imagen_datos) > 0) AS tiene_imagen
        FROM eventos
        WHERE {" AND ".join(condiciones)}
        ORDER BY fecha_hora ASC
    """

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(consulta, parametros)
    columnas = [desc[0] for desc in cursor.description]
    eventos = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    cursor.close()
    conexion.close()

    # La fecha se deja como datetime; la plantilla la formatea y agrupa por día.
    # Las imágenes se sirven desde la BD (ruta /imagenes/eventos/<id>) y las
    # que no tienen imagen quedan con None (placeholder en la tarjeta).
    _resolver_imagen(eventos)
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
               descripcion, link_fuente, imagen_url,
               (imagen_datos IS NOT NULL AND octet_length(imagen_datos) > 0) AS tiene_imagen
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
    _resolver_imagen([evento])
    return evento