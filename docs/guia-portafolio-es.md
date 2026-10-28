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

La [corrección #223, integrada](https://github.com/rodrix91/csv-quality-report/pull/223) impide que una primera línea `sep=` con comillas desequilibradas se descarte por error como metadato. Su [ejecución CI del PR](https://github.com/rodrix91/csv-quality-report/actions/runs/40602272910) aprobó **1.782 pruebas**, **100 % de cobertura de líneas y ramas** y **9/9 verificaciones**. El hito anterior de 1.776 pruebas queda documentado.

La [protección #224, integrada](https://github.com/rodrix91/csv-quality-report/pull/224) impide generar un informe de calidad con campos CSV entrecomillados incorrectamente (comillas sin cerrar o texto después de una comilla de cierre). Funciona con entrada estándar, gzip y saltos de línea antiguos, manteniendo intacto un informe JSON previamente verificado si la lectura falla. El [CI exacto](https://github.com/rodrix91/csv-quality-report/actions/runs/40610110107) aprobó **1.793 pruebas**, **100 % de cobertura de líneas y ramas** y **9/9 verificaciones**; se conserva el hito anterior de 1.782 pruebas.

### 2. Comprobar una alerta de integridad operativa

Repositorio: [ops-field-brief](https://github.com/rodrix91/ops-field-brief), Python 3.10 o superior.

```bash
PYTHONPATH=src python -m ops_field_brief examples/orders-incomplete-keys.csv \
  --required order_id --max-missing 1 \
  --key order_id,line_id --max-incomplete-keys 1 --json
```

Resultado esperado: **código de salida 1**. Esta salida indica que el ejemplo sintético **incumple deliberadamente** el umbral de claves compuestas incompletas. Es una prueba negativa prevista, no un fallo del software ni una aprobación del conjunto de datos.

El [PR #107, ya integrado](https://github.com/rodrix91/ops-field-brief/pull/107) mejora la validación `--strict-csv`: cuando una fila está mal estructurada, indica tanto su número de registro como la **línea física real** del archivo, incluso si hay campos entre comillas de varias líneas, archivos gzip o encabezados `sep=` de Excel. Su [validación exacta del PR](https://github.com/rodrix91/ops-field-brief/actions/runs/40596506521) aprobó **278 pruebas**, **100 % de cobertura de líneas y ramas** y **11/11 verificaciones**. Se conservan los hitos anteriores.

La [mejora #108, integrada](https://github.com/rodrix91/ops-field-brief/pull/108) permite además procesar archivos CSV antiguos con separadores de línea `CR` (retorno de carro), incluidos datos de una sola columna, la entrada estándar y encabezados `sep=` de Excel; conserva el comportamiento de los archivos `LF` y `CRLF`. La [matriz CI del último commit del PR](https://github.com/rodrix91/ops-field-brief/actions/runs/40599101356) aprobó **286 pruebas, cobertura del 100 % de líneas y ramas y 11/11 verificaciones**.

La [corrección #109, ya integrada](https://github.com/rodrix91/ops-field-brief/pull/109) añade compatibilidad con archivos CSV antiguos cuyos registros terminan en `CR` cuando se indica un separador explícito por entrada estándar. Preserva los encabezados BOM, los campos multilínea y la ubicación real de los errores; el [CI del commit exacto](https://github.com/rodrix91/ops-field-brief/actions/runs/40606326700) aprobó **291 pruebas, 100 % de cobertura de líneas y ramas y 11/11 verificaciones**. El hito previo de 286 pruebas permanece documentado.

### 3. Analizar una política de inventario

Repositorio: [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab), Python 3.11 o superior.

```bash
PYTHONPATH=src python -m inventory_policy_lab examples/demand_synthetic.csv --format json
```

Resultado esperado: un informe **JSON** de análisis de demanda, pronósticos y simulación de políticas; código de salida **0**. Son **resultados de un modelo**, no órdenes de compra aprobadas ni ahorros empresariales demostrados.

El [PR #96, integrado](https://github.com/rodrix91/inventory-policy-lab/pull/96), también permite leer archivos CSV que comienzan con `sep=;` cuando se indica expresamente `--delimiter semicolon`; no adivina separadores. El [CI validado](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40551924889) aprobó las nueve verificaciones tras su integración. El [PR #97 ya integrado](https://github.com/rodrix91/inventory-policy-lab/pull/97) incorpora un archivo sintético listo para ejecutar, con dos productos y 12 meses: `examples/regional-excel.csv`. Puedes probarlo desde la raíz del repositorio mediante `PYTHONPATH=src python -m inventory_policy_lab examples/regional-excel.csv --delimiter semicolon --format json`. El [PR #98, integrado](https://github.com/rodrix91/inventory-policy-lab/pull/98) corrige además la identificación de la **línea física real** cuando un CSV contiene campos entre comillas con varios saltos de línea. Su [CI verificado](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40564204525) aprobó **950 pruebas**, cobertura del **100 % de líneas y ramas** y **9/9** verificaciones en distintas plataformas; los hitos anteriores se conservan.

La [mejora #99](https://github.com/rodrix91/inventory-policy-lab/pull/99) valida los años de los períodos mensuales e impide que datos como `0000-01` pasen al modelo como fechas reales, sin alterar un informe previamente guardado. Su [CI exacto del PR](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40603064172) completó **958 pruebas**, **100 % de cobertura de líneas y ramas** y **9/9 comprobaciones**. El hito anterior de 950 pruebas sigue documentado.

La [corrección #100](https://github.com/rodrix91/inventory-policy-lab/pull/100) evita interpretar silenciosamente encabezados equivalentes de Unicode, como `sku` y `ſku`, como columnas independientes del ERP. Su [CI exacto](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40607684934) aprobó **966 pruebas**, **100 % de cobertura de líneas y ramas** y **9/9 verificaciones**, conservando el hito anterior de 958 pruebas y los informes preexistentes en caso de datos inválidos.

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

Estas cifras corresponden a **ejecuciones concretas y exitosas en la rama principal (main)**, no a estimaciones de adopción. Los resultados de PR anteriores se conservan arriba como hitos históricos:

| Proyecto | Pruebas verificadas | Cobertura de líneas y ramas | Evidencia actual |
|---|---:|---:|---|
| csv-quality-report | 1.796 | 100 % | [12/12 verificaciones aprobadas en main](https://github.com/rodrix91/csv-quality-report/actions/runs/40617268332) |
| ops-field-brief | 291 | 100 % | [14/14 verificaciones aprobadas en main](https://github.com/rodrix91/ops-field-brief/actions/runs/40617399628) |
| inventory-policy-lab | 966 | 100 % | [12/12 verificaciones aprobadas en main](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40617941997) |

Adicionalmente, el [workflow de demostraciones sintéticas](https://github.com/rodrix91/rodrix91/actions/runs/40620651075) aprobó **6/6 verificaciones** en Linux, Windows y macOS ejecutando los tres ejemplos de forma **independiente** con commits fijados. El ejemplo de integridad operativa debe finalizar con código 1 porque incumple intencionalmente un control de calidad. [Instrucciones para reproducirlos](portfolio-smoke-checks.md).

Los repositorios contienen su documentación, código fuente, historial, ejemplos y pruebas. La cobertura del 100 % **no garantiza por sí sola** que el software carezca de defectos.

## Límites y uso responsable

Estas herramientas son demostraciones analíticas independientes de carácter **alfa**. No representan clientes, operaciones productivas, certificaciones ni retornos financieros medidos. Antes de emplearlas con información real, verifica permisos y confidencialidad, documenta el esquema de entrada, revisa los supuestos técnicos y valida las decisiones con las personas responsables del negocio.
