import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Filters, PredictionData } from "../types";
import DataTable from "../components/DataTable";
import KPICard from "../components/KPICard";
import Spinner from "../components/Spinner";

export default function Predicciones({ filters }: { filters: Filters }) {
  const [equipoA, setEquipoA] = useState("");
  const [equipoB, setEquipoB] = useState("");

  const { data: equiposData } = useQuery<{ equipos: string[] }>({
    queryKey: ["equipos", filters.categoria, filters.temporada],
    queryFn: () => api.getEquipos(filters) as Promise<{ equipos: string[] }>,
  });

  const equipos = equiposData?.equipos ?? [];
  const eqA = equipoA || equipos[0] || "";
  const eqB = equipoB || equipos[1] || "";

  const { data, isLoading } = useQuery<PredictionData>({
    queryKey: ["predicciones", eqA, eqB, filters],
    queryFn: () => api.getPredicciones(eqA, eqB, filters) as Promise<PredictionData>,
    enabled: !!(eqA && eqB && eqA !== eqB),
  });

  const pred = data?.prediction;

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-bold">Predicciones (Modelo Poisson)</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">Equipo A (local)</label>
          <select value={eqA} onChange={(e) => setEquipoA(e.target.value)} className="select-input">
            {equipos.map((e) => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">Equipo B (visitante)</label>
          <select value={eqB} onChange={(e) => setEquipoB(e.target.value)} className="select-input">
            {equipos.map((e) => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
      </div>

      {isLoading && <div className="flex gap-3 items-center text-gray-400"><Spinner />Simulando...</div>}

      {pred && !isLoading && (
        <>
          <div className="card flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-200">Resultado esperado</h3>
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                pred.quality === "alta" ? "bg-green-900 text-green-300" :
                pred.quality === "media" ? "bg-yellow-900 text-yellow-300" :
                "bg-red-900 text-red-300"
              }`}>
                Confianza {pred.quality}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-brand-500">{(pred.probs.win_a * 100).toFixed(1)}%</p>
                <p className="text-xs text-gray-400">Victoria {eqA}</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-300">{(pred.probs.draw * 100).toFixed(1)}%</p>
                <p className="text-xs text-gray-400">Empate</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-orange-400">{(pred.probs.win_b * 100).toFixed(1)}%</p>
                <p className="text-xs text-gray-400">Victoria {eqB}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <KPICard icon="🎯" label={`xG ${eqA}`} value={pred.xg_a} />
              <KPICard icon="🎯" label={`xG total`} value={pred.xg_total} />
              <KPICard icon="🎯" label={`xG ${eqB}`} value={pred.xg_b} />
            </div>

            <p className="text-xs text-gray-500">{pred.details}</p>
          </div>

          {data.projection.length > 0 && (
            <section className="card flex flex-col gap-3">
              <h3 className="font-semibold text-gray-200">Proyección de tabla (+1 fecha, Monte Carlo)</h3>
              <DataTable
                columns={["Equipo", "Pos actual", "PTS actuales", "PTS esperados (+1 fecha)", "Pos esperada", "Prob. subir", "Prob. bajar", "Cambio probable"]}
                rows={data.projection as Record<string, unknown>[]}
              />
            </section>
          )}
        </>
      )}
    </div>
  );
}
