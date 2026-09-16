"""
Formateo de fechas y textos en español para la web pública.

strftime con locale no es confiable en todos los sistemas, así que usamos
listas propias para los nombres de días y meses.
"""

DIAS_SEMANA = [
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
]

DIAS_SEMANA_CORTO = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

MESES_CORTO = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# Palabras que indican que un evento es gratuito (para mostrar "Entrada gratuita").
_PALABRAS_GRATIS = ("grat", "libre", "sin cargo", "sin costo", "no pag", "entrada libre")


def precio_display(precio) -> str | None:
    """Normaliza el precio para la tarjeta.

    - Sin precio (None/'') -> None (la línea no se muestra).
    - Gratis ('Libre y gratuita', 'Gratis'...) -> 'Entrada gratuita'.
    - Con costo -> el texto tal cual ('Desde $35.000').
    """
    if not precio:
        return None

    texto = str(precio).strip()
    if not texto:
        return None

    minusculas = texto.lower()
    if any(palabra in minusculas for palabra in _PALABRAS_GRATIS):
        return "Entrada gratuita"

    return texto


def nombre_dia(fecha) -> str:
    """'viernes' (en minúscula, como corresponde dentro de una frase)."""
    return DIAS_SEMANA[fecha.weekday()]


def nombre_dia_corto(fecha) -> str:
    """'vie' para las píldoras de día tipo calendario."""
    return DIAS_SEMANA_CORTO[fecha.weekday()]


def nombre_mes(fecha) -> str:
    return MESES[fecha.month - 1]


def nombre_mes_corto(fecha) -> str:
    return MESES_CORTO[fecha.month - 1]


def encabezado_dia(fecha, cantidad: int) -> str:
    """'Viernes, 11 de septiembre · 1 evento' (o '2 eventos')."""
    palabra = "evento" if cantidad == 1 else "eventos"
    return f"{nombre_dia(fecha).capitalize()}, {fecha.day} de {nombre_mes(fecha)} · {cantidad} {palabra}"


def hora_display(fecha_hora) -> str:
    """Hora corta de un evento. Si es medianoche, es un evento 'de día completo'."""
    if fecha_hora.hour == 0 and fecha_hora.minute == 0:
        return "Todo el día"
    return f"{fecha_hora:%H:%M} hs"