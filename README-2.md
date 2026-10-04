# Pádel Madrid: mapa predictivo de reservas

**Autor:** Borja Ibáñez Pérez · ICAI  
**Repositorio:** https://github.com/Borjaa12/madrid-padel-demand

Propuesta de aplicación interactiva para explorar y predecir el número de reservas individuales de pistas de pádel en centros deportivos municipales de gestión directa de Madrid, por centro, día y franja horaria.

La aplicación permitirá explorar patrones históricos, comparar centros y consultar una previsión semanal junto con su error de evaluación. Está orientada a gestores deportivos, personal de planificación y personas interesadas en el uso del pádel municipal.

## Objetivos

1. Preparar un conjunto reproducible de reservas individuales de pádel a partir de datos públicos.
2. Mostrar patrones mediante filtros, mapas de calor, series temporales y comparaciones entre centros.
3. Estimar el número de reservas por centro, fecha y hora para un horizonte inicial de siete días.
4. Comparar el modelo con una referencia histórica mediante validación temporal.
5. Publicar una aplicación accesible por URL y documentar sus resultados y limitaciones.

## Datos

Fuente: [Deportes. Ocupación de unidades deportivas, Ayuntamiento de Madrid](https://datos.madrid.es/dataset/300086-0-deportes-utilizacion-unidades).

La ficha oficial ofrece ficheros desde 2017, actualización mensual y licencia **CC BY 4.0**. Cada registro contiene fecha de utilización, día de la semana, hora inicial y final, unidad deportiva, tipo de ocupación, descripción del uso y centro. La documentación de estructura y la licencia están disponibles en esa misma ficha.

La auditoría inicial comprobará la cobertura, los nombres de pistas y centros, los duplicados y los valores ausentes. Se distinguirán las reservas individuales de escuelas, clubes y temporada. Los ficheros originales se procesarán fuera de la aplicación; la web usará datos agregados para responder con rapidez.

### Límites del análisis

Los registros describen usos, pero no un calendario completo de franjas ofertadas, solicitudes rechazadas, precios ni la fecha de creación de las reservas. Por ello, se estimarán **reservas observadas**, sin interpretar los recuentos como porcentaje exacto de ocupación, disponibilidad o demanda no satisfecha.

La ausencia de registros no se convertirá automáticamente en cero: se revisarán la cobertura, la continuidad y los posibles cierres. Las franjas sin evidencia suficiente se señalarán o excluirán con una regla documentada. Las comparaciones entre centros tendrán en cuenta que pueden disponer de distinto número de pistas. No se extrapolarán resultados a clubes privados.

## Método previsto

1. Descargar los ficheros y documentar su procedencia y periodo.
2. Normalizar nombres, fechas y horas; filtrar pádel e identificar pistas por centro y unidad.
3. Revisar duplicados, duraciones y tipos de ocupación; seleccionar reservas individuales.
4. Agregar recuentos por centro, fecha y hora inicial, documentando el tratamiento de ausencias.
5. Construir variables de calendario y resúmenes históricos con información disponible al emitir la previsión.
6. Entrenar, evaluar y guardar datos procesados y previsiones para la aplicación.

**Referencia:** promedio histórico previo del mismo centro, día de la semana y hora.

**Modelo candidato:** `HistGradientBoostingRegressor` de scikit-learn, con variables de calendario, centro codificado y patrones históricos. Los retrasos se adaptarán al horizonte de siete días para evitar utilizar reservas futuras desconocidas.

**Evaluación:** separación cronológica, validación temporal para seleccionar el modelo y prueba final en el último bloque de semanas disponible, reservado de antemano. Se calculará MAE global y por centro, con análisis de franjas de mayor y menor uso. Si el modelo no mejora la referencia, se documentará y se mantendrá la alternativa más fiable.

## Visualización e interacción previstas

- Filtros compartidos por centro, periodo y franja horaria.
- Mapa de calor por día de la semana y hora, con escala y unidades explícitas.
- Series temporales y comparación entre centros.
- Vista semanal de previsiones y referencia histórica comparable.
- Panel con error de evaluación, cobertura y limitaciones.
- Descarga de resultados filtrados.

## Tecnología y despliegue previstos

Python, pandas, scikit-learn, Plotly y Streamlit. Se prevé desplegar la aplicación en **Streamlit Community Cloud** desde este repositorio, con datos agregados y previsiones precalculadas.

## Plan de trabajo inicial

| Fase | Trabajo | Entregable verificable |
| --- | --- | --- |
| 1. Inicio | Definir alcance y auditar la fuente | Propuesta PDF, README y diagnóstico de cobertura y calidad |
| 2. Datos | Preparar y explorar los registros | Pipeline reproducible y primeras visualizaciones |
| 3. Predicción | Crear referencia y modelo | Validación temporal y comparación de errores |
| 4. Aplicación | Integrar gráficos y predicciones | Interfaz, pruebas y URL pública |
| 5. Presentación | Explicar resultados y límites | Demo de cinco minutos y preparación de preguntas |

Se registrarán avances semanales durante el semestre mediante commits descriptivos y notas con decisiones, resultados y próximos pasos.

## Estructura prevista

La siguiente estructura es un plan de desarrollo; los módulos se incorporarán conforme se implementen.

```text
madrid-padel-demand/
├── README.md
├── docs/
│   └── Propuesta_Padel_Madrid.pdf
├── app.py
├── src/
│   ├── data.py
│   ├── features.py
│   └── model.py
├── tests/
├── data/
│   └── processed/
└── requirements.txt
```

## Estado del proyecto

**Propuesta inicial · octubre de 2026.** El desarrollo de la aplicación, el pipeline y el modelo está pendiente. Se añadirán las instrucciones de ejecución y la URL pública cuando estén disponibles.
