import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outputDir = __dirname;
const asOfDate = "2026-07-08";

const products = [
  {
    shortName: "六氟",
    productName: "六氟磷酸锂（国产）",
    spec: "LiPF6>=99.95%",
    productId: "202110220001",
    unit: "万元/吨",
  },
  {
    shortName: "磷酸铁锂电解液",
    productName: "电解液",
    spec: "磷酸铁锂用",
    productId: "202006100002",
    unit: "万元/吨",
  },
  {
    shortName: "三元电解液",
    productName: "电解液",
    spec: "三元动力用",
    productId: "202006100001",
    unit: "万元/吨",
  },
  {
    shortName: "LiFSI",
    productName: "双氟磺酰亚胺锂",
    spec: "LiFSI>=99.9%",
    productId: "202408270002",
    unit: "万元/吨",
  },
  {
    shortName: "VC",
    productName: "碳酸亚乙烯酯VC",
    spec: "电池级",
    productId: "202005210014",
    unit: "万元/吨",
  },
];

const detailUrl = (productId) => `https://hq.smm.cn/new-energy/category/${productId}`;
const historyUrl = (productId) =>
  `https://hq.smm.cn/ajax/spot/history/${productId}/2026-01-01/${asOfDate}`;

function parseDate(value) {
  const [y, m, d] = value.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d, 12, 0, 0));
}

function fmtDate(date) {
  return date.toISOString().slice(0, 10);
}

function mondayOf(date) {
  const d = new Date(date);
  const day = d.getUTCDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setUTCDate(d.getUTCDate() + diff);
  return d;
}

function addDays(date, days) {
  const d = new Date(date);
  d.setUTCDate(d.getUTCDate() + days);
  return d;
}

function round2(value) {
  return Math.round(value * 100) / 100;
}

function toWan(value) {
  return round2(Number(value) / 10000);
}

function productIdText(productId) {
  return `${productId}\u200B`;
}

function average(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function colLetter(n) {
  let s = "";
  while (n > 0) {
    const r = (n - 1) % 26;
    s = String.fromCharCode(65 + r) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

async function fetchHistory(product) {
  const url = historyUrl(product.productId);
  const res = await fetch(url, {
    headers: {
      "user-agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
      referer: detailUrl(product.productId),
      accept: "application/json,text/plain,*/*",
    },
  });
  if (!res.ok) {
    throw new Error(`SMM history request failed: ${res.status} ${product.productId}`);
  }
  const json = await res.json();
  if (json.code !== 0 || !Array.isArray(json.data)) {
    throw new Error(`SMM returned unexpected response for ${product.productId}`);
  }
  return json.data.map((row) => {
    const date = parseDate(row.renew_date);
    return {
      date,
      dateText: row.renew_date,
      shortName: product.shortName,
      productName: product.productName,
      spec: product.spec,
      productId: product.productId,
      lowYuan: Number(row.low),
      highYuan: Number(row.highs),
      avgYuan: Number(row.average),
      lowWan: toWan(row.low),
      highWan: toWan(row.highs),
      avgWan: toWan(row.average),
      changeYuan: row.vchange === undefined ? null : Number(row.vchange),
      changeRate: row.vchange_rate === undefined ? null : Number(row.vchange_rate),
      sourceUrl: detailUrl(product.productId),
    };
  });
}

function makeWeekRows(dailyRows) {
  const grouped = new Map();
  for (const row of dailyRows) {
    const start = mondayOf(row.date);
    const end = addDays(start, 6);
    const key = `${fmtDate(start)}|${fmtDate(end)}|${row.shortName}`;
    if (!grouped.has(key)) {
      grouped.set(key, {
        weekStart: start,
        weekEnd: end,
        product: row.shortName,
        productName: row.productName,
        spec: row.spec,
        productId: row.productId,
        sourceUrl: row.sourceUrl,
        rows: [],
      });
    }
    grouped.get(key).rows.push(row);
  }

  const rows = Array.from(grouped.values()).map((group) => {
    group.rows.sort((a, b) => a.date - b.date);
    const last = group.rows[group.rows.length - 1];
    return {
      weekStart: group.weekStart,
      weekEnd: group.weekEnd,
      latestDate: last.date,
      product: group.product,
      productName: group.productName,
      spec: group.spec,
      productId: group.productId,
      unit: "万元/吨",
      weekAvg: round2(average(group.rows.map((r) => r.avgWan))),
      weekEndPrice: last.avgWan,
      weekLow: Math.min(...group.rows.map((r) => r.lowWan)),
      weekHigh: Math.max(...group.rows.map((r) => r.highWan)),
      quoteDays: group.rows.length,
      status: fmtDate(group.weekEnd) > asOfDate ? `截至${asOfDate}的未完周` : "完整自然周",
      sourceUrl: group.sourceUrl,
    };
  });

  rows.sort((a, b) => a.weekStart - b.weekStart || a.product.localeCompare(b.product, "zh"));
  return rows;
}

function makeMatrixRows(weekRows) {
  const weeks = Array.from(
    new Map(weekRows.map((r) => [fmtDate(r.weekStart), r])).values(),
  ).sort((a, b) => a.weekStart - b.weekStart);
  return weeks.map((week) => {
    const row = {
      weekStart: week.weekStart,
      weekEnd: week.weekEnd,
      status: fmtDate(week.weekEnd) > asOfDate ? `截至${asOfDate}的未完周` : "完整自然周",
    };
    for (const product of products) {
      const match = weekRows.find(
        (r) =>
          fmtDate(r.weekStart) === fmtDate(week.weekStart) &&
          r.product === product.shortName,
      );
      row[product.shortName] = match ? match.weekAvg : null;
    }
    return row;
  });
}

function styleHeader(range) {
  range.format.fill = { color: "#D9EAF7" };
  range.format.font = { color: "#17365D", bold: true };
  range.format.wrapText = true;
  range.format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
}

function styleTable(range) {
  range.format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
  range.format.font = { color: "#000000", size: 10 };
}

function setColumnWidths(sheet, widths) {
  for (const [col, widthPx] of Object.entries(widths)) {
    sheet.getRange(`${col}:${col}`).format.columnWidthPx = widthPx;
  }
}

async function main() {
  const dailyRows = (await Promise.all(products.map(fetchHistory))).flat();
  dailyRows.sort((a, b) => a.date - b.date || a.shortName.localeCompare(b.shortName, "zh"));
  const weekRows = makeWeekRows(dailyRows);
  const matrixRows = makeMatrixRows(weekRows);

  const workbook = Workbook.create();
  const summary = workbook.worksheets.add("周频汇总");
  const matrix = workbook.worksheets.add("周均价矩阵");
  const raw = workbook.worksheets.add("日度原始数据");
  const sources = workbook.worksheets.add("来源说明");

  for (const sheet of [summary, matrix, raw, sources]) {
    sheet.showGridLines = false;
  }

  summary.getRange("A1:N1").merge();
  summary.getRange("A1").values = [[`电解液产业链关键品种周频价格跟踪（截至 ${asOfDate}）`]];
  summary.getRange("A1").format.font = { bold: true, size: 15, color: "#17365D" };
  summary.getRange("A2:N2").merge();
  summary.getRange("A2").values = [[
    "口径：SMM 公开历史行情接口返回的最近30个工作日报价；按自然周聚合，周均价为日度均价算术平均，周末价为该周最后一个披露日均价。单位统一为万元/吨；历史接口小数位存在轻微展示噪声，表内按0.01万元/吨四舍五入。",
  ]];
  summary.getRange("A2").format.wrapText = true;
  summary.getRange("A2").format.fill = { color: "#EAF2F8" };

  const summaryHeaders = [
    "周起始",
    "周截止",
    "最新披露日",
    "品种",
    "品名",
    "规格/口径",
    "产品编号",
    "单位",
    "周均价",
    "周末价",
    "周内低价",
    "周内高价",
    "披露天数",
    "周状态",
    "来源URL",
  ];
  summary.getRangeByIndexes(3, 0, 1, summaryHeaders.length).values = [summaryHeaders];
  styleHeader(summary.getRangeByIndexes(3, 0, 1, summaryHeaders.length));
  const summaryData = weekRows.map((r) => [
    r.weekStart,
    r.weekEnd,
    r.latestDate,
    r.product,
    r.productName,
    r.spec,
    productIdText(r.productId),
    r.unit,
    r.weekAvg,
    r.weekEndPrice,
    r.weekLow,
    r.weekHigh,
    r.quoteDays,
    r.status,
    r.sourceUrl,
  ]);
  summary.getRangeByIndexes(4, 0, summaryData.length, summaryHeaders.length).values = summaryData;
  styleTable(summary.getRangeByIndexes(4, 0, summaryData.length, summaryHeaders.length));
  summary.getRangeByIndexes(4, 0, summaryData.length, 3).setNumberFormat("yyyy-mm-dd");
  summary.getRangeByIndexes(4, 6, summaryData.length, 1).setNumberFormat("@");
  summary.getRangeByIndexes(4, 8, summaryData.length, 4).setNumberFormat("0.00");
  summary.getRangeByIndexes(4, 12, summaryData.length, 1).setNumberFormat("#,##0");
  summary.getRange("A4:O4").format.rowHeightPx = 34;
  summary.freezePanes.freezeRows(4);
  summary.getRange("A2").format.rowHeightPx = 42;
  setColumnWidths(summary, {
    A: 92,
    B: 92,
    C: 92,
    D: 105,
    E: 130,
    F: 135,
    G: 115,
    H: 70,
    I: 72,
    J: 72,
    K: 72,
    L: 72,
    M: 72,
    N: 135,
    O: 330,
  });

  matrix.getRange("A1:H1").merge();
  matrix.getRange("A1").values = [[`周均价矩阵（万元/吨，截至 ${asOfDate}）`]];
  matrix.getRange("A1").format.font = { bold: true, size: 15, color: "#17365D" };
  const matrixHeaders = ["周起始", "周截止", "周状态", ...products.map((p) => p.shortName)];
  matrix.getRangeByIndexes(2, 0, 1, matrixHeaders.length).values = [matrixHeaders];
  styleHeader(matrix.getRangeByIndexes(2, 0, 1, matrixHeaders.length));
  const matrixData = matrixRows.map((r) => [
    r.weekStart,
    r.weekEnd,
    r.status,
    ...products.map((p) => r[p.shortName]),
  ]);
  matrix.getRangeByIndexes(3, 0, matrixData.length, matrixHeaders.length).values = matrixData;
  styleTable(matrix.getRangeByIndexes(3, 0, matrixData.length, matrixHeaders.length));
  matrix.getRangeByIndexes(3, 0, matrixData.length, 2).setNumberFormat("yyyy-mm-dd");
  matrix.getRangeByIndexes(3, 3, matrixData.length, products.length).setNumberFormat("0.00");
  matrix.freezePanes.freezeRows(3);
  setColumnWidths(matrix, { A: 92, B: 92, C: 170, D: 82, E: 110, F: 100, G: 82, H: 82 });

  const rawHeaders = [
    "日期",
    "品种",
    "品名",
    "规格/口径",
    "产品编号",
    "低价_万元/吨",
    "高价_万元/吨",
    "均价_万元/吨",
    "低价_元/吨",
    "高价_元/吨",
    "均价_元/吨",
    "日涨跌_元/吨",
    "日涨跌幅",
    "来源URL",
  ];
  raw.getRange("A1:N1").values = [rawHeaders];
  styleHeader(raw.getRange("A1:N1"));
  const rawData = dailyRows.map((r) => [
    r.date,
    r.shortName,
    r.productName,
    r.spec,
    productIdText(r.productId),
    r.lowWan,
    r.highWan,
    r.avgWan,
    r.lowYuan,
    r.highYuan,
    r.avgYuan,
    r.changeYuan,
    r.changeRate,
    r.sourceUrl,
  ]);
  raw.getRangeByIndexes(1, 0, rawData.length, rawHeaders.length).values = rawData;
  styleTable(raw.getRangeByIndexes(1, 0, rawData.length, rawHeaders.length));
  raw.getRangeByIndexes(1, 0, rawData.length, 1).setNumberFormat("yyyy-mm-dd");
  raw.getRangeByIndexes(1, 4, rawData.length, 1).setNumberFormat("@");
  raw.getRangeByIndexes(1, 5, rawData.length, 3).setNumberFormat("0.00");
  raw.getRangeByIndexes(1, 8, rawData.length, 4).setNumberFormat("#,##0");
  raw.getRangeByIndexes(1, 12, rawData.length, 1).setNumberFormat("0.00%");
  raw.freezePanes.freezeRows(1);
  setColumnWidths(raw, {
    A: 92,
    B: 115,
    C: 130,
    D: 135,
    E: 115,
    F: 92,
    G: 92,
    H: 92,
    I: 95,
    J: 95,
    K: 95,
    L: 95,
    M: 90,
    N: 330,
  });

  const sourceRows = [
    ["项目", "说明"],
    ["截至日期", asOfDate],
    ["主数据来源", "SMM 上海有色网公开价格页与产品详情页"],
    ["价格页", "https://newenergy.smm.cn/price/14042-15014"],
    ["六氟", detailUrl("202110220001")],
    ["磷酸铁锂电解液", detailUrl("202006100002")],
    ["三元电解液", detailUrl("202006100001")],
    ["LiFSI", detailUrl("202408270002")],
    ["VC", detailUrl("202005210014")],
    [
      "历史范围限制",
      "公开历史接口本次仅返回最近30个工作日报价，无法代表完整长周期历史；更长连续周频需要 SMM/百川/隆众等会员数据或内部采购报价。",
    ],
    [
      "周频口径",
      "自然周（周一至周日）。周均价=该周所有披露日的日度均价算术平均；周末价=该周最后一个披露日均价；当前未完周按截至日期标注。",
    ],
  ];
  sources.getRangeByIndexes(0, 0, sourceRows.length, 2).values = sourceRows;
  styleHeader(sources.getRange("A1:B1"));
  styleTable(sources.getRangeByIndexes(1, 0, sourceRows.length - 1, 2));
  setColumnWidths(sources, { A: 150, B: 620 });
  sources.getRange("B:B").format.wrapText = true;

  const errorScan = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 50 },
    summary: "formula error scan",
  });
  console.log(errorScan.ndjson);

  const summaryCheck = await workbook.inspect({
    kind: "table",
    range: "周频汇总!A4:O15",
    include: "values",
    tableMaxRows: 12,
    tableMaxCols: 15,
    maxChars: 5000,
  });
  console.log(summaryCheck.ndjson);

  const previews = [
    ["周频汇总", "A1:O20", "preview_summary.png"],
    ["周均价矩阵", "A1:H12", "preview_matrix.png"],
    ["日度原始数据", "A1:N18", "preview_raw.png"],
    ["来源说明", "A1:B11", "preview_sources.png"],
  ];
  for (const [sheetName, range, filename] of previews) {
    const blob = await workbook.render({ sheetName, range, scale: 1.4, format: "png" });
    const bytes = new Uint8Array(await blob.arrayBuffer());
    await fs.writeFile(path.join(outputDir, filename), bytes);
  }

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(path.join(outputDir, "电解液产业链关键品种周频价格_20260708.xlsx"));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
