import { useState } from "react";
import type { Filters } from "../types";

const DEFAULTS: Filters = {
  categoria: "Todas",
  temporada: "Todas",
  jornada: "Todas",
  equipo: "Todos",
  tipo: "Todos",
  jugador: "Todos",
};

export function useFilters() {
  const [filters, setFilters] = useState<Filters>(DEFAULTS);

  function set(key: keyof Filters, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  function reset() {
    setFilters(DEFAULTS);
  }

  return { filters, set, reset };
}
