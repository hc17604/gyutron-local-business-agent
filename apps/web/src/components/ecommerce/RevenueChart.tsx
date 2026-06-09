import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { revenueTrend } from "../../data/mockDashboard";

export function RevenueChart() {
  return (
    <div className="chart-box">
      <ResponsiveContainer height={260} width="100%">
        <AreaChart data={revenueTrend}>
          <defs>
            <linearGradient id="revenueFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="5%" stopColor="#6f2dbd" stopOpacity={0.28} />
              <stop offset="95%" stopColor="#6f2dbd" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="day" tickLine={false} />
          <YAxis tickLine={false} width={58} />
          <Tooltip
            contentStyle={{ background: "#ffffff", border: "1px solid #e6e0ee", borderRadius: 2, boxShadow: "0 18px 46px rgba(31,11,53,0.16)" }}
            itemStyle={{ color: "#302b3a" }}
            labelStyle={{ color: "#6f687a" }}
          />
          <Area dataKey="revenue" fill="url(#revenueFill)" stroke="#6f2dbd" strokeWidth={2} type="monotone" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
