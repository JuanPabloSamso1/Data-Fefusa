import Plot from "react-plotly.js";

interface Props {
  labels: string[];
  values: number[];
  colors?: Record<string, string>;
}

const DEFAULT_COLORS: Record<string, string> = {
  Gol: "#3fb950",
  Falta: "#ff8800",
  Amarilla: "#d29922",
  Roja: "#ef4444",
  "Azul I": "#3b82f6",
  "Azul D": "#1d4ed8",
  "Penal Gol": "#2ea043",
  "Penal Errado": "#a371f7",
  Lesionado: "#8b949e",
  "Primer Tiempo": "#1f6feb",
  "Segundo Tiempo": "#58a6ff",
  Otros: "#6b7280",
};

export default function PlotPie({ labels, values, colors }: Props) {
  const colorMap = colors ?? DEFAULT_COLORS;
  const markerColors = labels.map((l) => colorMap[l] ?? "#4f8ef7");

  return (
    <Plot
      data={[{
        type: "pie",
        hole: 0.55,
        labels,
        values,
        marker: { colors: markerColors },
        textposition: "inside",
        textinfo: "label+percent",
        textfont: { size: 11 },
      }]}
      layout={{
        paper_bgcolor: "#161b22",
        plot_bgcolor: "#0d1117",
        font: { color: "#c9d1d9", family: "Inter, sans-serif", size: 12 },
        margin: { t: 16, r: 16, b: 16, l: 16 },
        showlegend: false,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", minHeight: 280 }}
    />
  );
}
