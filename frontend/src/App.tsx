import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Liga from "./pages/Liga";
import Equipo from "./pages/Equipo";
import Jugador from "./pages/Jugador";
import Partido from "./pages/Partido";
import Disciplina from "./pages/Disciplina";
import Comparativa from "./pages/Comparativa";
import Predicciones from "./pages/Predicciones";
import { useFilters } from "./hooks/useFilters";

const PAGES: Record<string, React.ComponentType<{ filters: ReturnType<typeof useFilters>["filters"] }>> = {
  liga: Liga,
  equipo: Equipo,
  jugador: Jugador,
  partido: Partido,
  disciplina: Disciplina,
  comparativa: Comparativa,
  predicciones: Predicciones,
};

export default function App() {
  const [activeTab, setActiveTab] = useState("liga");
  const { filters, set, reset } = useFilters();

  const Page = PAGES[activeTab] ?? Liga;

  return (
    <div className="flex min-h-screen">
      <Sidebar
        filters={filters}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onFilterChange={set}
        onReset={reset}
      />
      <main className="flex-1 p-6 overflow-auto">
        <Page filters={filters} />
      </main>
    </div>
  );
}
