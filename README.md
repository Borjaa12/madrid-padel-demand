# Madrid Pádel: análisis y predicción de reservas

**Autor:** Borja Ibáñez Pérez · ICAI  
**Aplicación:** [Abrir Madrid Pádel](https://madrid-padel-demand.onrender.com)  
**Repositorio:** [Borjaa12/madrid-padel-demand](https://github.com/Borjaa12/madrid-padel-demand)

He desarrollado Madrid Pádel para explorar los registros de reservas individuales de pádel en centros deportivos municipales de gestión directa de Madrid. Con esta aplicación busco analizar cuándo se juega, cómo evoluciona el uso registrado y qué diferencias aparecen entre centros y periodos.

La primera versión está desarrollada con Dash y publicada en Render. Actualmente estoy trabajando en la fase predictiva, con una primera estimación diaria por centro y una evaluación temporal frente a una referencia histórica. Las predicciones todavía no están integradas en la aplicación pública.

El proyecto está orientado a gestores deportivos, personal de planificación y personas interesadas en el uso del pádel municipal.

## Aplicación disponible

- Filtros compartidos por centro deportivo y periodo.
- Tarjetas con registros del periodo, centros con registros, última semana completa dentro del intervalo y variación semanal.
- Serie temporal de registros semanales.
- Mapa de calor por día de la semana y hora de inicio.
- Consulta de cobertura y comparación semanal.
- Descarga del resumen semanal filtrado en CSV.
- Diseño adaptable al ancho de pantalla.

La aplicación pública se ejecuta en Render y no requiere iniciar JupyterHub. En el plan gratuito, el servicio puede suspenderse por inactividad y tardar en responder en la primera visita.

## Objetivos

1. Preparar de forma reproducible los registros individuales de pádel a partir de datos públicos.
2. Explorar patrones de calendario, evolución semanal y diferencias entre centros, documentando su cobertura.
3. Desarrollar una primera estimación por centro y día para un horizonte de siete días.
4. Comparar un modelo de aprendizaje automático con una referencia histórica mediante evaluación temporal.
5. Integrar las estimaciones, sus errores y sus limitaciones en una aplicación accesible por URL.

En la propuesta inicial planteé realizar predicciones por centro, día y franja horaria. He decidido empezar por **centro y día** para evaluar una primera versión antes de ampliar el detalle horario. En el análisis descriptivo mantengo la hora de inicio.

## Datos y procedencia

Fuente: [Deportes. Ocupación de unidades deportivas — Ayuntamiento de Madrid](https://datos.madrid.es/dataset/300086-0-deportes-utilizacion-unidades). Licencia de origen: **CC BY 4.0**.

He utilizado los datos públicos de uso de unidades deportivas del Ayuntamiento de Madrid. He seleccionado los registros relacionados con pádel y revisado los casos identificados únicamente por la descripción del uso. Para este análisis me he centrado en las reservas individuales, separándolas de otros tipos de ocupación, como escuelas o temporada.

El conjunto utilizado por la aplicación contiene:

| Indicador | Valor |
| --- | ---: |
| Registros de reservas individuales | 417.661 |
| Centros tras normalizar nombres | 45 |
| Primera fecha | 02/01/2025 |
| Última fecha | 31/08/2026 |
| Registros de 2025 | 256.122 |
| Registros de 2026, enero–agosto | 161.539 |

El CSV de la aplicación es `Datos/app/reservas_padel_app.csv` y conserva una fila por registro individual seleccionado, con cuatro columnas: `fecha`, `Centro deportivo`, `hora_inicio_num` y `duracion_minutos`. Los cálculos agregados se obtienen a partir de ese archivo; la web no necesita leer los Excel originales.

Los totales anuales no son directamente comparables: 2025 incluye doce meses y 2026, ocho.

## Preparación y análisis realizados

Hasta ahora he completado las siguientes tareas:

- Lectura y combinación de hojas mensuales de varios años.
- Selección por unidad deportiva o uso relacionado con pádel.
- Revisión documentada de los casos seleccionados únicamente por uso.
- Revisión de duplicados y validación de fechas, horarios y duraciones.
- Normalización de nombres de centros, conservando la trazabilidad en la preparación.
- Unificación de variantes de nombre, incluida `CDM El Quijote` con `El Quijote`.
- Análisis de cobertura por centro, mes y año.
- Cálculo de indicadores y generación de gráficos interactivos.
- Separación de los cálculos reutilizables en `analisis.py` y de la interfaz en `app.py`.
- Despliegue de la primera versión de Dash en Render.

He realizado la revisión de duplicados durante la preparación de los datos originales. No repito esa eliminación sobre el CSV reducido de cuatro columnas, porque registros de pistas distintas pueden parecer iguales al retirar otras columnas.

## Cómo interpretar los indicadores

**Volumen semanal.** Recuento de registros de lunes a domingo. La serie omite las semanas de los extremos que no caben enteras en el intervalo seleccionado. Que una semana esté incluida por completo no garantiza que sus datos estén completos.

**Patrón por día y hora.** Media de inicios por hora entre las fechas con al menos un registro individual en la selección. Las horas sin registros de esas fechas aportan cero; las fechas sin ningún registro no se incorporan como días de demanda cero. Al seleccionar todos los centros, la media reúne sus registros y no representa una media por centro.

**Variación semanal.** Cambio porcentual respecto a la semana anterior. Debe interpretarse junto con los centros representados y la cobertura. Una variación no mide por sí sola un cambio de demanda.

## Primera fase predictiva: notebook 04

He preparado el primer experimento predictivo en `04_modelo_predictivo.ipynb`. La ejecución y revisión de sus resultados es el siguiente paso del proyecto. Añadiré las métricas y el método seleccionado cuando complete esa evaluación.

### Objetivo y tratamiento de ausencias

Para esta primera versión he definido cada observación de entrenamiento como un **centro-día con al menos un registro individual**. La variable que quiero estimar es el número de registros de ese día. Revisaré las combinaciones sin registros, pero no las rellenaré con cero ni las utilizaré como objetivos de evaluación.

Por tanto, las estimaciones son **condicionales a que el centro tenga registros ese día**. No predicen la probabilidad de apertura ni el volumen incondicional de todos los días naturales. Esta selección puede producir valores superiores a la media de todos los días, y disponer de algún registro no garantiza cobertura completa.

### Referencia y modelo

- **Referencia:** media histórica previa del mismo centro y día de la semana; si falta esa combinación, media del centro y, como último respaldo, media global de entrenamiento.
- **Modelo candidato:** `HistGradientBoostingRegressor` de scikit-learn con pérdida Poisson.
- **Variables:** centro, día de la semana, mes y posición cíclica dentro del año.
- **Preparación:** categorías codificadas mediante `OneHotEncoder` dentro de un `Pipeline`, ajustado únicamente con el entrenamiento de cada origen.
- **Versión inicial:** parámetros fijos, sin búsqueda automática, sin retrasos ni meteorología futura.

### Evaluación temporal de siete días

| Bloque | Fechas objetivo | Finalidad |
| --- | --- | --- |
| Histórico inicial | Hasta 03/05/2026 | Primer entrenamiento |
| Validación | 04/05/2026–28/06/2026 | Elegir el método por MAE |
| Prueba final | 29/06/2026–30/08/2026 | Evaluar la elección ya fijada |

He planteado una evaluación que simula una previsión cada lunes: la referencia y el modelo se ajustan únicamente con fechas anteriores y predicen los siete días siguientes. Las semanas ya terminadas pueden entrar en el entrenamiento de previsiones posteriores, también dentro del bloque de prueba. Mantendré fijados el método seleccionado y sus parámetros antes de examinar los resultados del test.

En cada origen se incluyen centros con al menos 28 días observados en el histórico y 14 en los últimos 56 días. Estos umbrales iniciales indican apoyo histórico, no apertura o cobertura completa. El notebook registra las exclusiones y las combinaciones sin objetivo observable.

Compararé los métodos mediante MAE, RMSE y sesgo global, además del error por centro, semana y horizonte. Elegiré el método con menor MAE de validación; en caso de empate, conservaré la referencia. Utilizaré el bloque de prueba para evaluar esa elección, sin cambiarla a partir de sus resultados.

**Disponibilidad de la información:** la evaluación supone que el histórico anterior al origen ya estaba disponible. No reproduce el retraso de publicación mensual de la fuente. Es un experimento retrospectivo, no una prueba de funcionamiento en tiempo real.

Después de la evaluación, el notebook realiza un ajuste final con todo el histórico y genera una demostración para los siete días siguientes a la última fecha disponible. Con el CSV actual, ese intervalo es **01/09/2026–07/09/2026**. Por tanto, se trata de una demostración histórica. El proceso guarda el modelo con `joblib`, sus metadatos, las versiones utilizadas, las predicciones y las conclusiones del experimento.

## Estructura del proyecto

| Archivo o carpeta | Función |
| --- | --- |
| `README.md` | Descripción, estado e instrucciones |
| `Propuesta_Padel_Madrid-2.pdf` | Propuesta inicial entregada |
| `01_preparacion_padel_multianual.ipynb` | Lectura, selección, revisión y validación |
| `02_exploracion_y_kpis_revisado.ipynb` | Normalización, cobertura, indicadores y gráficos |
| `03_iniciar_dash.ipynb` | Arranque de la aplicación en JupyterHub de ICAI |
| `04_modelo_predictivo.ipynb` | Preparación, evaluación y guardado del primer modelo |
| `app.py` | Interfaz Dash y callbacks |
| `analisis.py` | Carga, filtros y cálculos del panel |
| `assets/estilos.css` | Diseño de la aplicación |
| `requirements.txt` | Dependencias de la aplicación desplegada |
| `.python-version` | Familia de Python utilizada en Render |
| `Datos/originales/` | Excel de origen, en el entorno de trabajo |
| `Datos/criterios/` | Decisiones de revisión |
| `Datos/procesados/` | Resultados de la preparación |
| `Datos/analisis/` | Tablas y gráficos exploratorios |
| `Datos/app/reservas_padel_app.csv` | Datos utilizados por la aplicación |
| `Datos/modelo/` | Tablas, métricas, auditorías y predicciones generadas por el notebook 04 |
| `modelos/` | Paquete joblib, metadatos y versiones de entrenamiento |
| `informes/modelo/` | Gráficos HTML y conclusiones del notebook 04 |

Las carpetas de resultados del modelo se generan al ejecutar el notebook 04. Esta estructura recoge tanto el código como los datos y resultados de mi entorno de trabajo; no todos los archivos están publicados en GitHub.

## Ejecutar la aplicación

### En un ordenador con Python

Desde la carpeta principal del proyecto:

```bash
python -m venv .venv
```

La activación del entorno se realiza con `source .venv/bin/activate` en macOS/Linux o con `.venv\Scripts\Activate.ps1` en PowerShell. A continuación se instalan las dependencias y se inicia la aplicación:

```bash
python -m pip install -r requirements.txt
python app.py
```

La aplicación queda disponible en la dirección que muestra la terminal, normalmente `http://127.0.0.1:8050`. El CSV debe estar en `Datos/app/` y el CSS en `assets/`.

### En JupyterHub de ICAI

He incluido `03_iniciar_dash.ipynb` para iniciar la aplicación desde JupyterHub de ICAI. Se ejecuta desde la misma carpeta que `app.py` y utiliza el proxy del servidor personal, que debe estar instalado y habilitado. Ese acceso depende de la sesión de ICAI; la versión pública está alojada en Render.

### Para ejecutar el notebook 04

El notebook utiliza el mismo CSV que la aplicación. Las dependencias adicionales de modelado pueden instalarse desde una celda de Jupyter:

```python
%pip install "scikit-learn==1.8.0" "joblib>=1.4,<2" "plotly==6.9.0"
```

Las celdas se ejecutan en orden a partir del CSV ya preparado, sin necesidad de iniciar Dash. El notebook registra las versiones utilizadas para poder reproducir el entrenamiento. La incorporación del modelo a la aplicación incluirá la actualización de las dependencias del despliegue.

## Despliegue en Render

- Servicio web conectado a la rama `main` del repositorio.
- Directorio raíz vacío, con `app.py` en la raíz del repositorio.
- Python 3.13 indicado en `.python-version`.
- Instalación: `pip install -r requirements.txt`.
- Arranque:

```bash
gunicorn app:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
```

El objeto `server` está definido como `server = app.server`. Render proporciona el puerto mediante `PORT`. Las rutas del proxy de JupyterHub no se configuran en Render.

## Limitaciones

- Se analizan registros de uso, no todas las solicitudes o intenciones de jugar.
- No se dispone del calendario completo de pistas ofertadas, cierres, precios, solicitudes rechazadas o fecha de creación de las reservas.
- No se calcula un porcentaje de ocupación, disponibilidad ni demanda no satisfecha.
- La ausencia de registros no demuestra cierre ni demanda cero.
- La cantidad de pistas y la cobertura pueden diferir entre centros y periodos.
- La evaluación predictiva es condicional a días observados y su prueba final incluye verano; no puede asumirse el mismo rendimiento durante todo el año.
- La publicación mensual limita la actualidad del histórico y no se modela su retraso en esta primera evaluación.
- Los resultados no se extrapolan a clubes privados.

## Estado y próximos pasos

- [x] Propuesta inicial y repositorio.
- [x] Preparación y revisión de los datos.
- [x] Exploración, cobertura e indicadores.
- [x] Aplicación interactiva en Dash.
- [x] Primera versión pública en Render.
- [x] Preparación del notebook 04 y de su protocolo de evaluación.
- [ ] Ejecutar y revisar el notebook 04; documentar sus métricas y el método seleccionado.
- [ ] Integrar el método seleccionado y sus limitaciones en Dash.
- [ ] Valorar la ampliación a franjas horarias tras evaluar la primera versión diaria.
- [ ] Comprobar la versión final, actualizar la documentación y preparar la exposición de cinco minutos.

Documento los avances mediante commits descriptivos con los cambios, las decisiones y los resultados. Conservo la propuesta inicial como referencia del alcance de partida y actualizo este README conforme avanza el proyecto.

## Tecnologías y referencias

Python, pandas y NumPy para datos; Jupyter para documentar el proceso; Plotly y Dash para visualización e interacción; Gunicorn y Render para despliegue. La fase predictiva utiliza scikit-learn y joblib.

- [Datos abiertos del Ayuntamiento de Madrid](https://datos.madrid.es/dataset/300086-0-deportes-utilizacion-unidades)
- [HistGradientBoostingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html)
- [Buenas prácticas y prevención de fugas de información](https://scikit-learn.org/stable/common_pitfalls.html)
- [Persistencia de modelos](https://scikit-learn.org/stable/model_persistence.html)
- [Despliegue de aplicaciones Flask en Render](https://render.com/docs/deploy-flask)
- [Características del plan gratuito de Render](https://render.com/docs/free)
