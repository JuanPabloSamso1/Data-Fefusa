interface Props {
  columns: string[];
  rows: Record<string, unknown>[];
  maxRows?: number;
}

export default function DataTable({ columns, rows, maxRows }: Props) {
  const displayed = maxRows ? rows.slice(0, maxRows) : rows;
  return (
    <div className="overflow-auto rounded-lg border border-surface-600">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayed.map((row, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c} className="text-gray-200">
                  {row[c] === null || row[c] === undefined ? "—" : String(row[c])}
                </td>
              ))}
            </tr>
          ))}
          {displayed.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="text-center text-gray-500 py-6">
                Sin datos
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
