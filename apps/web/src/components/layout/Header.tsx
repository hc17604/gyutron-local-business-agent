import { Activity, DatabaseZap, HardDrive, RefreshCw, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getHealth } from "../../api/client";
import type { HealthResponse } from "../../types/api";
import type { PageKey } from "../../types";

interface HeaderProps {
  title: string;
  onNavigate: (page: PageKey) => void;
}

export function Header({ title, onNavigate }: HeaderProps) {
  const { t } = useTranslation();
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <header className="top-header">
      <div>
        <p className="eyebrow">{t("header.workspace")}</p>
        <h1>{title}</h1>
      </div>
      <div className="header-actions">
        <span className="header-pill success"><HardDrive size={14} />{t("header.localMode")}</span>
        <span className={health ? "header-pill info" : "header-pill warning"}><Activity size={14} />{health ? t("header.apiReady") : t("header.apiOffline")}</span>
        <span className="last-sync">{t("header.updatedAt", { time: "09:42" })}</span>
        <button className="button secondary" onClick={() => onNavigate("sources")} type="button">
          <Upload size={16} />
          {t("header.uploadData")}
        </button>
        <button className="button primary" onClick={() => onNavigate("reports")} type="button">
          <DatabaseZap size={16} />
          {t("header.generateReport")}
        </button>
        <button aria-label={t("header.refresh")} className="icon-button" type="button">
          <RefreshCw size={16} />
        </button>
      </div>
    </header>
  );
}
