import { productRanking } from "../../data/mockDashboard";
import { StatusBadge } from "../common/StatusBadge";

export function ProductRanking() {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Revenue</th>
            <th>Margin</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {productRanking.map((row) => (
            <tr key={row.product}>
              <td>{row.product}</td>
              <td>{row.revenue}</td>
              <td>{row.margin}</td>
              <td>
                <StatusBadge label={row.status} tone={row.status.includes("risk") || row.status.includes("Low") ? "warning" : "success"} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
