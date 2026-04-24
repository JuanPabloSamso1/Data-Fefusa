import type { Filters } from "../types";

const BASE = "/api";

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(BASE + path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v) url.searchParams.set(k, v);
    });
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function filterParams(f: Partial<Filters>): Record<string, string> {
  return {
    categoria: f.categoria ?? "Todas",
    temporada: f.temporada ?? "Todas",
    jornada: f.jornada ?? "Todas",
    equipo: f.equipo ?? "Todos",
    tipo: f.tipo ?? "Todos",
    jugador: f.jugador ?? "Todos",
  };
}

export const api = {
  getFilters: () => get("/filters"),

  getLiga: (f: Partial<Filters>) => get("/liga", filterParams(f)),

  getEquipos: (f: Partial<Filters>) => get("/equipos", filterParams(f)),

  getEquipo: (team: string, f: Partial<Filters>) =>
    get(`/equipo/${encodeURIComponent(team)}`, filterParams(f)),

  getJugadores: (f: Partial<Filters>) => get("/jugadores", filterParams(f)),

  getJugador: (playerKey: string, f: Partial<Filters>) =>
    get(`/jugador/${encodeURIComponent(playerKey)}`, filterParams(f)),

  getPartidos: (f: Partial<Filters>) => get("/partidos", filterParams(f)),

  getPartido: (id: string, f: Partial<Filters>) =>
    get(`/partido/${encodeURIComponent(id)}`, filterParams(f)),

  getDisciplina: (f: Partial<Filters>) => get("/disciplina", filterParams(f)),

  getComparativa: (jugadorA: string, jugadorB: string, f: Partial<Filters>) =>
    get("/comparativa", { ...filterParams(f), jugador_a: jugadorA, jugador_b: jugadorB }),

  getPredicciones: (equipoA: string, equipoB: string, f: Partial<Filters>) =>
    get("/predicciones", { ...filterParams(f), equipo_a: equipoA, equipo_b: equipoB }),
};
