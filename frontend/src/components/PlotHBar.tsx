import Plot from "react-plotly.js";

interface Props {
  x: number[];
  y: string[];
  color?: string;
  colorScale?: [number, string][];
  xLabel?: string;
}

const LAYOUT_BASE = {
  paper_bgcolor: "#161b22",
  plot_bgcolor: "#0d1117",
  font: { color: "#c9d1d9", family: "Inter, sans-serif", size: 12 },
};

export default function PlotHBar({ x, y, color = "#4f8ef7", colorScale, xLabel }: Props) {
  const markerColor = colorScale
    ? { color: x, colorscale: colorScale, showscale: false }
    : { color };

  const height = Math.max(200, y.length * 38);

  return (
    <Plot
      data={[{
        type: "bar",
        orientation: "h",
        x,
        y,
        marker: markerColor as never,
        text: x.map(String),
        textposition: "outside",
      }]}
      layout={{
        ...LAYOUT_BASE,
        height,
        margin: { t: 16, r: 56, b: 40, l: 8 },
        xaxis: { title: { text: xLabel }, gridcolor: "#21262d", color: "#8b949e" },
        yaxis: { gridcolor: "#21262d", color: "#8b949e", automargin: true },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
    />
  );
}
