"""Madrid Pádel: ejecutar con python app.py o desde el notebook 03."""
from pathlib import Path
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html
from analisis import cargar_datos, filtrar, resumen_semanal, patron_horario
from panel_prediccion import crear_panel, registrar_callbacks

BASE = Path(__file__).resolve().parent
DATOS = cargar_datos(BASE / 'Datos' / 'app' / 'reservas_padel_app.csv')
MIN_FECHA, MAX_FECHA = DATOS['fecha'].min(), DATOS['fecha'].max()
CENTROS = sorted(DATOS['Centro deportivo'].unique())
AZUL = '#2563eb'
CONFIG_GRAFICOS = {'displaylogo': False, 'responsive': True}
app = Dash(__name__, assets_folder=str(BASE / 'assets'), title='Madrid Pádel | ICAI')
server = app.server


def numero(valor, decimales=0):
    if pd.isna(valor):
        return 'Sin datos'
    texto = f'{valor:,.{decimales}f}'
    return texto.replace(',', '_').replace('.', ',').replace('_', '.')


def tarjeta(titulo, valor, detalle):
    return html.Div([html.P(titulo, className='kpi-label'), html.Div(valor, className='kpi-value'),
                     html.P(detalle, className='kpi-detail')], className='kpi')


def estilo_figura(fig, altura=420):
    fig.update_layout(template='plotly_white', height=altura,
        font={'family': 'Arial, sans-serif', 'color': '#17243b', 'size': 13},
        paper_bgcolor='white', plot_bgcolor='white', margin={'l': 45, 'r': 20, 't': 20, 'b': 62})
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#e8edf4')
    return fig


def figura_vacia(mensaje):
    fig = go.Figure()
    fig.add_annotation(text=mensaje, x=.5, y=.5, xref='paper', yref='paper', showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return estilo_figura(fig)


def panel(titulo, descripcion, identificador):
    return html.Section(
        [
            html.H2(titulo),
            html.P(descripcion, className="panel-note"),
            dcc.Checklist(id='mostrar-valores', options=[{'label': 'Mostrar cifras', 'value': 'mostrar'}],
                          value=['mostrar'], className='heatmap-toggle') if identificador == 'horario' else None,
            dcc.Graph(
                id=identificador,
                config=CONFIG_GRAFICOS,
                responsive=True,
                style={
                    "height": "420px",
                    "width": "100%",
                    "minWidth": 0
                }
            )
        ],
        className="panel horario-panel" if identificador == "horario" else "panel"
    )


app.layout = html.Div([
    html.Header([
        html.Div([html.Span('ICAI', className='eyebrow'),
            html.H1(['Madrid ', html.Span('Pádel')]),
            html.P('Cuándo se juega, cómo cambia el uso y qué cuentan los datos.')]),
        html.Div([html.Span('RESERVAS INDIVIDUALES', className='badge'),
            html.P(f'{MIN_FECHA:%d/%m/%Y} — {MAX_FECHA:%d/%m/%Y}'),
            html.Small('Borja Ibáñez Pérez')], className='hero-meta')
    ], className='hero'),
    html.Main([
        html.Nav([html.A('Análisis histórico', href='#historico'), html.A('Predicción y evaluación', href='#predicciones')], className='section-nav', **{'aria-label': 'Secciones del panel'}),
        html.Section([
            html.Div([html.Label('Centro deportivo', htmlFor='centro'),
                dcc.Dropdown(id='centro', options=[{'label':'Todos los centros', 'value':'__todos__'}]
                    + [{'label':c, 'value':c} for c in CENTROS], value='__todos__', clearable=False)], className='centro-filter'),
            html.Div([html.Label('Periodo de análisis'),
                dcc.DatePickerRange(id='fechas', min_date_allowed=MIN_FECHA.date(),
                    max_date_allowed=MAX_FECHA.date(), start_date=MIN_FECHA.date(), end_date=MAX_FECHA.date(),
                    display_format='DD/MM/YYYY', first_day_of_week=1, minimum_nights=0,
                    start_date_placeholder_text='Inicio', end_date_placeholder_text='Fin')], className='date-filter'),
            html.Button('Descargar resumen semanal ↓', id='descargar', n_clicks=0, className='download'),
            dcc.Download(id='descarga-csv')
        ], className='filters', id='historico'),
        html.P(id='estado', className='status', role='status'),
        dcc.Loading(html.Div([
            html.Div(id='indicadores', className='kpis'),
            html.Div([
                panel('01 / Evolución semanal', 'Registros por semana de lunes a domingo. Los extremos parciales se omiten.', 'semanal'),
                panel('02 / Día y hora', 'Media de inicios por día observado. Amarillo claro: menor volumen. Rojo oscuro: mayor volumen.', 'horario')
            ], className='charts'),
            html.P(id='nota-semanas', className='method-note'),
            html.P(id='nota-horario', className='method-note'),
            html.Details([
                html.Summary('Explorar la cobertura y la comparación semanal'),
                dcc.Graph(
                    id="cobertura",
                    config=CONFIG_GRAFICOS,
                    responsive=True,
                    style={"height": "320px", "width": "100%"}
                ),
                html.P('Últimas 12 semanas del intervalo. Una casilla vacía significa que no se puede calcular el valor.'),
                html.Div(id='tabla-semanas', className='table-scroll')
            ], className='panel details')
        ]), type='circle', color=AZUL),
        html.Details([
            html.Summary('Cómo interpretar este panel'),
            html.P('Una reserva se cuenta una vez, en su hora de inicio. La media horaria utiliza solo fechas con algún registro individual en la selección; las franjas sin registros de esas fechas aportan cero.'),
            html.P('Los días o semanas sin registros no demuestran un cierre ni ausencia de demanda. El número de centros y la cobertura pueden cambiar; una variación semanal no mide por sí sola un cambio de demanda.'),
            html.P('No se dispone del calendario completo de pistas disponibles. Por eso no se estima un porcentaje de ocupación ni demanda no satisfecha.')
        ], className='methodology'),
        crear_panel(CENTROS),
        html.Footer([html.Span('Fuente: Ayuntamiento de Madrid · CC BY 4.0'),
            html.A('Consultar datos de origen ↗', href='https://datos.madrid.es/dataset/300086-0-deportes-utilizacion-unidades',
                   target='_blank', rel='noopener noreferrer')])
    ], className='content')
])


def tabla_html(semanas):
    columnas = [('semana','Semana'), ('reservas_registradas','Registros'),
        ('variacion_pct','Variación %'), ('centros_con_registros','Centros'),
        ('dias_con_registros','Días con registros')]
    filas = []
    for _, fila in semanas.tail(12).iterrows():
        valores = [fila['semana'].strftime('%d/%m/%Y')]
        for clave, _ in columnas[1:]:
            valores.append('—' if pd.isna(fila[clave]) else numero(fila[clave], 2 if clave=='variacion_pct' else 0))
        filas.append(html.Tr([html.Td(v) for v in valores]))
    return html.Table([html.Thead(html.Tr([html.Th(t) for _, t in columnas])), html.Tbody(filas)])


@app.callback(
    Output('indicadores','children'), Output('semanal','figure'), Output('horario','figure'),
    Output('cobertura','figure'), Output('tabla-semanas','children'), Output('estado','children'),
    Output('nota-semanas','children'), Output('nota-horario','children'),
    Input('centro','value'), Input('fechas','start_date'), Input('fechas','end_date'),
    Input('mostrar-valores','value'))
def actualizar(centro, inicio, fin, mostrar_valores=None):
    if not inicio or not fin or pd.Timestamp(inicio) > pd.Timestamp(fin):
        vacia = figura_vacia('Selecciona un intervalo de fechas válido.')
        return [], vacia, vacia, vacia, '', 'Selecciona ambas fechas en orden.', '', ''
    inicio = max(pd.Timestamp(inicio).normalize(), MIN_FECHA)
    fin = min(pd.Timestamp(fin).normalize(), MAX_FECHA)
    seleccion = filtrar(DATOS, centro, inicio, fin)
    nombre = 'Todos los centros' if centro=='__todos__' else centro
    estado = f'{nombre} · {inicio:%d/%m/%Y} — {fin:%d/%m/%Y} · {numero(len(seleccion))} registros encontrados'
    if seleccion.empty:
        vacia = figura_vacia('Sin registros para esta selección.')
        tarjetas = [tarjeta('Registros en el periodo','0','Registros encontrados en el archivo'),
            tarjeta('Centros con registros','0','En la selección'),
            tarjeta('Última semana del intervalo','Sin datos','Sin registros observados'),
            tarjeta('Variación semanal','No calculable','No equivale a cero demanda')]
        return tarjetas, vacia, vacia, vacia, '', estado, 'La ausencia de registros no permite concluir que el centro estuviera cerrado.', ''
    semanas = resumen_semanal(seleccion, inicio, fin)
    ultima_valor, ultima_detalle, cambio, detalle_cambio = 'No disponible', 'No cabe una semana de lunes a domingo.', 'No calculable', 'Se necesitan dos semanas consecutivas con registros.'
    if not semanas.empty:
        ultima = semanas.iloc[-1]
        ultima_valor = numero(ultima['reservas_registradas'])
        ultima_detalle = f"{ultima['semana']:%d/%m/%Y} — {ultima['fin_semana']:%d/%m/%Y}"
        if pd.notna(ultima['variacion_pct']):
            cambio = ('+' if ultima['variacion_pct'] >= 0 else '−') + numero(abs(ultima['variacion_pct']), 2) + ' %'
            detalle_cambio = f"Frente a la semana anterior · centros: {numero(ultima['centros_semana_anterior'])} → {numero(ultima['centros_con_registros'])}"
    tarjetas = [tarjeta('Registros en el periodo',numero(len(seleccion)),'Incluye todos los días seleccionados'),
        tarjeta('Centros con registros',numero(seleccion['Centro deportivo'].nunique()),f"En {numero(seleccion['fecha'].nunique())} fechas observadas"),
        tarjeta('Última semana del intervalo',ultima_valor,ultima_detalle),
        tarjeta('Variación semanal',cambio,detalle_cambio)]
    if semanas.empty:
        fig_sem = figura_vacia('El intervalo no contiene una semana de lunes a domingo.')
        fig_cob = figura_vacia('Amplía el intervalo para ver la cobertura semanal.')
    else:
        fig_sem = px.line(semanas, x='semana', y='reservas_registradas', markers=True,
            hover_data=['centros_con_registros','dias_con_registros'], color_discrete_sequence=[AZUL],
            labels={'semana':'Lunes de la semana','reservas_registradas':'Registros',
                'centros_con_registros':'Centros','dias_con_registros':'Días con registros'})
        fig_sem.update_traces(connectgaps=False, line_width=2.5, marker_size=5)
        estilo_figura(fig_sem).update_layout(hovermode='x unified')
        fig_sem.update_yaxes(rangemode='tozero')
        fig_cob = px.line(semanas, x='semana', y='centros_con_registros', markers=True,
            color_discrete_sequence=['#64748b'], labels={'semana':'Lunes de la semana','centros_con_registros':'Centros con registros'})
        fig_cob.update_traces(connectgaps=False)
        estilo_figura(fig_cob, 240).update_yaxes(range=[0, len(CENTROS)+1])
    media, fechas = patron_horario(seleccion)
    # Mostrar las franjas presentes en el conjunto original (8–22 en esta versión).
    horas = list(range(int(DATOS['hora'].min()), int(DATOS['hora'].max())+1))
    matriz = media[horas]
    muestras = np.repeat(fechas.to_numpy()[:, None], len(horas), axis=1)
    fig_hora = go.Figure(go.Heatmap(z=matriz.to_numpy(), x=[f'{h:02d}:00' for h in horas],
        y=list(matriz.index), customdata=muestras, colorscale='YlOrRd', xgap=2, ygap=2,
        zmin=0, hoverongaps=False, colorbar={'title':{'text':'Media'},'thickness':12,'outlinewidth':0},
        hovertemplate='%{y} · %{x}<br>Media: %{z:.1f} registros<br>Fechas observadas: %{customdata}<extra></extra>'))
    if mostrar_valores and 'mostrar' in mostrar_valores:
        maximo = float(np.nanmax(matriz.to_numpy()))
        for dia in matriz.index:
            for hora in horas:
                valor = matriz.loc[dia, hora]
                if pd.notna(valor):
                    color = '#ffffff' if maximo > 0 and valor / maximo >= .70 else '#17243b'
                    fig_hora.add_annotation(x=f'{hora:02d}:00', y=dia, text=numero(valor, 1),
                                            showarrow=False, font={'size':10, 'color':color})
    estilo_figura(fig_hora).update_yaxes(autorange='reversed', showgrid=False)
    fig_hora.update_xaxes(title='Hora de inicio', tickangle=-45)
    nota_sem = 'Las tarjetas de última semana y variación usan la última semana de lunes a domingo que cabe en el intervalo. Que quepa entera no garantiza que sus datos estén completos.'
    nota_hora = 'Fechas utilizadas por día: ' + ' · '.join(f'{d[:3]}: {int(n)}' for d,n in fechas.items()) + '. Las medias suman los centros seleccionados; no son medias por centro. La escala de color se ajusta a la selección: para comparar gráficos, consulta las cifras.'
    return tarjetas, fig_sem, fig_hora, fig_cob, tabla_html(semanas), estado, nota_sem, nota_hora


@app.callback(Output('descarga-csv','data'), Input('descargar','n_clicks'),
    State('centro','value'), State('fechas','start_date'), State('fechas','end_date'), prevent_initial_call=True)
def descargar(n_clicks, centro, inicio, fin):
    if not inicio or not fin or pd.Timestamp(inicio) > pd.Timestamp(fin):
        return None
    inicio, fin = max(pd.Timestamp(inicio), MIN_FECHA), min(pd.Timestamp(fin), MAX_FECHA)
    tabla = resumen_semanal(filtrar(DATOS, centro, inicio, fin), inicio, fin)
    return dcc.send_data_frame(tabla.to_csv, 'resumen_semanal_padel.csv', index=False, encoding='utf-8-sig')


registrar_callbacks(app)


if __name__ == '__main__':
    app.run(debug=False, host=os.environ.get('HOST', '127.0.0.1'), port=int(os.environ.get('PORT', '8050')))
