import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { revenueTrend } from "../../data/mockDashboard";

export function RevenueChart() {
  return (
    <div className="chart-box">
      <ResponsiveContainer height={260} width="100%">
        <AreaChart data={revenueTrend}>
          <defs>
            <linearGradient id="revenueFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.28} />
              <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#eef2f7" vertical={false} />
          <XAxis dataKey="day" tickLine={false} />
          <YAxis tickLine={false} width={58} />
          <Tooltip />
          <Area dataKey="revenue" fill="url(#revenueFill)" stroke="#4f46e5" strokeWidth={2} type="monotone" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
