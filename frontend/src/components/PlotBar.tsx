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
  paper_bgcolor: "#161b22",
  plot_bgcolor: "#0d1117",
  font: { color: "#c9d1d9", family: "Inter, sans-serif", size: 12 },
  margin: { t: 32, r: 16, b: 48, l: 48 },
};

export default function PlotBar({ x, y, color = "#4f8ef7", title, xLabel, yLabel }: Props) {
  return (
    <Plot
      data={[{ type: "bar", x, y, marker: { color } }]}
      layout={{
        ...LAYOUT_BASE,
        title: title ? { text: title, font: { size: 14 } } : undefined,
        xaxis: { title: { text: xLabel }, gridcolor: "#21262d", color: "#8b949e" },
        yaxis: { title: { text: yLabel }, gridcolor: "#21262d", color: "#8b949e" },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", minHeight: 260 }}
    />
  );
}
