import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Filters, PlayerProfile, PlayerCatalogRow } from "../types";
import KPICard from "../components/KPICard";
import PlotBar from "../components/PlotBar";
import DataTable from "../components/DataTable";
import Spinner from "../components/Spinner";

export default function Jugador({ filters }: { filters: Filters }) {
  const [playerKey, setPlayerKey] = useState<string>("");

  const { data: catalogData } = useQuery<{ jugadores: PlayerCatalogRow[] }>({
    queryKey: ["jugadores", filters.categoria, filters.temporada, filters.equipo],
    queryFn: () => api.getJugadores(filters) as Promise<{ jugadores: PlayerCatalogRow[] }>,
  });

  const key = playerKey || catalogData?.jugadores[0]?.player_key || "";

  const { data, isLoading } = useQuery<PlayerProfile>({
    queryKey: ["jugador", key, filters],
    queryFn: () => api.getJugador(key, filters) as Promise<PlayerProfile>,
    enabled: !!key,
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <h2 className="text-xl font-bold">Perfil de Jugador</h2>
        <select
          value={key}
          onChange={(e) => setPlayerKey(e.target.value)}
          className="select-input max-w-xs"
        >
          {catalogData?.jugadores.map((j) => (
            <option key={j.player_key} value={j.player_key}>{j.label}</option>
          ))}
        </select>
      </div>

      {isLoading && <div className="flex gap-3 items-center text-gray-400"><Spinner />Cargando...</div>}

      {data && !isLoading && (
        <>
          {data.label && <p className="text-gray-400 text-sm">{data.label}</p>}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KPICard icon="🏟️" label="Partidos" value={data.summary.partidos} />
            <KPICard icon="⚽" label="Goles" value={data.summary.goles} />
            <KPICard icon="📈" label="Gol/partido" value={data.summary.goles_por_partido} />
            <KPICard icon="📋" label="IPD" value={data.summary.ipd} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <KPICard icon="⚠️" label="Faltas" value={data.summary.faltas} />
            <KPICard icon="🟨" label="Amarillas" value={data.summary.amarillas} />
            <KPICard icon="🔵" label="Azul I" value={data.summary.azul_i} />
            <KPICard icon="🔵" label="Azul D" value={data.summary.azul_d} />
            <KPICard icon="🟥" label="Rojas" value={data.summary.rojas} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <section className="card flex flex-col gap-3">
              <h3 className="font-semibold text-gray-200">Goles por partido</h3>
              <DataTable
                columns={["Jornada", "Partido", "Goles"]}
                rows={data.timeline as Record<string, unknown>[]}
              />
            </section>

            <section className="card flex flex-col gap-3">
              <h3 className="font-semibold text-gray-200">Momentum goleador</h3>
              <PlotBar
                x={data.momentum.map((r) => r.Bloque)}
                y={data.momentum.map((r) => r.Goles)}
                color="#f97316"
              />
            </section>
          </div>
        </>
      )}
    </div>
  );
}
