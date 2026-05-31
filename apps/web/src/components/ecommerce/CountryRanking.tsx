import { countryData } from "../../data/mockDashboard";

export function CountryRanking() {
  return (
    <div className="ranking-list">
      {countryData.map((item) => (
        <div className="ranking-row" key={item.country}>
          <span>{item.country}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.min(item.inquiries * 2.2, 100)}%` }} />
          </div>
          <strong>{item.inquiries}</strong>
        </div>
      ))}
    </div>
  );
}
