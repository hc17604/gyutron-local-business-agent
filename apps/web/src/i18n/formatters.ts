import type { TFunction } from "i18next";

export function formatStatus(status: string | undefined, t: TFunction): string {
  if (!status) {
    return "-";
  }
  const key = status.toLowerCase().replace(/\s+/g, "_");
  return t(`status.${key}`, { defaultValue: status });
}

export function formatSeverity(severity: string | undefined, t: TFunction): string {
  return formatStatus(severity, t);
}

export function formatReportType(type: string | undefined, t: TFunction): string {
  if (!type) {
    return "-";
  }
  const key = type.toLowerCase().replace(/[\s-]+/g, "_");
  return t(`reportTypes.${key}`, { defaultValue: type });
}

export function formatAutomationType(type: string | undefined, t: TFunction): string {
  if (!type) {
    return "-";
  }
  const key = type.toLowerCase().replace(/[\s-]+/g, "_");
  return t(`automationTypes.${key}`, { defaultValue: type });
}

export function formatConnectorType(type: string | undefined, t: TFunction): string {
  if (!type) {
    return "-";
  }
  const key = type.toLowerCase().replace(/[\s-]+/g, "_");
  return t(`connectorTypes.${key}`, { defaultValue: type });
}

export function formatDataType(type: string | undefined, t: TFunction): string {
  if (!type) {
    return "-";
  }
  const key = type.toLowerCase().replace(/[\s-]+/g, "_");
  return t(`dataTypes.${key}`, { defaultValue: type });
}

export function formatCountry(country: string | undefined, language: string): string {
  if (!country || !language.toLowerCase().startsWith("zh")) {
    return country ?? "-";
  }
  const countries: Record<string, string> = {
    Brazil: "巴西",
    Indonesia: "印尼",
    Malaysia: "马来西亚",
    US: "美国",
    USA: "美国",
    Germany: "德国",
    Vietnam: "越南",
    Mexico: "墨西哥",
    UAE: "阿联酋",
  };
  return countries[country] ?? country;
}

export function formatToolName(toolId: string, t: TFunction): string {
  return t(`tools.${toolId}`, { defaultValue: toolId });
}
