# Auditoría completa del dashboard FEFUSA

## 1) Inventario funcional actual

### 1.1 Páginas, tabs, containers y bloques visuales

- **Página principal única (`dashboard/app.py`)** con navegación por radio horizontal:
  - `📌 Resumen`
  - `🛡️ Equipos`
  - `👤 Jugadores`
  - `📊 Partidos / Predicción`.
- **Subtabs dentro de `📊 Partidos / Predicción`:**
  - `🟨 Disciplina`
  - `⏳ Línea de Tiempo de Partido`.
- **Bloques globales**:
  - Header dinámico (categoría/temporada).
  - Fila de KPIs (6 tarjetas).
  - Insight banner por página.
  - Footer con fecha fija de actualización.

### 1.2 KPIs actuales

KPIs renderizados de forma global (independiente de página seleccionada):

1. Total Eventos
2. Goles
3. Faltas
4. T. Amarillas
5. T. Rojas
6. Partidos (o "Partidos con participación" cuando hay jugador filtrado).

### 1.3 Tablas actuales

- `🏆 Tabla de Posiciones`
- `📈 Ranking Elo`
- `🏟️ Resultados de Partidos`
- `🟨 Tabla Disciplinaria por Equipo`.

### 1.4 Gráficos actuales

**Resumen**
- `📈 Rendimiento por Equipo (G/E/P)`
- `📌 Eventos por Tipo`

**Equipos**
- `⚽ Goles por Equipo`
- `🛡️ Goles Recibidos por Equipo`
- `⏱️ Goles por Periodo`
- `🛑 Tiros Castigo (Cometidos vs A Favor)`

**Jugadores**
- `📅 Goles por Jornada`
- `🏅 Ranking de Goleadores`
- `📉 Carrera de Goleadores (Acumulado por Jornada)`
- `⚔️ Faltas Cometidas vs Recibidas`
- `⚖️ Eficiencia Ofensiva vs Disciplina`

**Partidos / Predicción → Disciplina**
- `🎯 Faltas vs Tiros Castigos Cometidos`
- `🟥 Evolución de Tarjetas por Bloques (10 min)`
- `🪓 Top Jugadores más Indisciplinados`

**Partidos / Predicción → Línea de tiempo**
- `⏳ Evolución del Marcador y Eventos (Línea de Tiempo)` (feed HTML/CSS custom)

### 1.5 Filtros actuales

**Sidebar global**:
- Categoría
- Temporada
- Jornada
- Equipo
- Tipo de evento
- Jugador
- Botón "Limpiar filtros" y breadcrumb de contexto activo.

**Filtros locales en tab de línea de tiempo**:
- Categoría (local)
- Temporada (local)
- Equipo 1
- Equipo 2 (rival)
- Multi-select de tipos de eventos

> Observación: existe solapamiento/confusión entre filtros globales y locales en esta vista.

---

## 2) Clasificación por componente (DEJAR / MOVER / ELIMINAR)

## 2.1 Navegación y estructura

| Componente | Decisión | Justificación de valor analítico + UX |
|---|---|---|
| Radio principal de 4 páginas | **MOVER** | El enfoque actual mezcla dominios (disciplina, predicción, timeline) en una misma página "Partidos / Predicción"; conviene separar por objetivo analítico. |
| Subtabs de `Partidos / Predicción` | **MOVER** | La tab de Disciplina no es "predicción" y la de timeline es análisis táctico/operativo. Deben ir a módulos dedicados. |
| Insight banner por página | **DEJAR** | Aporta lectura rápida (resumen ejecutivo) y es útil para usuarios no técnicos. |
| Footer con fecha hardcodeada | **MOVER** | Mantener footer, pero fecha debe venir de metadatos de carga para no generar desconfianza. |

## 2.2 KPIs

| KPI | Decisión | Justificación |
|---|---|---|
| Total Eventos | **DEJAR** | KPI base de volumen; útil en contexto filtrado. |
| Goles | **DEJAR** | Métrica principal de rendimiento ofensivo. |
| Faltas | **MOVER** | Debe vivir en módulo Disciplina o mostrarse como KPI secundario contextual. |
| T. Amarillas | **MOVER** | Ídem faltas; en visión general puede saturar la fila principal. |
| T. Rojas | **MOVER** | Ídem. Mantener en Disciplina/Jugadores. |
| Partidos / Partidos con participación | **DEJAR** | Da tamaño muestral, clave para interpretar ratios. |

**Recomendación:** convertir la fila principal en KPIs más ejecutivos: Partidos, Goles, Goles/Partido, % victorias, Índice disciplina (agregado).

## 2.3 Tablas

| Tabla | Decisión | Justificación |
|---|---|---|
| Tabla de Posiciones | **DEJAR** | Muy alto valor para comparación entre entidades (equipos). |
| Ranking Elo | **MOVER** | Mantener pero en sección de comparación/ranking avanzado. No junto a resumen básico. |
| Resultados de Partidos | **MOVER** | Mejor como drill-down en módulo Equipos/Partidos, no en home. |
| Tabla Disciplinaria | **DEJAR** | Alto valor operativo; debe ir en módulo Disciplina o Equipos > Disciplina. |

## 2.4 Gráficos

| Gráfico | Decisión | Justificación |
|---|---|---|
| Rendimiento por Equipo (G/E/P) | **DEJAR** | Excelente para comparación rápida entre entidades. |
| Eventos por Tipo (pie) | **MOVER** | Útil, pero pie pierde precisión; mejor en overview secundario o cambiar luego a barra. |
| Goles por Equipo | **DEJAR** | Core para rendimiento ofensivo comparativo. |
| Goles Recibidos por Equipo | **DEJAR** | Complementa ataque con defensa (balance analítico). |
| Goles por Periodo (1T/2T) | **MOVER** | Bueno para tendencias temporales; debería estar en "Tendencias" no en bloque general de equipos. |
| Tiros Castigo (Cometidos vs A Favor) | **DEJAR** | Diferencial de disciplina con impacto competitivo. |
| Goles por Jornada | **MOVER** | Métrica temporal más de tendencia que de jugador puro. |
| Ranking de Goleadores | **DEJAR** | Alto valor para scouting y rendimiento individual. |
| Carrera de Goleadores | **DEJAR** | Explica tendencias individuales y momentum. |
| Faltas Cometidas vs Recibidas | **MOVER** | Está hoy en Jugadores, pero es métrica por equipo; debe vivir en Equipos/Disciplina. |
| Eficiencia Ofensiva vs Disciplina | **MOVER** | Comparativa por equipo (no jugador), mover a Equipos/Benchmark. |
| Faltas vs Tiros Castigos | **DEJAR** | Relación causal útil para entrenadores. |
| Evolución de Tarjetas por Bloques | **DEJAR** | Explicación de tendencias disciplinarias intra-partido. |
| Top Jugadores más Indisciplinados | **DEJAR** | Alto valor para disciplina individual. |
| Línea de tiempo de partido | **DEJAR** | Muy útil como explicación narrativa de partido específico. |

## 2.5 Filtros

| Filtro | Decisión | Justificación |
|---|---|---|
| Categoría / Temporada / Jornada (global) | **DEJAR** | Núcleo del contexto analítico. |
| Equipo / Jugador (global) | **DEJAR** | Esenciales para slicing por entidad. |
| Tipo de evento (global) | **MOVER** | Puede distorsionar KPIs generales; mejor como filtro avanzado colapsable o local por módulo. |
| Filtros locales de timeline duplicando categoría/temporada | **ELIMINAR (reemplazar)** | Reemplazar por selector de partido único derivado de filtros globales + búsqueda, evitando doble estado. |

**Reemplazo explícito crítico:**
- Quitar selectores locales categoría/temporada en timeline **solo** después de crear selector único de partido (`Partido`) conectado al contexto global.

---

## 3) Problemas detectados de consistencia funcional y visual

1. **Inconsistencia de dominio por página**
   - En `👤 Jugadores` hay gráficos claramente de equipo (`faltas cometidas vs recibidas`, `eficiencia vs disciplina`).

2. **Solapamiento de filtros (global vs local)**
   - La línea de tiempo usa filtros independientes, rompiendo expectativa de "todo responde a la sidebar".

3. **Ambigüedad semántica de "Predicción"**
   - La página llamada "Partidos / Predicción" no tiene modelo predictivo explícito; la etiqueta crea expectativa no cumplida.

4. **Sobrecarga cognitiva en la home**
   - KPIs + 3 tablas + 2 gráficos puede ser demasiado para lectura ejecutiva rápida.

5. **Fecha fija de datos**
   - Fecha hardcodeada en sidebar/footer puede quedar desactualizada y erosionar confianza.

6. **Inconsistencia de clasificación analítica**
   - Métricas disciplinarias repartidas en páginas dispares, dificultando flujo de análisis.

---

## 4) Propuesta de arquitectura objetivo

## Módulo 1 — **Visión general**
**Objetivo:** resumen rápido.

- KPIs ejecutivos (partidos, goles, goles/partido, % victorias, índice disciplina).
- Mini tabla posiciones (top N) + forma reciente.
- Snapshot de eventos por tipo (versión compacta).
- Insight principal automático.

## Módulo 2 — **Equipos**
**Objetivo:** comparación entre entidades.

- Tabla de posiciones completa.
- Ranking Elo.
- Goles a favor vs en contra.
- Rendimiento G/E/P.
- Scatter eficiencia vs disciplina.
- Sección Disciplina de equipo (faltas, tiros castigo, tarjetas).

## Módulo 3 — **Jugadores**
**Objetivo:** performance individual + tendencia.

- Ranking goleadores.
- Carrera de goleadores.
- Top indisciplinados.
- KPIs por jugador seleccionado (goles, tarjetas, participación).

## Módulo 4 — **Predicciones**
**Objetivo:** predicción útil y accionable (fase posterior).

- **Fase actual (sin nueva lógica):**
  - Renombrar temporalmente a "Partidos" o "Partidos y tendencia" hasta que exista modelo.
  - Mantener timeline de partido como explicación de tendencia/eventos.
- **Fase siguiente (futura):**
  - Probabilidad de resultado por cruce.
  - Proyección de goles esperados.
  - Alertas de riesgo disciplinario.

---

## 5) Refactorización mínima sugerida (sin cambios grandes de UI/lógica)

1. **Separar navegación por dominio real**
   - Renombrar `📊 Partidos / Predicción` a `📊 Partidos` (temporal).
   - Reubicar componentes que hoy están mal clasificados (solo mover llamadas de funciones entre secciones).

2. **Unificar filtros para timeline**
   - Mantener filtros globales y usar un selector local único: `Partido`.
   - Evitar selectores duplicados de categoría/temporada.

3. **Externalizar blueprint de layout**
   - Crear archivo de configuración (dict/list) para mapear módulos y componentes. Mejora mantenibilidad sin cambiar visualmente en grande.

4. **Fecha de actualización dinámica**
   - Derivar "datos actualizados" desde metadatos de CSV (mtime) en `data_loader`.

---

## 6) Archivos a tocar (plan recomendado)

### Alta prioridad
- `dashboard/app.py`
  - Reorganizar páginas/módulos.
  - Mover llamadas de charts/tables a módulos correctos.
  - Simplificar flujo de timeline.

- `dashboard/filters.py`
  - Consolidar estrategia de filtros globales.
  - Reducir filtros redundantes por página.

### Media prioridad
- `dashboard/kpis.py`
  - Reordenar KPIs y separar KPIs ejecutivos vs disciplina.

- `dashboard/charts.py`
  - (sin rediseño fuerte) actualizar títulos/secciones para coherencia de dominio.

- `dashboard/tables.py`
  - Reubicar responsabilidades de tablas por módulo (sin cambiar cálculo base).

### Baja prioridad
- `dashboard/data_loader.py`
  - Exponer `last_updated` para fecha real.

- `dashboard/styles.py`
  - Ajustes menores de consistencia visual entre tabs/radios y densidad de bloques.

---

## 7) Mapeo de reemplazos críticos (antes de eliminar)

- **Filtros locales categoría/temporada en timeline**
  - **Reemplaza por:** selector único `Partido` filtrado por sidebar.
- **Etiqueta "Predicción" sin modelo**
  - **Reemplaza por:** "Partidos" hasta implementar modelos reales.
- **Gráficos de equipo ubicados en Jugadores**
  - **Reemplaza por:** reubicación en módulo Equipos.

---

## 8) Priorización de valor real

1. **Alto impacto inmediato**
   - Reorganizar por dominio (Visión general / Equipos / Jugadores / Partidos).
   - Resolver filtros duplicados.

2. **Alto impacto siguiente**
   - KPI layer más ejecutiva y menos redundante.
   - Flujo de comparación de equipos más lineal.

3. **Fase posterior**
   - Predicción real con output accionable (probabilidades y alertas).

