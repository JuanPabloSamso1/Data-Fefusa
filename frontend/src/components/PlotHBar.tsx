import Plot from "react-plotly.js";

interface Props {
  x: number[];
  y: string[];
  color?: string;
  colorScale?: [number, string][];
  xLabel?: string;
}

const LAYOUT_BASE = {
  paper_bgcolor: "#111827",
  plot_bgcolor: "#0b0e1a",
  font: { color: "#8b9ab5", family: "Inter, sans-serif", size: 11 },
};

export default function PlotHBar({ x, y, color = "#00c2a8", colorScale, xLabel }: Props) {
  const marker = colorScale
    ? { color: x, colorscale: colorScale, showscale: false, line: { color: "rgba(0,194,168,0.3)", width: 1 } }
    : { color, line: { color: "rgba(0,194,168,0.3)", width: 1 } };

  const height = Math.max(200, y.length * 38);

  return (
    <Plot
      data={[{
        type: "bar",
        orientation: "h",
        x,
        y,
        marker: marker as never,
        text: x.map(String),
        textposition: "outside",
      }]}
      layout={{
        ...LAYOUT_BASE,
        height,
        margin: { t: 16, r: 56, b: 40, l: 8 },
        xaxis: { title: { text: xLabel }, gridcolor: "#1e2d40", color: "#8b9ab5" },
        yaxis: { gridcolor: "#1e2d40", color: "#8b9ab5", automargin: true },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
    />
  );
}
