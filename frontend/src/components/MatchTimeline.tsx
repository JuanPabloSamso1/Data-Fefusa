interface MatchEvent {
  tipo_evento: string;
  minuto: number;
  segundo: number;
  periodo: string | number;
  equipo: string;
  jugador: string | null;
}

interface Props {
  events: MatchEvent[];
  teamLeft: string;
  teamRight: string;
}

const ICONS: Record<string, string> = {
  Gol: "⚽",
  Falta: "🟧",
  Amarilla: "🟨",
  Roja: "🟥",
  "Azul I": "🟦",
  "Azul D": "🔷",
  "Penal Gol": "✅",
  "Penal Errado": "❌",
  Lesionado: "🩹",
};

const COLORS: Record<string, string> = {
  Gol: "#3fb950",
  Falta: "#ff8800",
  Amarilla: "#d29922",
  Roja: "#ff4444",
  "Azul I": "#58a6ff",
  "Azul D": "#1f6feb",
  "Penal Gol": "#2ea043",
  "Penal Errado": "#a371f7",
  Lesionado: "#8b949e",
};

const SHOW = new Set(["Gol", "Falta", "Amarilla", "Roja", "Azul I", "Azul D", "Penal Gol", "Penal Errado"]);

function normPeriod(v: string | number): string {
  const s = String(v).toUpperCase().trim();
  if (["1", "1T", "FIRST_HALF", "FIRSTHALF"].includes(s)) return "1T";
  if (["2", "2T", "SECOND_HALF", "SECONDHALF"].includes(s)) return "2T";
  return s;
}

export default function MatchTimeline({ events, teamLeft, teamRight }: Props) {
  const filtered = [...events]
    .filter((e) => SHOW.has(e.tipo_evento))
    .sort((a, b) => a.minuto - b.minuto || a.segundo - b.segundo);

  if (filtered.length === 0) {
    return <p className="text-gray-500 text-sm py-4">Sin eventos destacados.</p>;
  }

  let sawFirstHalf = false;
  let insertedHalftime = false;
  const rows: React.ReactNode[] = [];

  filtered.forEach((ev, idx) => {
    const period = normPeriod(ev.periodo);
    if (period === "1T") sawFirstHalf = true;
    if (period === "2T" && sawFirstHalf && !insertedHalftime) {
      insertedHalftime = true;
      rows.push(
        <div key="ht" className="flex items-center gap-2 py-3">
          <div className="flex-1 border-t border-surface-600" />
          <span className="text-xs text-gray-400 px-3 py-0.5 border border-surface-600 rounded-full font-semibold uppercase tracking-wider">
            Entretiempo
          </span>
          <div className="flex-1 border-t border-surface-600" />
        </div>
      );
    }

    const icon = ICONS[ev.tipo_evento] ?? "•";
    const color = COLORS[ev.tipo_evento] ?? "#c9d1d9";
    const player = ev.jugador || "Sin jugador";
    const isLeft = ev.equipo === teamLeft;
    const isRight = ev.equipo === teamRight;

    const cell = (
      <div className="flex items-center gap-2 min-w-0">
        <span style={{ color, flexShrink: 0 }}>{icon}</span>
        <div className="flex flex-col min-w-0">
          <span className="text-sm font-semibold text-white truncate">{player}</span>
          <span className="text-xs text-gray-500">{ev.tipo_evento}</span>
        </div>
      </div>
    );

    rows.push(
      <div
        key={idx}
        className="grid items-center gap-2 py-2 border-b border-surface-700 last:border-0"
        style={{ gridTemplateColumns: "1fr 64px 1fr" }}
      >
        <div className="flex justify-end">{isLeft ? cell : null}</div>
        <div className="flex justify-center">
          <span className="text-xs font-bold text-gray-300 bg-surface-700 border border-surface-600 rounded-full px-2 py-0.5 min-w-[44px] text-center">
            {ev.minuto}'
          </span>
        </div>
        <div className="flex justify-start">{isRight ? cell : null}</div>
      </div>
    );
  });

  return (
    <div className="rounded-xl border border-surface-600 overflow-hidden">
      <div
        className="grid bg-surface-700 px-4 py-2 text-xs font-semibold text-gray-300"
        style={{ gridTemplateColumns: "1fr 64px 1fr" }}
      >
        <div className="text-right">{teamLeft}</div>
        <div className="text-center text-gray-500">Min</div>
        <div className="text-left">{teamRight}</div>
      </div>
      <div className="px-4 py-1">{rows}</div>
    </div>
  );
}
