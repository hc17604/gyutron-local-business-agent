import { leadRows } from "../../data/mockDashboard";
import { StatusBadge } from "../common/StatusBadge";

export function LeadTable() {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Customer</th>
            <th>Country</th>
            <th>Product</th>
            <th>Value</th>
            <th>Owner</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {leadRows.map((row) => (
            <tr key={row.customer}>
              <td>{row.customer}</td>
              <td>{row.country}</td>
              <td>{row.product}</td>
              <td>{row.value}</td>
              <td>{row.owner}</td>
              <td>
                <StatusBadge label={row.status} tone={row.status === "Overdue" ? "risk" : "info"} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
