import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Filters, TeamProfile } from "../types";
import KPICard from "../components/KPICard";
import DataTable from "../components/DataTable";
import PlotBar from "../components/PlotBar";
import Spinner from "../components/Spinner";

export default function Equipo({ filters }: { filters: Filters }) {
  const [selectedTeam, setSelectedTeam] = useState<string>("");

  const { data: equiposData } = useQuery<{ equipos: string[] }>({
    queryKey: ["equipos", filters.categoria, filters.temporada],
    queryFn: () => api.getEquipos(filters) as Promise<{ equipos: string[] }>,
  });

  const team = selectedTeam || equiposData?.equipos[0] || "";

  const { data, isLoading } = useQuery<TeamProfile>({
    queryKey: ["equipo", team, filters],
    queryFn: () => api.getEquipo(team, filters) as Promise<TeamProfile>,
    enabled: !!team,
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <h2 className="text-xl font-bold">Perfil de Equipo</h2>
        <select
          value={team}
          onChange={(e) => setSelectedTeam(e.target.value)}
          className="select-input max-w-xs"
        >
          {equiposData?.equipos.map((e) => (
            <option key={e} value={e}>{e}</option>
          ))}
        </select>
      </div>

      {isLoading && <div className="flex gap-3 items-center text-gray-400"><Spinner />Cargando...</div>}

      {data && !isLoading && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <KPICard icon="🏟️" label="PJ" value={data.summary.pj} />
            <KPICard icon="🏆" label="PTS" value={data.summary.pts} />
            <KPICard icon="⚽" label="GF" value={data.summary.gf} />
            <KPICard icon="🧤" label="GC" value={data.summary.gc} />
            <KPICard icon="📊" label="EGR" value={`${data.summary.egr}%`} />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <KPICard icon="✅" label="Victorias" value={data.summary.pg} />
            <KPICard icon="🤝" label="Empates" value={data.summary.pe} />
            <KPICard icon="❌" label="Derrotas" value={data.summary.pp} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <section className="card flex flex-col gap-3">
              <h3 className="font-semibold text-gray-200">Últimos 5 partidos</h3>
              <DataTable
                columns={["Jornada", "Resultado", "Detalle"]}
                rows={data.last_five as Record<string, unknown>[]}
              />
            </section>

            <section className="card flex flex-col gap-3">
              <h3 className="font-semibold text-gray-200">Indicadores por partido</h3>
              <DataTable
                columns={["Indicador", "Valor"]}
                rows={data.per_match as Record<string, unknown>[]}
              />
            </section>
          </div>

          <section className="card flex flex-col gap-3">
            <h3 className="font-semibold text-gray-200">Balance de goles por bloque</h3>
            <PlotBar
              x={[...new Set(data.momentum.map((r) => r.Bloque))]}
              y={data.momentum
                .filter((r) => r.Tipo === "A favor")
                .map((r) => r.Goles)}
              color="#22c55e"
              yLabel="Goles a favor"
            />
          </section>
        </>
      )}
    </div>
  );
}
