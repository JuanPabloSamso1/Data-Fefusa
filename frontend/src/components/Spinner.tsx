export default function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sz = size === "sm" ? "h-4 w-4" : size === "lg" ? "h-10 w-10" : "h-6 w-6";
  return (
    <div className={`${sz} animate-spin rounded-full border-2 border-surface-600 border-t-brand-500`} />
  );
}
