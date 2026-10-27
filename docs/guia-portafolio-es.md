# Guía de revisión del portafolio (español)

Esta guía está dirigida a **reclutadores, equipos de analítica, responsables de operaciones y evaluadores técnicos**. Presenta tres proyectos públicos de Python que muestran prácticas de validación de datos, reproducibilidad y análisis de inventarios. Son **prototipos de código abierto con datos sintéticos**, no despliegues empresariales ni casos de éxito comercial verificados.

[English version](portfolio-review-guide.md) · [Estudio de caso técnico](portfolio-case-study.md) · [Perfil principal](../README.md)

## Qué problema aborda cada proyecto

| Pregunta de negocio | Proyecto | Qué puede comprobar un evaluador |
|---|---|---|
| ¿El archivo recibido tiene calidad suficiente para analizarlo? | [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | Columnas obligatorias, faltantes, tipos inferidos, duplicados y controles de calidad |
| ¿Son fiables las claves e identificadores de una operación? | [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | Completitud, claves compuestas, duplicados y concentración por grupos |
| ¿Cómo se comportaría una política de reposición ante la demanda histórica? | [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | Segmentación ABC-XYZ, pronósticos evaluados, inventario de seguridad y simulaciones de reposición |

Los proyectos son complementarios desde una perspectiva conceptual, pero **cada uno funciona por separado**. No existe aquí una integración empresarial de extremo a extremo.

## Revisión práctica en cinco minutos

Instala la versión adecuada de Python, clona cada repositorio por separado y ejecuta su comando **desde la raíz del repositorio correspondiente**. Los ejemplos incluidos son sintéticos y están versionados en GitHub.

### 1. Examinar la calidad de un CSV

Repositorio: [csv-quality-report](https://github.com/rodrix91/csv-quality-report), Python 3.11 o superior.

```bash
PYTHONPATH=src python -m csv_quality_report examples/tiny.csv --format json
```

Resultado esperado: un informe JSON sobre un CSV pequeño. Revisa sus indicadores de filas, columnas, valores faltantes y tipos inferidos. El código de salida esperado es **0**. Consulta las [pruebas automatizadas](https://github.com/rodrix91/csv-quality-report/tree/main/tests). La mejora [#222](https://github.com/rodrix91/csv-quality-report/pull/222) también permite detectar correctamente separadores en exportaciones CSV antiguas con saltos de línea `CR`, aun cuando una fila larga cruza el límite de lectura; está cubierta por pruebas reales del programa.

### 2. Comprobar una alerta de integridad operativa

Repositorio: [ops-field-brief](https://github.com/rodrix91/ops-field-brief), Python 3.10 o superior.

```bash
PYTHONPATH=src python -m ops_field_brief examples/orders-incomplete-keys.csv \
  --required order_id --max-missing 1 \
  --key order_id,line_id --max-incomplete-keys 1 --json
```

Resultado esperado: **código de salida 1**. Esta salida indica que el ejemplo sintético **incumple deliberadamente** el umbral de claves compuestas incompletas. Es una prueba negativa prevista, no un fallo del software ni una aprobación del conjunto de datos.

### 3. Analizar una política de inventario

Repositorio: [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab), Python 3.11 o superior.

```bash
PYTHONPATH=src python -m inventory_policy_lab examples/demand_synthetic.csv
```

Resultado esperado: un informe de análisis de demanda, pronósticos y simulación de políticas; código de salida **0**. Son **resultados de un modelo**, no órdenes de compra aprobadas ni ahorros empresariales demostrados.

El [PR #96, integrado](https://github.com/rodrix91/inventory-policy-lab/pull/96), también permite leer archivos CSV que comienzan con `sep=;` cuando se indica expresamente `--delimiter semicolon`; no adivina separadores. El [CI validado](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40551924889) aprobó las nueve verificaciones tras su integración. El [PR #97 ya integrado](https://github.com/rodrix91/inventory-policy-lab/pull/97) incorpora un archivo sintético listo para ejecutar, con dos productos y 12 meses: `examples/regional-excel.csv`. Puedes probarlo desde la raíz del repositorio mediante `PYTHONPATH=src python -m inventory_policy_lab examples/regional-excel.csv --delimiter semicolon --format json`. El [PR #98, integrado](https://github.com/rodrix91/inventory-policy-lab/pull/98) corrige además la identificación de la **línea física real** cuando un CSV contiene campos entre comillas con varios saltos de línea. Su [CI verificado](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40564204525) aprobó **950 pruebas**, cobertura del **100 % de líneas y ramas** y **9/9** verificaciones en distintas plataformas; los hitos anteriores se conservan.

## Si utilizas Windows PowerShell

En PowerShell no se emplea el prefijo `PYTHONPATH=src` de Bash. En la raíz **de cada repositorio**, configura temporalmente esta variable:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
```

Luego ejecuta el comando `python -m ...` del proyecto correspondiente, **sin** el prefijo `PYTHONPATH=src`, y consulta su código de salida inmediatamente después:

```powershell
$LASTEXITCODE
Remove-Item Env:PYTHONPATH
```

Las tres herramientas cuentan con verificaciones automatizadas para Windows, pero estos comandos específicos de PowerShell no se han validado manualmente en una sesión interactiva. Puedes consultar también la [guía en inglés con comandos completos de PowerShell](portfolio-review-guide.md#five-minute-review-on-windows-powershell).

## Evidencia técnica verificable

Estas cifras corresponden a **ejecuciones concretas** de GitHub Actions, no a estimaciones de adopción:

| Proyecto | Pruebas verificadas | Cobertura de líneas y ramas | Evidencia |
|---|---:|---:|---|
| csv-quality-report | 1.776 | 100 % | [9/9 verificaciones aprobadas en main para CSV con saltos CR](https://github.com/rodrix91/csv-quality-report/actions/runs/40558419557) |
| ops-field-brief | 273 | 100 % | [11/11 verificaciones aprobadas en main](https://github.com/rodrix91/ops-field-brief/actions/runs/40556567860) |
| inventory-policy-lab | 950 | 100 % | [9/9 verificaciones aprobadas en el PR #98](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40564204525) |

Los repositorios contienen su documentación, código fuente, historial, ejemplos y pruebas. La cobertura del 100 % **no garantiza por sí sola** que el software carezca de defectos.

## Límites y uso responsable

Estas herramientas son demostraciones analíticas independientes de carácter **alfa**. No representan clientes, operaciones productivas, certificaciones ni retornos financieros medidos. Antes de emplearlas con información real, verifica permisos y confidencialidad, documenta el esquema de entrada, revisa los supuestos técnicos y valida las decisiones con las personas responsables del negocio.
