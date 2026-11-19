"""Estimaciones diarias y evaluación temporal de Madrid Pádel."""
from functools import lru_cache
from importlib.metadata import version
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

BASE = Path(__file__).resolve().parent
CENTRO = 'Centro deportivo'


@lru_cache(maxsize=1)
def cargar_modelo():
    meta = json.loads((BASE / 'modelos/metadatos_modelo.json').read_text(encoding='utf-8'))
    for nombre in ['numpy', 'pandas', 'scikit-learn', 'joblib']:
        if version(nombre) != meta['versiones'][nombre]:
            raise RuntimeError(f"Versión incompatible de {nombre}: se necesita {meta['versiones'][nombre]}. Instala requirements.txt.")
    paquete = joblib.load(BASE / 'modelos/modelo_diario.joblib')
    return paquete, meta


def crear_X(tabla):
    X = tabla[[CENTRO, 'fecha']].copy()
    fechas = pd.to_datetime(X['fecha'])
    X[CENTRO] = X[CENTRO].astype(str)
    X['dia_semana'] = fechas.dt.day_of_week.astype(str)
    X['mes'] = fechas.dt.month.astype(str)
    dias_anio = np.where(fechas.dt.is_leap_year, 366, 365)
    angulo = 2 * np.pi * (fechas.dt.day_of_year - 1) / dias_anio
    X['seno_anual'] = np.sin(angulo)
    X['coseno_anual'] = np.cos(angulo)
    return X[[CENTRO, 'dia_semana', 'mes', 'seno_anual', 'coseno_anual']]


def predecir(centro):
    paquete, _ = cargar_modelo()
    if centro not in paquete['centros_elegibles']:
        return pd.DataFrame()
    origen = pd.Timestamp(paquete['ultima_fecha_historica']) + pd.Timedelta(days=1)
    tabla = pd.DataFrame({CENTRO: centro, 'fecha': pd.date_range(origen, periods=paquete['horizonte_dias'])})
    ref = paquete['referencia']
    aux = tabla.assign(dia_semana=tabla['fecha'].dt.day_of_week)
    aux = aux.merge(ref['por_centro_dia'], on=[CENTRO, 'dia_semana'], how='left', sort=False, validate='many_to_one')
    tabla['pred_referencia'] = aux['pred_ref'].fillna(aux[CENTRO].map(ref['por_centro'])).fillna(ref['global']).to_numpy()
    with threadpool_limits(limits=2):
        tabla['pred_modelo'] = paquete['pipeline_candidato'].predict(crear_X(tabla))
    elegida = 'pred_modelo' if paquete['metodo_elegido'] == 'modelo' else 'pred_referencia'
    tabla['estimacion_condicional'] = tabla[elegida]
    tabla['metodo_elegido'] = paquete['metodo_elegido']
    tabla['interpretacion'] = 'Estimación condicionada a un día con registros; no confirma apertura'
    return tabla


@lru_cache(maxsize=1)
def cargar_evaluacion():
    return pd.read_csv(BASE / 'Datos/modelo/predicciones_test.csv', parse_dates=['fecha', 'origen'])


def evaluar_centro(centro):
    tabla = cargar_evaluacion()
    tabla = tabla.loc[tabla[CENTRO].eq(centro)].copy()
    observados = tabla.dropna(subset=['reservas_registradas'])
    filas = []
    for metodo, columna in [('Referencia', 'pred_referencia'), ('Modelo', 'pred_modelo')]:
        error = observados[columna] - observados['reservas_registradas']
        filas.append({'Método': metodo, 'MAE': error.abs().mean(),
                      'RMSE': np.sqrt((error ** 2).mean()), 'Sesgo': error.mean(),
                      'Días evaluados': len(error)})
    return tabla, pd.DataFrame(filas)
