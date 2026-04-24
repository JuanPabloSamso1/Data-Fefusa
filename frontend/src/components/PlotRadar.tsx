import Plot from "react-plotly.js";

interface Props {
  categories: string[];
  valueA: number[];
  valueB: number[];
  labelA: string;
  labelB: string;
}

export default function PlotRadar({ categories, valueA, valueB, labelA, labelB }: Props) {
  return (
    <Plot
      data={[
        {
          type: "scatterpolar",
          r: [...valueA, valueA[0]],
          theta: [...categories, categories[0]],
          name: labelA,
          fill: "toself",
          line: { color: "#4f8ef7" },
        },
        {
          type: "scatterpolar",
          r: [...valueB, valueB[0]],
          theta: [...categories, categories[0]],
          name: labelB,
          fill: "toself",
          line: { color: "#f97316" },
        },
      ]}
      layout={{
        paper_bgcolor: "#161b22",
        plot_bgcolor: "#0d1117",
        font: { color: "#c9d1d9", family: "Inter, sans-serif", size: 12 },
        polar: {
          bgcolor: "#0d1117",
          radialaxis: { visible: true, range: [0, 1], color: "#8b949e", gridcolor: "#21262d" },
          angularaxis: { color: "#8b949e", gridcolor: "#21262d" },
        },
        legend: { bgcolor: "transparent" },
        margin: { t: 32, r: 32, b: 32, l: 32 },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", minHeight: 300 }}
    />
  );
}
