import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Filters, MatchSummary, MatchData } from "../types";
import DataTable from "../components/DataTable";
import PlotBar from "../components/PlotBar";
import MatchTimeline from "../components/MatchTimeline";
import Spinner from "../components/Spinner";

export default function Partido({ filters }: { filters: Filters }) {
  const [partidoId, setPartidoId] = useState<string>("");

  const { data: listData } = useQuery<{ partidos: MatchSummary[] }>({
    queryKey: ["partidos", filters],
    queryFn: () => api.getPartidos(filters) as Promise<{ partidos: MatchSummary[] }>,
  });

  const id = partidoId || listData?.partidos[0]?.id || "";

  const { data, isLoading } = useQuery<MatchData>({
    queryKey: ["partido", id, filters.categoria, filters.temporada],
    queryFn: () => api.getPartido(id, filters) as Promise<MatchData>,
    enabled: !!id,
  });

  const teams = data
    ? [...new Set(data.momentum.map((r) => r.Equipo))]
    : [];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4 flex-wrap">
        <h2 className="text-xl font-bold">Análisis de Partido</h2>
        <select
          value={id}
          onChange={(e) => setPartidoId(e.target.value)}
          className="select-input max-w-md"
        >
          {listData?.partidos.map((p) => (
            <option key={p.id} value={p.id}>{p.label}</option>
          ))}
        </select>
      </div>

      {isLoading && <div className="flex gap-3 items-center text-gray-400"><Spinner />Cargando...</div>}

      {data && !isLoading && (
        <>
          <div className="card flex items-center justify-center gap-8 py-6">
            <div className="text-center">
              <p className="text-lg font-bold text-white">{data.match.local}</p>
              <p className="text-xs text-gray-400">Local</p>
            </div>
            <div className="text-center">
              <p className="text-5xl font-black text-white">
                {data.match.goles_local} — {data.match.goles_visitante}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {data.match.jornada} {data.match.fecha ? `· ${String(data.match.fecha).slice(0, 10)}` : ""}
              </p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-white">{data.match.visitante}</p>
              <p className="text-xs text-gray-400">Visitante</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <section className="card flex flex-col gap-3">
              <h3 className="font-semibold text-gray-200">Goles por periodo</h3>
              <DataTable
                columns={["Periodo", "Equipo", "Goles"]}
                rows={data.period_summary as Record<string, unknown>[]}
              />
            </section>

            <section className="card flex flex-col gap-3">
              <h3 className="font-semibold text-gray-200">Momentum por equipo</h3>
              {teams.map((team) => (
                <div key={team}>
                  <p className="text-xs text-gray-400 mb-1">{team}</p>
                  <PlotBar
                    x={data.momentum.filter((r) => r.Equipo === team).map((r) => r.Bloque)}
                    y={data.momentum.filter((r) => r.Equipo === team).map((r) => r.Goles)}
                    color={team === data.match.local ? "#4f8ef7" : "#f97316"}
                  />
                </div>
              ))}
            </section>
          </div>

          <section className="card flex flex-col gap-3">
            <h3 className="font-semibold text-gray-200">⏳ Línea de tiempo</h3>
            <MatchTimeline
              events={data.events}
              teamLeft={data.match.local}
              teamRight={data.match.visitante}
            />
          </section>

          <section className="card flex flex-col gap-3">
            <h3 className="font-semibold text-gray-200">
              Todos los eventos ({data.events.length})
            </h3>
            <DataTable
              columns={["minuto", "segundo", "periodo", "tipo_evento", "equipo", "jugador"]}
              rows={data.events as unknown as Record<string, unknown>[]}
              maxRows={50}
            />
          </section>
        </>
      )}
    </div>
  );
}
