"""Cálculos de la aplicación: pandas, sin modificar los datos originales."""
from pathlib import Path
import pandas as pd

DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def cargar_datos(ruta):
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f'Falta {ruta}. Copia el CSV exportado por el notebook 02 en Datos/app/.')
    datos = pd.read_csv(ruta, encoding='utf-8-sig', parse_dates=['fecha'])
    columnas = ['fecha', 'Centro deportivo', 'hora_inicio_num', 'duracion_minutos']
    if not set(columnas).issubset(datos.columns):
        raise ValueError(f'El CSV debe incluir estas columnas: {columnas}')
    if datos.empty or datos[columnas].isna().any().any():
        raise ValueError('El CSV está vacío o contiene valores ausentes. Revisa la exportación.')
    datos['fecha'] = pd.to_datetime(datos['fecha'], errors='raise').dt.normalize()
    for columna in ['hora_inicio_num', 'duracion_minutos']:
        datos[columna] = pd.to_numeric(datos[columna], errors='raise')
    if not datos['hora_inicio_num'].between(0, 24, inclusive='left').all():
        raise ValueError('Las horas de inicio deben estar entre 0 y menos de 24.')
    if not datos['duracion_minutos'].between(0, 1440, inclusive='right').all():
        raise ValueError('Se han encontrado duraciones fuera de rango.')
    # Protección adicional: la exportación ya debe venir normalizada.
    datos['Centro deportivo'] = (datos['Centro deportivo'].astype('string')
        .str.normalize('NFC').str.replace(r'\s+', ' ', regex=True).str.strip()
        .replace({'CDM El Quijote': 'El Quijote'}))
    if datos['Centro deportivo'].eq('').any():
        raise ValueError('Hay centros sin nombre.')
    datos['hora'] = (datos['hora_inicio_num'] // 1).astype(int)
    datos['semana'] = datos['fecha'].dt.to_period('W-SUN').dt.start_time
    return datos


def filtrar(datos, centro, inicio, fin):
    mascara = datos['fecha'].between(inicio, fin)
    if centro and centro != '__todos__':
        mascara &= datos['Centro deportivo'].eq(centro)
    return datos.loc[mascara].copy()


def resumen_semanal(datos, inicio, fin):
    """Solo semanas lunes-domingo dentro de los límites seleccionados.

    Una semana sin registros se conserva como NaN. Que una semana quepa
    en el intervalo no certifica la integridad de sus datos.
    """
    inicio, fin = pd.Timestamp(inicio).normalize(), pd.Timestamp(fin).normalize()
    primer_lunes = inicio + pd.Timedelta(days=(-inicio.day_of_week) % 7)
    ultimo_lunes = fin - pd.Timedelta(days=fin.day_of_week)  # lunes de esa semana
    if ultimo_lunes + pd.Timedelta(days=6) > fin:
        ultimo_lunes -= pd.Timedelta(days=7)
    semanas = pd.date_range(primer_lunes, ultimo_lunes, freq='W-MON')
    agrupado = datos.groupby('semana').agg(
        reservas_registradas=('fecha', 'size'),
        centros_con_registros=('Centro deportivo', 'nunique'),
        dias_con_registros=('fecha', 'nunique'))
    tabla = agrupado.reindex(semanas).rename_axis('semana').reset_index()
    tabla['fin_semana'] = tabla['semana'] + pd.Timedelta(days=6)
    tabla['reservas_semana_anterior'] = tabla['reservas_registradas'].shift(1)
    tabla['centros_semana_anterior'] = tabla['centros_con_registros'].shift(1)
    anterior = tabla['reservas_semana_anterior'].where(tabla['reservas_semana_anterior'] > 0)
    tabla['variacion_pct'] = (tabla['reservas_registradas'] / anterior - 1) * 100
    tabla['cambio_numero_centros'] = tabla['centros_con_registros'] - tabla['centros_semana_anterior']
    return tabla


def patron_horario(datos):
    """Media de inicios por fecha con algún registro individual (todos los centros filtrados)."""
    conteos = (datos.groupby(['fecha', 'hora']).size().unstack('hora', fill_value=0)
               .reindex(columns=range(24), fill_value=0))
    media = conteos.groupby(conteos.index.day_of_week).mean().reindex(range(7))
    fechas = (datos[['fecha']].drop_duplicates()
              .assign(dia=lambda x: x['fecha'].dt.day_of_week)
              .groupby('dia').size().reindex(range(7), fill_value=0))
    media.index = DIAS
    fechas.index = DIAS
    return media, fechas
