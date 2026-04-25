import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { FilterOptions, Filters } from "../types";
import Spinner from "./Spinner";

const TABS = [
  { id: "liga", label: "🏆 Liga" },
  { id: "equipo", label: "🛡️ Equipo" },
  { id: "jugador", label: "👤 Jugador" },
  { id: "partido", label: "⚽ Partido" },
  { id: "disciplina", label: "🟨 Disciplina" },
  { id: "comparativa", label: "📊 Comparativa" },
  { id: "predicciones", label: "🔮 Predicciones" },
];

interface Props {
  filters: Filters;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onFilterChange: (key: keyof Filters, value: string) => void;
  onReset: () => void;
}

export default function Sidebar({ filters, activeTab, onTabChange, onFilterChange, onReset }: Props) {
  const { data, isLoading } = useQuery<FilterOptions>({
    queryKey: ["filters"],
    queryFn: () => api.getFilters() as Promise<FilterOptions>,
  });

  return (
    <aside className="w-64 shrink-0 bg-navy-900 border-r border-navy-600 flex flex-col h-screen sticky top-0 overflow-y-auto">
      <div className="p-4 border-b border-[#1e2d40]">
        <h1 className="text-xl font-bold text-[#f0f4ff]">⚽ FEFUSA</h1>
        <p className="text-xs text-[#8b9ab5] mt-0.5">Dashboard de Analytics</p>
        <div className="mt-4 h-[1px] bg-[#00c2a8]" />
      </div>

      <nav className="p-3 border-b border-navy-600 flex flex-col gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`tab-btn text-left ${activeTab === tab.id ? "bg-[#00c2a8] text-[#0b0e1a] rounded-none" : "tab-btn-inactive"}`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="p-4 flex flex-col gap-3 flex-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[#8b9ab5] uppercase tracking-wide">Filtros</span>
          <button onClick={onReset} className="text-xs text-[#00c2a8] hover:text-[#1a9e8e]">
            Limpiar
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-4"><Spinner /></div>
        ) : data ? (
          <>
            <FilterSelect
              label="Categoría"
              value={filters.categoria}
              options={["Todas", ...data.categorias]}
              onChange={(v) => onFilterChange("categoria", v)}
            />
            <FilterSelect
              label="Temporada"
              value={filters.temporada}
              options={["Todas", ...data.temporadas]}
              onChange={(v) => onFilterChange("temporada", v)}
            />
            <FilterSelect
              label="Jornada"
              value={filters.jornada}
              options={["Todas", ...data.jornadas]}
              onChange={(v) => onFilterChange("jornada", v)}
            />
            <FilterSelect
              label="Equipo"
              value={filters.equipo}
              options={["Todos", ...data.equipos]}
              onChange={(v) => onFilterChange("equipo", v)}
            />
            <FilterSelect
              label="Tipo evento"
              value={filters.tipo}
              options={["Todos", ...data.tipos]}
              onChange={(v) => onFilterChange("tipo", v)}
            />
            <FilterSelect
              label="Jugador"
              value={filters.jugador}
              options={["Todos", ...data.jugadores]}
              onChange={(v) => onFilterChange("jugador", v)}
            />
          </>
        ) : null}
      </div>

      {data && (
        <div className="p-4 border-t border-navy-600">
          <p className="text-xs text-[#4a5568]">Actualizado: {data.last_update}</p>
        </div>
      )}
    </aside>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-[#8b9ab5] w-20 truncate">{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="select-input py-1 text-xs">
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}
