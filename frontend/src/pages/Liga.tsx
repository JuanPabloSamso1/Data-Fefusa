import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Filters, LigaData } from "../types";
import KPICard from "../components/KPICard";
import DataTable from "../components/DataTable";
import PlotBar from "../components/PlotBar";
import PlotHBar from "../components/PlotHBar";
import PlotPie from "../components/PlotPie";
import Spinner from "../components/Spinner";

export default function Liga({ filters }: { filters: Filters }) {
  const { data, isLoading, error } = useQuery<LigaData>({
    queryKey: ["liga", filters],
    queryFn: () => api.getLiga(filters) as Promise<LigaData>,
  });

  if (isLoading) return <LoadingState />;
  if (error || !data) return <ErrorState />;

  const {
    summary, standings, egr, streaks, momentum,
    goals_by_team, events_by_type, goals_by_round, top_scorers, goals_by_period,
  } = data;

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold">Liga / Temporada</h2>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <KPICard icon="🏟️" label="Partidos" value={summary.partidos} />
        <KPICard icon="⚽" label="Goles" value={summary.goles} />
        <KPICard icon="📈" label="Goles/partido" value={summary.goles_por_partido} />
        <KPICard icon="🧤" label="Menos goleado" value={summary.equipo_menos_goleado} />
        <KPICard icon="🔥" label="Mejor EGR" value={summary.mejor_eficiencia} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="card flex flex-col gap-3">
          <h3 className="font-semibold text-gray-200">Tabla de posiciones</h3>
          <DataTable
            columns={["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DIF", "PTS"]}
            rows={standings as unknown as Record<string, unknown>[]}
          />
        </section>

        <section className="card flex flex-col gap-3">
          <h3 className="font-semibold text-gray-200">Momentum de goles</h3>
          <PlotBar
            x={momentum.map((r) => r.Bloque)}
            y={momentum.map((r) => r.Goles)}
            color="#4f8ef7"
            yLabel="Goles"
          />
        </section>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="card flex flex-col gap-3">
          <h3 className="font-semibold text-gray-200">⚽ Goles por equipo</h3>
          <PlotHBar
            x={goals_by_team.map((r) => r.Goles)}
            y={goals_by_team.map((r) => r.equipo)}
            colorScale={[[0, "#1f6feb"], [1, "#79c0ff"]]}
            xLabel="Goles"
          />
        </section>

        <section className="card flex flex-col gap-3">
          <h3 className="font-semibold text-gray-200">📌 Eventos por tipo</h3>
          <PlotPie
            labels={events_by_type.map((r) => r.tipo_evento)}
            values={events_by_type.map((r) => r.Cantidad)}
          />
        </section>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="card flex flex-col gap-3">
          <h3 className="font-semibold text-gray-200">📅 Goles por jornada</h3>
          <PlotBar
            x={goals_by_round.map((r) => r.jornada)}
            y={goals_by_round.map((r) => r.Goles)}
            color="#3fb950"
            yLabel="Goles"
          />
        </section>

        <section className="card flex flex-col gap-3">
          <h3 className="font-semibold text-gray-200">⏱️ Goles por periodo</h3>
          <PlotPie
            labels={goals_by_period.map((r) => r.Periodo)}
            values={goals_by_period.map((r) => r.Goles)}
          />
        </section>
      </div>

      <section className="card flex flex-col gap-3">
        <h3 className="font-semibold text-gray-200">🏅 Top goleadores</h3>
        <PlotHBar
          x={top_scorers.map((r) => r.Goles)}
          y={top_scorers.map((r) => r.label)}
          colorScale={[[0, "#1a4731"], [1, "#3fb950"]]}
          xLabel="Goles"
        />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="card flex flex-col gap-3">
          <h3 className="font-semibold text-gray-200">Eficiencia Goleadora Relativa (EGR)</h3>
          <DataTable
            columns={["Equipo", "PJ", "GF", "GC", "GF/PJ", "GC/PJ", "EGR"]}
            rows={egr as unknown as Record<string, unknown>[]}
          />
        </section>

        <section className="card flex flex-col gap-3">
          <h3 className="font-semibold text-gray-200">Rachas actuales</h3>
          <DataTable
            columns={["Equipo", "Racha", "Partidos", "Detalle"]}
            rows={streaks as unknown as Record<string, unknown>[]}
          />
        </section>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center h-64 gap-3 text-gray-400">
      <Spinner size="lg" />
      <span>Cargando liga...</span>
    </div>
  );
}

function ErrorState() {
  return (
    <div className="flex items-center justify-center h-64 text-red-400">
      Error cargando datos. Verificá que el servidor API esté activo.
    </div>
  );
}
