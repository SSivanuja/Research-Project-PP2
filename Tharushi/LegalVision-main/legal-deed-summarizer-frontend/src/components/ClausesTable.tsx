import type { Clause } from "../lib/types";

export default function ClausesTable({ clauses }: { clauses: Clause[] }) {
  return (
    <div className="overflow-x-auto rounded-2xl border">
      <table className="min-w-full text-sm">
        <thead className="bg-neutral-50 text-neutral-700">
          <tr>
            <th className="px-3 py-2 text-left">Clause</th>
            <th className="px-3 py-2 text-left">Perspective</th>
            <th className="px-3 py-2 text-left">Confidence</th>
            <th className="px-3 py-2 text-left">Text</th>
          </tr>
        </thead>
        <tbody>
          {clauses.map((c) => (
            <tr key={c.clause_id} className="border-t">
              <td className="px-3 py-2 font-medium">{c.clause_id}</td>
              <td className="px-3 py-2">{c.predicted_perspective}</td>
              <td className="px-3 py-2">
                {typeof c.confidence === "number"
                  ? c.confidence.toFixed(3)
                  : "-"}
              </td>
              <td className="px-3 py-2">
                <div className="max-w-3xl whitespace-pre-wrap text-neutral-800">
                  {c.clause_text}
                </div>
                {c.top2_labels ? (
                  <div className="mt-1 text-xs text-neutral-500">
                    top2: {c.top2_labels}
                  </div>
                ) : null}
              </td>
            </tr>
          ))}
          {clauses.length === 0 ? (
            <tr>
              <td className="px-3 py-8 text-center text-neutral-500" colSpan={4}>
                No clauses returned.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}