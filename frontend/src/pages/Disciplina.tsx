import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Filters } from "../types";
import DataTable from "../components/DataTable";
import PlotBar from "../components/PlotBar";
import PlotHBar from "../components/PlotHBar";
import Spinner from "../components/Spinner";

interface DisciplinaData {
  equipos: Record<string, unknown>[];
  jugadores: Record<string, unknown>[];
  timeline: { Bloque: string; tipo_evento: string; Cantidad: number }[];
  top_undisciplined: { label: string; equipo: string; Puntaje: number }[];
}

export default function Disciplina({ filters }: { filters: Filters }) {
  const { data, isLoading, error } = useQuery<DisciplinaData>({
    queryKey: ["disciplina", filters],
    queryFn: () => api.getDisciplina(filters) as Promise<DisciplinaData>,
  });

  if (isLoading) return <div className="flex gap-3 items-center text-gray-400 py-10"><Spinner />Cargando...</div>;
  if (error || !data) return <div className="text-red-400 py-10">Error cargando datos.</div>;

  const tiposEvento = [...new Set(data.timeline.map((r) => r.tipo_evento))];
  const TIMELINE_COLORS: Record<string, string> = {
    Falta: "#6b7280",
    Amarilla: "#eab308",
    "Azul I": "#3b82f6",
    "Azul D": "#1d4ed8",
    Roja: "#ef4444",
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-bold">Disciplina</h2>

      <section className="card flex flex-col gap-3">
        <h3 className="font-semibold text-gray-200">Por equipo</h3>
        <DataTable
          columns={["Equipo", "PJ", "Faltas", "Amarillas", "Azul I", "Azul D", "Rojas", "Tarjetas", "IPD", "Riesgo"]}
          rows={data.equipos}
        />
      </section>

      <section className="card flex flex-col gap-3">
        <h3 className="font-semibold text-gray-200">🪓 Top jugadores más indisciplinados</h3>
        <PlotHBar
          x={data.top_undisciplined.map((r) => r.Puntaje)}
          y={data.top_undisciplined.map((r) => r.label)}
          colorScale={[[0, "#ff8800"], [1, "#ff4444"]]}
          xLabel="Puntaje de infracciones"
        />
      </section>

      <section className="card flex flex-col gap-3">
        <h3 className="font-semibold text-gray-200">Timeline de incidencias</h3>
        {tiposEvento.map((tipo) => (
          <div key={tipo}>
            <p className="text-xs text-gray-400 mb-1">{tipo}</p>
            <PlotBar
              x={data.timeline.filter((r) => r.tipo_evento === tipo).map((r) => r.Bloque)}
              y={data.timeline.filter((r) => r.tipo_evento === tipo).map((r) => r.Cantidad)}
              color={TIMELINE_COLORS[tipo] ?? "#6b7280"}
            />
          </div>
        ))}
      </section>

      <section className="card flex flex-col gap-3">
        <h3 className="font-semibold text-gray-200">Por jugador</h3>
        <DataTable
          columns={["Jugador", "Equipo", "PJ", "Faltas", "Amarillas", "Azul I", "Azul D", "Rojas", "Tarjetas", "IPD", "Riesgo"]}
          rows={data.jugadores}
          maxRows={30}
        />
      </section>
    </div>
  );
}
