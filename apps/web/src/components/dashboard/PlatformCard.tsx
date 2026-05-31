import type { PlatformPerformance } from "../../types";
import { StatusBadge } from "../common/StatusBadge";

interface PlatformCardProps {
  platform: PlatformPerformance;
}

export function PlatformCard({ platform }: PlatformCardProps) {
  return (
    <article className="platform-card">
      <div className="card-row">
        <strong>{platform.platform}</strong>
        <StatusBadge label={platform.trend} tone={platform.tone} />
      </div>
      <div className="platform-grid">
        <span>Revenue</span>
        <strong>{platform.revenue}</strong>
        <span>Orders</span>
        <strong>{platform.orders}</strong>
        <span>Inquiries</span>
        <strong>{platform.inquiries}</strong>
        <span>Conversion</span>
        <strong>{platform.conversion}</strong>
      </div>
    </article>
  );
}
