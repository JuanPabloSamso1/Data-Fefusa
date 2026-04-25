import Plot from "react-plotly.js";

interface Props {
  x: string[];
  y: number[];
  color?: string;
  title?: string;
  xLabel?: string;
  yLabel?: string;
}

const LAYOUT_BASE = {
  paper_bgcolor: "#111827",
  plot_bgcolor: "#0b0e1a",
  font: { color: "#8b9ab5", family: "Inter, sans-serif", size: 11 },
  margin: { t: 32, r: 16, b: 48, l: 48 },
};

export default function PlotBar({ x, y, color = "#00c2a8", title, xLabel, yLabel }: Props) {
  return (
    <Plot
      data={[{ type: "bar", x, y, marker: { color, line: { color: "rgba(0,194,168,0.3)", width: 1 } } }]}
      layout={{
        ...LAYOUT_BASE,
        title: title ? { text: title, font: { size: 14, color: "#f0f4ff" } } : undefined,
        xaxis: { title: { text: xLabel }, gridcolor: "#1e2d40", color: "#8b9ab5" },
        yaxis: { title: { text: yLabel }, gridcolor: "#1e2d40", color: "#8b9ab5" },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", minHeight: 260 }}
    />
  );
}
