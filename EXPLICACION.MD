# Explicación del proyecto Movies ETL & Analytics Dashboard

## 1. Resumen ejecutivo

Este proyecto desarrolla un pipeline ETL completo para consolidar información de películas proveniente de tres fuentes: IMDB, TMDB y OMDb. La idea principal es unificar los datos, limpiarlos, validar su calidad y almacenarlos en una base de datos SQLite para luego visualizarlos en un dashboard interactivo con Streamlit y Plotly.

El sistema está pensado para mostrar una visión analítica útil sobre el catálogo de películas, incluyendo calificaciones, ingresos de fuentes, tendencias por año, géneros, décadas y directores más frecuentes.

## 2. Speech para explicar el proyecto al profesor

"Este proyecto implementa una solución de ingeniería de datos aplicada al dominio de películas. El objetivo fue construir un pipeline ETL que extraiga datos desde múltiples fuentes externas, los transforme en un formato homogéneo y los cargue en una base de datos local para análisis.

La arquitectura del sistema está dividida en cuatro partes principales: extracción, transformación, carga y visualización. En la etapa de extracción, el sistema obtiene datasets desde Kaggle para IMDB y TMDB, y además consulta la API de OMDb para enriquecer el catálogo con información como género, director, actores, duración y calificaciones. En la fase de transformación, se normalizan títulos, se extraen años válidos, se eliminan registros anómalos, se limpian valores nulos y se combinan los datos mediante una clave de coincidencia basada en el título normalizado.

La etapa de carga guarda los resultados consolidados en una base de datos SQLite con una tabla llamada movies. El dashboard, construido con Streamlit, permite filtrar por género, año y categoría de calificación, y muestra gráficos interactivos para explorar tendencias del catálogo. Entre los ajustes más importantes que se implementaron, destaca la mejora del límite de extracción de TMDB, que pasó de un muestreo de 5,000 registros a la carga total disponible, lo que permitió obtener una cobertura mucho mayor del dataset.

Además, se incorporaron validaciones para evitar títulos vacíos, años irreales, ratings fuera de rango y duplicados. Los resultados finales muestran un catálogo consolidado de 999 películas, con una base de datos preparada para consultas analíticas y una interfaz de visualización que facilita la toma de decisiones y el análisis exploratorio de datos."

## 3. Objetivo del proyecto

- Unificar información de películas de varias fuentes.
- Mejorar la calidad de los datos mediante transformaciones y validaciones.
- Construir una base analítica local que permita consultar y visualizar métricas.
- Desarrollar una solución reutilizable y portable mediante Docker.

## 4. Arquitectura general del sistema

1. Extracción
   - IMDB: extracción desde dataset de Kaggle.
   - TMDB: extracción desde dataset de Kaggle con soporte para cargar todos los registros disponibles.
   - OMDb: enriquecimiento por API REST para obtener datos faltantes o complementarios.

2. Transformación
   - Normalización de títulos.
   - Extracción y corrección de años.
   - Limpieza de géneros, directores, actores y runtime.
   - Unión por clave de título normalizado.
   - Cálculo de rating combinado.
   - Validaciones de integridad.

3. Carga
   - Inserción en SQLite en la tabla movies.
   - Persistencia de resultados en data/processed/movies_consolidated.csv.

4. Visualización
   - Dashboard en Streamlit.
   - Gráficos interactivos con Plotly.
   - Filtros por género, año y categoría de calificación.

## 5. Flujo de datos detallado

### Extracción

- El módulo [etl/extract.py](etl/extract.py) descarga o lee los datos brutos de IMDB y TMDB.
- Si no hay archivos locales, el sistema intenta descargar datasets desde Kaggle usando kagglehub.
- OMDb se consulta con títulos normalizados y, cuando corresponde, con el año de estreno para mejorar la precisión.

### Transformación

- El módulo [etl/transform.py](etl/transform.py) realiza:
  - Normalización de títulos con regex.
  - Extracción de años mediante regex y validación de rango.
  - Sustitución de años faltantes con la mediana.
  - Coalescing de columnas entre IMDB y TMDB.
  - Creación de métricas derivadas: combined_rating, rating_tier y decade.

### Validaciones

- [etl/validators.py](etl/validators.py) aplica reglas para:
  - eliminar títulos vacíos,
  - descartar años fuera de rango,
  - corregir ratings fuera de los límites esperados,
  - eliminar duplicados por título y año,
  - descartar registros con valores críticos inexistentes.

### Carga

- [etl/load.py](etl/load.py) crea la tabla movies en SQLite y carga los registros ya validados.
- La salida final se deja también en un CSV procesado para trazabilidad y análisis offline.

## 6. Dashboard y analítica

El dashboard en [dashboard/app.py](dashboard/app.py) permite:

- visualizar el volumen total del catálogo,
- revisar la calificación promedio global,
- analizar la distribución por género,
- observar la evolución por año,
- explorar la distribución por década,
- revisar el top 10 de películas mejor calificadas,
- comparar cobertura por fuente de datos.

## 7. Problemas detectados y soluciones aplicadas

Durante el desarrollo se identificaron varios problemas importantes:

- El extractor de TMDB estaba limitando el número de registros a aproximadamente 5,000.
- Algunas entradas contenían títulos poco útiles o no relacionados con películas.
- Había valores de año irreales o futuros que afectaban el análisis temporal.
- Los géneros podían repetirse o venirse con formatos inconsistentes.

Las correcciones implementadas incluyen:

- fijar TMDB_SAMPLE_SIZE a 0 para permitir extracción completa,
- filtrar registros TMDB usando la lista de títulos del IMDB Top 1000 como referencia de calidad,
- aplicar un límite superior de año razonable (2026),
- normalizar el primer género como criterio principal en los filtros.

## 8. Verificación y evidencia del funcionamiento

Durante la verificación del proyecto se ejecutaron estas comprobaciones:

- `PYTHONPATH=. pytest -q tests/test_transform.py`
  - Resultado: 9 pruebas aprobadas en 0.18s.
- `python run_pipeline.py`
  - Resultado: carga exitosa de 999 películas en la base de datos.
- `docker compose config`
  - Resultado: validación correcta de la configuración de contenedores.

## 9. Cómo ejecutar el proyecto localmente

1. Crear y activar un entorno virtual.
2. Instalar dependencias con `pip install -r requirements.txt`.
3. Configurar variables en `.env` con `OMDB_API_KEY` si se desea enriquecimiento adicional.
4. Ejecutar `python run_pipeline.py`.
5. Iniciar el dashboard con `streamlit run dashboard/app.py`.

## 10. Cómo ejecutar con Docker

1. Asegurarse de tener Docker Desktop o Docker Engine disponible.
2. Crear el archivo `.env` con las variables necesarias.
3. Ejecutar:
   - `docker compose up --build`
4. El servicio ETL cargará los datos y el dashboard estará disponible en `http://localhost:8501`.

## 11. Conclusión

Este proyecto demuestra una solución completa de procesamiento de datos aplicada a un caso real de analítica cinematográfica. Integra extracción de datos desde múltiples fuentes, transformaciones de calidad, control de validación, almacenamiento persistente y visualización interactiva. Además, mostró cómo se pueden corregir problemas de calidad de datos y mejorar el rendimiento del pipeline con decisiones enfocadas en la consistencia y robustez del sistema.
