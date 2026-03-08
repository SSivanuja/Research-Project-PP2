import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { Clause } from "../lib/types";

export default function AnalyticsPanel({ clauses }: { clauses: Clause[] }) {
  const data = useMemo(() => {
    const map = new Map<string, number>();
    for (const c of clauses) {
      const k = c.predicted_perspective || "unknown";
      map.set(k, (map.get(k) || 0) + 1);
    }
    return Array.from(map.entries()).map(([name, count]) => ({ name, count }));
  }, [clauses]);

  return (
    <div className="space-y-4">
      <div className="text-sm text-neutral-700">
        Clause distribution by predicted perspective
      </div>
      <div className="h-72 rounded-2xl border bg-white p-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="text-xs text-neutral-500">
        This chart is computed from <code>clauses[].predicted_perspective</code>.
      </div>
    </div>
  );
}