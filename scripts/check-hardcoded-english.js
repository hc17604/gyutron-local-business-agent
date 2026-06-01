import fs from "node:fs";
import path from "node:path";

const root = fs.existsSync(path.resolve("apps/web/src")) ? path.resolve("apps/web/src") : path.resolve("src");
const allowed = [
  "GyuTron",
  "Alibaba",
  "Shopee",
  "Amazon",
  "TikTok",
  "Shopify",
  "OpenAI",
  "DeepSeek",
  "Ollama",
  "LM Studio",
  "API",
  "SKU",
  "ERP",
  "CSV",
  "Excel",
  "SQLite",
  "POST",
  "GT",
];

const suspicious = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full);
      continue;
    }
    if (!/\.(tsx|ts)$/.test(entry.name) || full.includes(`${path.sep}i18n${path.sep}`)) {
      continue;
    }
    const text = fs.readFileSync(full, "utf8");
    const patterns = [
      />\s*([A-Z][A-Za-z0-9 ,/&().:'"-]{3,})\s*</g,
      /(?:title|label|placeholder|description|eyebrow)=["']([A-Z][A-Za-z0-9 ,/&().:'"-]{3,})["']/g,
    ];
    for (const pattern of patterns) {
      for (const match of text.matchAll(pattern)) {
        const value = match[1].trim();
        if (allowed.some((item) => value.includes(item))) {
          continue;
        }
        suspicious.push(`${path.relative(process.cwd(), full)}: ${value}`);
      }
    }
  }
}

walk(root);

if (suspicious.length) {
  console.log("Possible hardcoded English UI strings:");
  for (const item of suspicious.slice(0, 200)) {
    console.log(`- ${item}`);
  }
  process.exitCode = 1;
} else {
  console.log("No obvious hardcoded English UI strings found.");
}
