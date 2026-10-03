# Hola, soy Rodrigo

Hi, I'm Rodrigo. This profile is in Spanish and English.

## Qué hago
Construyo herramientas de línea de comandos en Python y trabajo en calidad de datos. / I build Python command-line tools and work on data quality.

## Problemas que resuelvo
- Revisar rápido un archivo CSV antes de usarlo: tipos, valores vacíos, valores distintos y filas duplicadas.
- Dejar el trabajo reproducible: pruebas, análisis estático y una auditoría independiente antes de publicar.

## Proyectos
### [csv-quality-report](https://github.com/rodrix91/csv-quality-report) (prototipo alpha)
Herramienta de línea de comandos en Python, solo biblioteca estándar, que perfila un CSV: tipos inferidos, valores vacíos, valores distintos, más frecuentes y filas duplicadas. Salida en Markdown o JSON. Licencia MIT.

Estado: prototipo alpha. Una auditoría independiente lo aprobó para publicación (commit `314fafce`). En esa revisión, con Python 3.11, 3.12 y 3.13, pasaron 54 pruebas, ruff y mypy no dieron errores, el paquete se construyó e instaló en un entorno limpio, detect-secrets no encontró secretos y pip-audit, aplicado al archivo de dependencias fijadas (lock), no reportó vulnerabilidades.
Aún no tiene CI, medición de cobertura ni pruebas en Windows o macOS.

## Stack que se ve en el código
Python (biblioteca estándar), pytest, ruff, mypy.

## Contacto
- LinkedIn: https://www.linkedin.com/in/rodrigo-p-625862153
