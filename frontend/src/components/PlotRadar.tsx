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
        paper_bgcolor: "#111827",
        plot_bgcolor: "#0b0e1a",
        font: { color: "#8b9ab5", family: "Inter, sans-serif", size: 11 },
        polar: {
          bgcolor: "#0b0e1a",
          radialaxis: { visible: true, range: [0, 1], color: "#8b9ab5", gridcolor: "#1e2d40" },
          angularaxis: { color: "#8b9ab5", gridcolor: "#1e2d40" },
        },
        legend: { bgcolor: "transparent", font: { color: "#8b9ab5" } },
        margin: { t: 32, r: 32, b: 32, l: 32 },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", minHeight: 300 }}
    />
  );
}
