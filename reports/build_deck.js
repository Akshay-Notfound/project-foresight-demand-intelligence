const pptxgen = require("pptxgenjs");

const NAVY = "1A1B3A";
const PURPLE = "4C51BF";
const GREEN = "2CA02C";
const RED = "D62728";
const GRAY = "4A5568";
const LIGHTGRAY = "F4F5F9";
const WHITE = "FFFFFF";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
const W = 13.33, H = 7.5;

function baseSlide(bgColor) {
  const s = pres.addSlide();
  s.background = { color: bgColor || WHITE };
  return s;
}

function footer(s, pageNum) {
  s.addText("Project FORESIGHT — NorthBay Living  |  Confidential", {
    x: 0.5, y: H - 0.4, w: 8, h: 0.3, fontSize: 9, color: "9CA3AF", isTextBox: true,
  });
  s.addText(String(pageNum), {
    x: W - 1, y: H - 0.4, w: 0.5, h: 0.3, fontSize: 9, color: "9CA3AF",
    align: "right", isTextBox: true,
  });
}

// ---------- Slide 1: Title ----------
{
  const s = baseSlide(NAVY);
  s.addText("Project FORESIGHT", {
    x: 0.8, y: 2.3, w: 11.5, h: 1.0, fontSize: 44, bold: true, color: WHITE, isTextBox: true,
  });
  s.addText("AI-Powered Demand & Inventory Intelligence for NorthBay Living", {
    x: 0.8, y: 3.25, w: 11.5, h: 0.6, fontSize: 20, color: "C7C9F0", isTextBox: true,
  });
  s.addText("Executive Readout  ·  Head of Operations & Finance", {
    x: 0.8, y: 5.6, w: 8, h: 0.4, fontSize: 14, color: "9CA3AF", isTextBox: true,
  });
  s.addText("Prepared by the FORESIGHT engagement team  ·  Zidio Development", {
    x: 0.8, y: 6.0, w: 8, h: 0.4, fontSize: 12, color: "7C7FB0", isTextBox: true,
  });
}

// ---------- Slide 2: Bottom line up front (rupee impact) ----------
{
  const s = baseSlide(WHITE);
  s.addText("The bottom line", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 28, bold: true, color: NAVY, isTextBox: true });
  s.addText("Right now, across the SKUs we scored, NorthBay has money exposed in both directions at once.", {
    x: 0.7, y: 1.25, w: 11.9, h: 0.5, fontSize: 14, color: GRAY, isTextBox: true,
  });

  const cardY = 2.1, cardH = 3.1, cardW = 5.6;
  // Card 1: stockout
  s.addShape(pres.ShapeType.roundRect, { x: 0.7, y: cardY, w: cardW, h: cardH, fill: { color: "FDEDEC" }, rectRadius: 0.12, line: { type: "none" } });
  s.addText("REORDER NOW", { x: 1.0, y: cardY + 0.3, w: cardW - 0.6, h: 0.35, fontSize: 13, bold: true, color: RED, isTextBox: true });
  s.addText("₹8.5 lakh", { x: 1.0, y: cardY + 0.7, w: cardW - 0.6, h: 0.9, fontSize: 40, bold: true, color: RED, isTextBox: true, margin: 0 });
  s.addText("in projected sales at risk from 5 SKUs likely to stock out over the next 8 weeks.", {
    x: 1.0, y: cardY + 1.65, w: cardW - 0.6, h: 1.0, fontSize: 13, color: GRAY, isTextBox: true,
  });

  // Card 2: overstock
  s.addShape(pres.ShapeType.roundRect, { x: 6.95, y: cardY, w: cardW, h: cardH, fill: { color: "EFECFB" }, rectRadius: 0.12, line: { type: "none" } });
  s.addText("MARKDOWN / CLEAR", { x: 7.25, y: cardY + 0.3, w: cardW - 0.6, h: 0.35, fontSize: 13, bold: true, color: PURPLE, isTextBox: true });
  s.addText("₹2.6 crore", { x: 7.25, y: cardY + 0.7, w: cardW - 0.6, h: 0.9, fontSize: 40, bold: true, color: PURPLE, isTextBox: true, margin: 0 });
  s.addText("in working capital locked in 5 SKUs holding far more stock than they will sell.", {
    x: 7.25, y: cardY + 1.65, w: cardW - 0.6, h: 1.0, fontSize: 13, color: GRAY, isTextBox: true,
  });

  s.addText("125 of 138 scored SKUs are healthy and need no action this cycle.", {
    x: 0.7, y: 5.55, w: 11.9, h: 0.4, fontSize: 13, italic: true, color: GRAY, isTextBox: true,
  });
  footer(s, 2);
}

// ---------- Slide 3: The problem ----------
{
  const s = baseSlide(WHITE);
  s.addText("The problem we were asked to solve", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY, isTextBox: true });

  const items = [
    { t: "Best-sellers run out.", d: "Lost sales that can never be recovered, and frustrated customers." },
    { t: "Slow movers pile up.", d: "Cash locked in stock that later gets marked down at a loss." },
    { t: "Planning is manual.", d: "~200 SKUs are stocked on gut feel and spreadsheets, with no forecast in place today." },
  ];
  let y = 1.7;
  items.forEach((it) => {
    s.addShape(pres.ShapeType.ellipse, { x: 0.8, y: y + 0.05, w: 0.18, h: 0.18, fill: { color: PURPLE }, line: { type: "none" } });
    s.addText(it.t, { x: 1.2, y: y - 0.15, w: 5.2, h: 0.5, fontSize: 17, bold: true, color: NAVY, isTextBox: true });
    s.addText(it.d, { x: 1.2, y: y + 0.3, w: 5.2, h: 0.6, fontSize: 13, color: GRAY, isTextBox: true });
    y += 1.15;
  });

  s.addShape(pres.ShapeType.roundRect, { x: 6.9, y: 1.6, w: 5.7, h: 3.4, fill: { color: LIGHTGRAY }, rectRadius: 0.12, line: { type: "none" } });
  s.addText("What FORESIGHT delivers", { x: 7.2, y: 1.85, w: 5.1, h: 0.4, fontSize: 15, bold: true, color: NAVY, isTextBox: true });
  const deliv = [
    "An 8-week, SKU-level demand forecast",
    "A stockout / overstock risk flag per SKU",
    "The rupee value at stake, so the team can prioritise",
    "A planning dashboard the ops team can use without a data scientist",
    "A scoring API for any SKU, on demand",
  ];
  s.addText(deliv.map((d, i) => ({ text: d, options: { bullet: { code: "2022" }, breakLine: i < deliv.length - 1, color: GRAY, fontSize: 13 } })), {
    x: 7.2, y: 2.35, w: 5.1, h: 2.4, isTextBox: true, paraSpaceAfter: 10,
  });
  footer(s, 3);
}

// ---------- Slide 4: Data & seasonality ----------
{
  const s = baseSlide(WHITE);
  s.addText("What the data shows", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY, isTextBox: true });
  s.addImage({ path: "chart_seasonality.png", x: 0.7, y: 1.4, w: 5.7, h: 3.33 });
  s.addImage({ path: "chart_category_revenue.png", x: 6.7, y: 1.4, w: 5.9, h: 3.44 });

  const insights = [
    "Demand is ~45% higher in June than in January — a clear, exploitable seasonal pattern, not noise.",
    "Promotion weeks lift average daily units by ~60% (28.5 vs. 17.8 units/day).",
    "Furnishings drives the largest share of revenue, followed by Decor and Small Appliances.",
  ];
  s.addText(insights.map((d, i) => ({ text: d, options: { bullet: { code: "2022" }, breakLine: i < insights.length - 1, color: GRAY, fontSize: 13 } })), {
    x: 0.7, y: 4.95, w: 11.9, h: 1.6, isTextBox: true, paraSpaceAfter: 8,
  });
  footer(s, 4);
}

// ---------- Slide 5: Forecast accuracy ----------
{
  const s = baseSlide(WHITE);
  s.addText("Forecast accuracy — honestly validated", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY, isTextBox: true });
  s.addImage({ path: "chart_backtest.png", x: 0.7, y: 1.35, w: 6.3, h: 3.68 });

  s.addShape(pres.ShapeType.roundRect, { x: 7.35, y: 1.35, w: 5.3, h: 1.55, fill: { color: LIGHTGRAY }, rectRadius: 0.12, line: { type: "none" } });
  s.addText("27.6%", { x: 7.6, y: 1.5, w: 4.8, h: 0.75, fontSize: 34, bold: true, color: PURPLE, isTextBox: true, margin: 0 });
  s.addText("lower forecast error than a naive same-week-last-year guess, averaged across 6 backtest folds — and the model wins on every single fold.", {
    x: 7.6, y: 2.2, w: 4.8, h: 0.65, fontSize: 12, color: GRAY, isTextBox: true,
  });

  const notes = [
    "Tested with rolling-origin backtesting: trained only on the past, evaluated on the next week, repeated 6 times.",
    "No future information ever enters a feature — the honest way to validate a forecast.",
    "One data issue was caught and fixed: the extract ends mid-week, which was inflating error on the final period. Corrected, not hidden.",
  ];
  s.addText(notes.map((d, i) => ({ text: d, options: { bullet: { code: "2022" }, breakLine: i < notes.length - 1, color: GRAY, fontSize: 12 } })), {
    x: 7.35, y: 3.1, w: 5.3, h: 2.0, isTextBox: true, paraSpaceAfter: 8,
  });
  footer(s, 5);
}

// ---------- Slide 6: Risk & decisioning ----------
{
  const s = baseSlide(WHITE);
  s.addText("Turning the forecast into a decision", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY, isTextBox: true });
  s.addImage({ path: "chart_risk_grid.png", x: 0.6, y: 1.3, w: 5.4, h: 4.5 });

  const rows = [
    ["Reorder Now", "5 SKUs", "High stockout risk", RED],
    ["Markdown / Clear", "5 SKUs", "High overstock risk", PURPLE],
    ["Watch / Volatile", "0 SKUs", "High on both", "E0A800"],
    ["Healthy", "125 SKUs", "No action needed", GREEN],
  ];
  let ry = 1.5;
  rows.forEach((r) => {
    s.addShape(pres.ShapeType.roundRect, { x: 6.4, y: ry, w: 0.16, h: 0.9, fill: { color: r[3] }, line: { type: "none" }, rectRadius: 0.04 });
    s.addText(r[0], { x: 6.75, y: ry, w: 3.0, h: 0.4, fontSize: 15, bold: true, color: NAVY, isTextBox: true });
    s.addText(r[2], { x: 6.75, y: ry + 0.4, w: 3.0, h: 0.4, fontSize: 11, color: GRAY, isTextBox: true });
    s.addText(r[1], { x: 9.9, y: ry + 0.15, w: 2.7, h: 0.6, fontSize: 20, bold: true, color: r[3], isTextBox: true, align: "right", margin: 0 });
    ry += 1.1;
  });
  s.addText("Every SKU sits on this grid, sized by rupee value at stake — the ops team can triage the whole catalogue at a glance instead of reading a spreadsheet row by row.", {
    x: 6.4, y: ry + 0.1, w: 6.2, h: 0.9, fontSize: 12, italic: true, color: GRAY, isTextBox: true,
  });
  footer(s, 6);
}

// ---------- Slide 7: The dashboard & service ----------
{
  const s = baseSlide(WHITE);
  s.addText("Built to be used without us in the room", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY, isTextBox: true });

  const cols = [
    { t: "Planning dashboard", d: "Filter by category or SKU, see forecast vs. actual, and get a prioritised reorder/markdown list — no spreadsheet required." },
    { t: "Scoring API", d: "Ask for any SKU (or a batch) and get back its forecast, risk level, and recommended action — ready to plug into other tools." },
    { t: "One-command pipeline", d: "The whole system re-runs from raw data with a single command, so next month's numbers are one click away, not a re-engagement." },
  ];
  let cx = 0.7;
  cols.forEach((c) => {
    s.addShape(pres.ShapeType.roundRect, { x: cx, y: 1.7, w: 3.75, h: 3.6, fill: { color: LIGHTGRAY }, rectRadius: 0.12, line: { type: "none" } });
    s.addText(c.t, { x: cx + 0.3, y: 1.95, w: 3.15, h: 0.7, fontSize: 16, bold: true, color: PURPLE, isTextBox: true });
    s.addText(c.d, { x: cx + 0.3, y: 2.65, w: 3.15, h: 2.4, fontSize: 12.5, color: GRAY, isTextBox: true });
    cx += 4.0;
  });
  footer(s, 7);
}

// ---------- Slide 8: Limitations & recommendation ----------
{
  const s = baseSlide(WHITE);
  s.addText("Limitations and what we recommend next", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY, isTextBox: true });

  s.addText("Limitations, stated plainly", { x: 0.7, y: 1.5, w: 5.7, h: 0.4, fontSize: 15, bold: true, color: NAVY, isTextBox: true });
  const lims = [
    "Built and validated on a simulated dataset shaped like NorthBay's real extracts — re-run against live data before acting on the figures.",
    "A stocked-out SKU's recorded sales understate its true demand; this can make some risk scores conservative.",
    "Risk thresholds are a starting point, tuned for this dataset — they should be adjusted against real reorder outcomes.",
  ];
  s.addText(lims.map((d, i) => ({ text: d, options: { bullet: { code: "2022" }, breakLine: i < lims.length - 1, color: GRAY, fontSize: 12.5 } })), {
    x: 0.7, y: 2.0, w: 5.7, h: 3.2, isTextBox: true, paraSpaceAfter: 10,
  });

  s.addText("Recommended next steps", { x: 6.9, y: 1.5, w: 5.7, h: 0.4, fontSize: 15, bold: true, color: NAVY, isTextBox: true });
  const nexts = [
    "Connect real sales and inventory extracts and re-run the pipeline.",
    "Pilot the 5 Reorder-Now recommendations this week; track outcomes.",
    "Review risk thresholds with the ops team after one full cycle.",
    "Extend the promo calendar with confirmed upcoming campaigns.",
  ];
  s.addText(nexts.map((d, i) => ({ text: d, options: { bullet: { code: "2022" }, breakLine: i < nexts.length - 1, color: GRAY, fontSize: 12.5 } })), {
    x: 6.9, y: 2.0, w: 5.7, h: 3.2, isTextBox: true, paraSpaceAfter: 10,
  });
  footer(s, 8);
}

pres.writeFile({ fileName: "FORESIGHT_Executive_Readout.pptx" }).then(() => console.log("done"));
