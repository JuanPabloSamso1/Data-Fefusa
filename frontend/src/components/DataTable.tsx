interface Props {
  columns: string[];
  rows: Record<string, unknown>[];
  maxRows?: number;
  selectedKey?: string;
  selectedValue?: unknown;
  compact?: boolean;
}

export default function DataTable({ columns, rows, maxRows, selectedKey, selectedValue, compact = false }: Props) {
  const displayed = maxRows ? rows.slice(0, maxRows) : rows;

  return (
    <div className={`overflow-auto rounded-lg border border-navy-600 ${compact ? 'text-xs' : 'text-sm'}`}>
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c} className={compact ? 'py-1' : 'py-2'}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayed.map((row, i) => {
            const isSelected = selectedKey && row[selectedKey] === selectedValue;
            return (
              <tr 
                key={i} 
                className={`${isSelected ? 'bg-red-900/20 border-l-2 border-red-500' : ''} ${i % 2 !== 0 ? 'bg-navy-700/30' : ''}`}
              >
                {columns.map((c) => {
                  const val = row[c];
                  const isNumeric = typeof val === 'number';
                  return (
                    <td 
                      key={c} 
                      className={`text-[#f0f4ff] ${isNumeric ? 'text-right' : 'text-left'} ${compact ? 'py-1' : 'py-2'}`}
                    >
                      {val === null || val === undefined ? "—" : String(val)}
                    </td>
                  );
                })}
              </tr>
            );
          })}
          {displayed.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="text-center text-[#4a5568] py-6">
                Sin datos
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
