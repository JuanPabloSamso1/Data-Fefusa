export interface Filters {
  categoria: string;
  temporada: string;
  jornada: string;
  equipo: string;
  tipo: string;
  jugador: string;
}

export interface FilterOptions {
  categorias: string[];
  temporadas: string[];
  jornadas: string[];
  equipos: string[];
  tipos: string[];
  jugadores: string[];
  last_update: string;
}

export interface StandingsRow {
  Pos: number;
  Equipo: string;
  PJ: number;
  G: number;
  E: number;
  P: number;
  GF: number;
  GC: number;
  DIF: number;
  PTS: number;
}

export interface EGRRow {
  Equipo: string;
  PJ: number;
  GF: number;
  GC: number;
  "GF/PJ": number;
  "GC/PJ": number;
  EGR: number;
}

export interface StreakRow {
  Equipo: string;
  Racha: string;
  Partidos: number;
  Detalle: string;
}

export interface MomentumRow {
  Bloque: string;
  Goles: number;
}

export interface LigaData {
  standings: StandingsRow[];
  egr: EGRRow[];
  streaks: StreakRow[];
  summary: {
    partidos: number;
    goles: number;
    goles_por_partido: number;
    equipo_menos_goleado: string;
    mejor_eficiencia: string;
  };
  momentum: MomentumRow[];
  goals_by_team: { equipo: string; Goles: number }[];
  events_by_type: { tipo_evento: string; Cantidad: number }[];
  goals_by_round: { jornada: string; Goles: number }[];
  top_scorers: { label: string; equipo: string; Goles: number }[];
  goals_by_period: { Periodo: string; Goles: number }[];
}

export interface TeamProfile {
  summary: {
    pj: number; pg: number; pe: number; pp: number;
    pts: number; gf: number; gc: number; dif: number;
    egr: number; ipd: number;
  };
  last_five: { Jornada: string; Resultado: string; Detalle: string }[];
  per_match: { Indicador: string; Valor: number }[];
  momentum: { Bloque: string; Tipo: string; Goles: number }[];
}

export interface PlayerProfile {
  label: string;
  summary: {
    goles: number; partidos: number; goles_por_partido: number;
    faltas: number; amarillas: number; azul_i: number;
    azul_d: number; rojas: number; ipd: number;
  };
  timeline: { Jornada: string; Partido: number; Goles: number }[];
  momentum: { Bloque: string; Goles: number }[];
}

export interface PlayerCatalogRow {
  player_key: string;
  Jugador: string;
  Equipo: string;
  label: string;
  persona_id: string | null;
}

export interface MatchSummary {
  id: string;
  label: string;
  equipo_local: string;
  equipo_visitante: string;
  jornada: string;
  fecha: string | null;
}

export interface MatchEvent {
  tipo_evento: string;
  minuto: number;
  segundo: number;
  periodo: string;
  equipo: string;
  jugador: string | null;
}

export interface MatchData {
  match: {
    id: string; local: string; visitante: string;
    goles_local: number; goles_visitante: number;
    jornada: string; fecha: string | null;
  };
  events: MatchEvent[];
  period_summary: { Periodo: string; Equipo: string; Goles: number }[];
  momentum: { Bloque: string; Equipo: string; Goles: number }[];
  non_regular_goal_events: number;
}

export interface DisciplineTeamRow {
  Equipo: string; PJ: number; Faltas: number;
  Amarillas: number; "Azul I": number; "Azul D": number;
  Rojas: number; Tarjetas: number; IPD: number; Riesgo: string;
}

export interface DisciplinePlayerRow extends DisciplineTeamRow {
  Jugador: string;
}

export interface ComparisonData {
  label_a: string;
  label_b: string;
  table: { Metrica: string; [key: string]: number | string }[];
  radar: { Metrica: string; A: number; B: number }[];
}

export interface PredictionData {
  prediction: {
    xg_a: number; xg_b: number; xg_total: number;
    probs: { win_a: number; draw: number; win_b: number };
    quality: string; details: string;
    strengths?: { team: string; PJ: number; gf_pg: number; gc_pg: number; atk: number; deff: number }[];
  };
  projection: {
    Equipo: string; "Pos actual": number; "PTS actuales": number;
    "PTS esperados (+1 fecha)": number; "Pos esperada": number;
    "Prob. subir": number; "Prob. bajar": number; "Cambio probable": string;
  }[];
}
