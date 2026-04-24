import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Filters, PlayerCatalogRow, ComparisonData } from "../types";
import DataTable from "../components/DataTable";
import PlotRadar from "../components/PlotRadar";
import Spinner from "../components/Spinner";

export default function Comparativa({ filters }: { filters: Filters }) {
  const [playerA, setPlayerA] = useState("");
  const [playerB, setPlayerB] = useState("");

  const { data: catalogData } = useQuery<{ jugadores: PlayerCatalogRow[] }>({
    queryKey: ["jugadores", filters.categoria, filters.temporada, filters.equipo],
    queryFn: () => api.getJugadores(filters) as Promise<{ jugadores: PlayerCatalogRow[] }>,
  });

  const keyA = playerA || catalogData?.jugadores[0]?.player_key || "";
  const keyB = playerB || catalogData?.jugadores[1]?.player_key || "";

  const { data, isLoading } = useQuery<ComparisonData>({
    queryKey: ["comparativa", keyA, keyB, filters],
    queryFn: () => api.getComparativa(keyA, keyB, filters) as Promise<ComparisonData>,
    enabled: !!(keyA && keyB && keyA !== keyB),
  });

  const jugadores = catalogData?.jugadores ?? [];

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold">Comparativa de Jugadores</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">Jugador A</label>
          <select value={keyA} onChange={(e) => setPlayerA(e.target.value)} className="select-input">
            {jugadores.map((j) => <option key={j.player_key} value={j.player_key}>{j.label}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">Jugador B</label>
          <select value={keyB} onChange={(e) => setPlayerB(e.target.value)} className="select-input">
            {jugadores.map((j) => <option key={j.player_key} value={j.player_key}>{j.label}</option>)}
          </select>
        </div>
      </div>

      {isLoading && <div className="flex gap-3 items-center text-gray-400"><Spinner />Calculando...</div>}

      {data && !isLoading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section className="card flex flex-col gap-3">
            <h3 className="font-semibold text-gray-200">Métricas comparadas</h3>
            <DataTable
              columns={["Metrica", data.label_a, data.label_b]}
              rows={data.table as Record<string, unknown>[]}
            />
          </section>

          <section className="card flex flex-col gap-3">
            <h3 className="font-semibold text-gray-200">Radar</h3>
            <PlotRadar
              categories={data.radar.map((r) => r.Metrica)}
              valueA={data.radar.map((r) => r.A)}
              valueB={data.radar.map((r) => r.B)}
              labelA={data.label_a}
              labelB={data.label_b}
            />
          </section>
        </div>
      )}
    </div>
  );
}
