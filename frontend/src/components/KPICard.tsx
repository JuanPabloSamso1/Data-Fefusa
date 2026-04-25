interface Props {
  icon: string;
  label: string;
  value: string | number;
  sub?: string;
}

export default function KPICard({ icon, label, value, sub }: Props) {
  return (
    <div className="kpi-card">
      <div className="flex justify-between items-start">
        <span className="text-[10px] uppercase tracking-widest text-secondary">{label}</span>
        <span className="text-base opacity-40">{icon}</span>
      </div>
      <span className="text-2xl font-bold text-white mt-1">{value}</span>
      {sub && <span className="text-xs text-muted mt-0.5">{sub}</span>}
    </div>
  );
}
