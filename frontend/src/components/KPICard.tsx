interface Props {
  icon: string;
  label: string;
  value: string | number;
  sub?: string;
}

export default function KPICard({ icon, label, value, sub }: Props) {
  return (
    <div className="kpi-card">
      <span className="text-xl">{icon}</span>
      <span className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</span>
      <span className="text-2xl font-bold text-white">{value}</span>
      {sub && <span className="text-xs text-gray-500">{sub}</span>}
    </div>
  );
}
