"""Sección de predicción y evaluación de la aplicación."""
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html
from prediccion import cargar_modelo, predecir, evaluar_centro

COLOR_MODELO = '#2563eb'
COLOR_REFERENCIA = '#c05a16'


def numero(valor, decimales=2):
    if pd.isna(valor):
        return '—'
    return f'{valor:,.{decimales}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def figura(titulo_y='Registros por centro y día'):
    fig = go.Figure()
    fig.update_layout(template='plotly_white', height=420, hovermode='x unified',
                      margin=dict(l=45, r=20, t=35, b=65),
                      font=dict(family='Arial', color='#17243b'),
                      legend=dict(orientation='h', y=1.12),
                      xaxis_title='Fecha', yaxis_title=titulo_y)
    fig.update_yaxes(rangemode='tozero', gridcolor='#e8edf4')
    return fig


def tabla_html(tabla):
    filas = []
    for fila in tabla.itertuples(index=False, name=None):
        valores = [numero(x) if isinstance(x, (float, int)) else str(x) for x in fila]
        filas.append(html.Tr([html.Td(x) for x in valores]))
    return html.Table([html.Thead(html.Tr([html.Th(c) for c in tabla.columns])), html.Tbody(filas)])


def crear_panel(centros):
    paquete, meta = cargar_modelo()
    inicio = pd.Timestamp(paquete['ultima_fecha_historica']) + pd.Timedelta(days=1)
    fin = inicio + pd.Timedelta(days=paquete['horizonte_dias'] - 1)
    elegibles = set(paquete['centros_elegibles'])
    opciones = [{'label': c if c in elegibles else c + ' · sin previsión', 'value': c} for c in centros]
    return html.Section([
        html.Div([html.Span('MODELO DIARIO', className='eyebrow'),
                  html.H2('03 / Predicción y evaluación'),
                  html.P(f'Demostración histórica · {inicio:%d/%m/%Y} — {fin:%d/%m/%Y}. Histórico hasta {pd.Timestamp(paquete["ultima_fecha_historica"]):%d/%m/%Y}.')], className='prediction-heading'),
        html.P('Estimaciones para días con registros. No indican disponibilidad de pistas ni confirman que el centro abra. El periodo de esta sección es independiente del filtro de fechas del análisis histórico.', className='prediction-note'),
        html.Div([
            html.Div([html.Label('Centro de la predicción', htmlFor='centro-prediccion'),
                      dcc.Dropdown(id='centro-prediccion', options=opciones,
                                   value=next(c for c in centros if c in elegibles), clearable=False)], className='centro-filter'),
            html.Button('Descargar estimaciones ↓', id='descargar-prediccion', n_clicks=0, className='download'),
            dcc.Download(id='csv-prediccion')
        ], className='filters'),
        html.P(id='estado-prediccion', className='status', role='status'),
        dcc.Loading(html.Div([
            html.Div(id='kpis-prediccion', className='kpis'),
            html.Div([
                html.Section([html.H2('Estimaciones para siete días'),
                    html.P('Modelo y referencia histórica. Los decimales representan valores estimados, no reservas confirmadas.', className='panel-note'),
                    dcc.Graph(id='grafico-prevision', responsive=True, style={'height': '420px'}, config={'displaylogo': False})], className='panel'),
                html.Section([html.H2('Comparación en la prueba final'),
                    html.P('29/06/2026–30/08/2026. Predicciones emitidas antes de observar cada semana. Los huecos indican objetivos no observados.', className='panel-note'),
                    dcc.Graph(id='grafico-test', responsive=True, style={'height': '420px'}, config={'displaylogo': False})], className='panel')
            ], className='charts'),
            html.Details([html.Summary('Ver estimaciones diarias y errores del centro'),
                          html.Div(id='tabla-prevision', className='table-scroll'),
                          html.Div(id='tabla-error', className='table-scroll')], className='panel details')
        ]), color=COLOR_MODELO),
        html.Details([
            html.Summary('Método, resultados globales y límites'),
            html.P('He comparado una media histórica por centro y día de la semana con un modelo HistGradientBoosting de variables de calendario. He seleccionado el método utilizando únicamente el MAE de validación.'),
            tabla_html(pd.DataFrame([
                {'Bloque': bloque, 'Método': metodo, 'MAE': valores['MAE'], 'RMSE': valores['RMSE'], 'Sesgo': valores['sesgo'], 'Días evaluados': valores['n_dias_centro']}
                for bloque, clave in [('Validación', 'metricas_validacion'), ('Prueba', 'metricas_test')]
                for metodo, valores in meta[clave].items()
            ])),
            html.P('En validación, los métodos están prácticamente empatados. La mejora en prueba corresponde a un periodo de verano y no garantiza el mismo resultado en otras estaciones.'),
            html.P('La evaluación solo utiliza centro-días con registros observados. La ausencia de registros no se convierte en cero. Un sesgo positivo indica sobreestimación.'),
            html.P('En la evaluación temporal he reentrenado cada lunes con fechas anteriores. La aplicación carga el modelo final guardado. Para emitir la demostración se exigen al menos 28 días históricos observados y 14 en los últimos 56 días; 40 de los 45 centros cumplen esos criterios.'),
            html.P('Se supone disponible el histórico anterior a cada previsión; no se reproduce el retraso mensual de publicación de los datos. No se han estimado intervalos de predicción.')
        ], className='panel details table-scroll')
    ], className='prediction-section', id='predicciones')


def actualizar_prediccion(centro):
    paquete, _ = cargar_modelo()
    prevision = predecir(centro)
    test, errores = evaluar_centro(centro)
    metodo = 'Modelo' if paquete['metodo_elegido'] == 'modelo' else 'Referencia'
    metrica = errores.loc[errores['Método'].eq(metodo)].iloc[0]
    ref_mae = errores.iloc[0]['MAE']
    mejora = (1 - metrica['MAE'] / ref_mae) * 100 if pd.notna(ref_mae) and ref_mae > 0 else float('nan')
    def tarjeta(titulo, valor, detalle):
        return html.Div([html.P(titulo, className='kpi-label'), html.Div(valor, className='kpi-value'), html.P(detalle, className='kpi-detail')], className='kpi')
    kpis = [tarjeta('Método seleccionado', metodo, 'Selección global por validación'),
            tarjeta('MAE del centro en prueba', numero(metrica['MAE']), 'Registros por día observado'),
            tarjeta('Mejora frente a referencia', numero(mejora) + ' %' if pd.notna(mejora) else '—', 'Un valor negativo indica empeoramiento'),
            tarjeta('Días evaluados del centro', numero(metrica['Días evaluados'], 0), 'Objetivos observados en prueba')]
    fig_pre = figura()
    if prevision.empty:
        fig_pre.add_annotation(text='Sin suficiente histórico reciente para emitir la previsión.', x=.5, y=.5, xref='paper', yref='paper', showarrow=False)
        estado = f'{centro}: sin previsión. No cumple los criterios de apoyo histórico; esto no demuestra un cierre.'
        tabla_pre = html.P('No se emiten estimaciones para este centro.')
    else:
        for col, nombre, color, dash in [('pred_modelo', 'Modelo', COLOR_MODELO, 'solid'), ('pred_referencia', 'Referencia', COLOR_REFERENCIA, 'dash')]:
            fig_pre.add_trace(go.Scatter(x=prevision['fecha'], y=prevision[col], name=nombre, mode='lines+markers', line=dict(color=color, dash=dash)))
        estado = f'{centro}: siete estimaciones diarias condicionadas a días con registros. Método seleccionado: {metodo.lower()}.'
        tabla_pre = prevision[['fecha', 'pred_modelo', 'pred_referencia', 'estimacion_condicional']].copy()
        tabla_pre['fecha'] = tabla_pre['fecha'].dt.strftime('%d/%m/%Y')
        tabla_pre.columns = ['Fecha', 'Modelo', 'Referencia', 'Estimación seleccionada']
        tabla_pre = tabla_html(tabla_pre)
    fig_test = figura()
    if test.empty or test['reservas_registradas'].notna().sum() == 0:
        fig_test.add_annotation(text='Sin días observados evaluables en la prueba.', x=.5, y=.5, xref='paper', yref='paper', showarrow=False)
    else:
        test = test.set_index('fecha').reindex(pd.date_range('2026-06-29', '2026-08-30'))
        for col, nombre, color, dash in [('reservas_registradas', 'Observados', '#17243b', 'solid'), ('pred_modelo', 'Modelo', COLOR_MODELO, 'solid'), ('pred_referencia', 'Referencia', COLOR_REFERENCIA, 'dash')]:
            valores = test[col].where(test['reservas_registradas'].notna())
            fig_test.add_trace(go.Scatter(x=test.index, y=valores, name=nombre, mode='lines', connectgaps=False, line=dict(color=color, dash=dash)))
    return kpis, fig_pre, fig_test, tabla_pre, tabla_html(errores), estado, prevision.empty


def registrar_callbacks(app):
    app.callback(Output('kpis-prediccion', 'children'), Output('grafico-prevision', 'figure'),
                 Output('grafico-test', 'figure'), Output('tabla-prevision', 'children'),
                 Output('tabla-error', 'children'), Output('estado-prediccion', 'children'),
                 Output('descargar-prediccion', 'disabled'), Input('centro-prediccion', 'value'))(actualizar_prediccion)

    @app.callback(Output('csv-prediccion', 'data'), Input('descargar-prediccion', 'n_clicks'),
                  State('centro-prediccion', 'value'), prevent_initial_call=True)
    def descargar_prediccion(n_clicks, centro):
        tabla = predecir(centro)
        if tabla.empty:
            return None
        return dcc.send_data_frame(tabla.to_csv, 'estimaciones_diarias_padel.csv', index=False, encoding='utf-8-sig')
