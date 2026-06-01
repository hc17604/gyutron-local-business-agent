import { useTranslation } from "react-i18next";

import { countryData } from "../../data/mockDashboard";
import { formatCountry } from "../../i18n/formatters";

export function CountryRanking() {
  const { i18n } = useTranslation();

  return (
    <div className="ranking-list">
      {countryData.map((item) => (
        <div className="ranking-row" key={item.country}>
          <span>{formatCountry(item.country, i18n.language)}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.min(item.inquiries * 2.2, 100)}%` }} />
          </div>
          <strong>{item.inquiries}</strong>
        </div>
      ))}
    </div>
  );
}
