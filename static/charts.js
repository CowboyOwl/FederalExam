function percentageBar(value) {
  return Math.max(0, Math.min(100, Number(value) || 0));
}

function renderChart(element) {
  const series = JSON.parse(element.dataset.series || "[]");
  const type = element.dataset.chart || "attempts";
  const width = 520;
  const height = 220;
  const padding = 34;
  const values = series.map((item) => Number(item[type] || 0));
  const maxValue = type === "accuracy" ? 100 : Math.max(1, ...values);
  const points = values.map((value, index) => {
    const x = series.length <= 1
      ? width / 2
      : padding + (index * (width - padding * 2)) / (series.length - 1);
    const y = height - padding - (value / maxValue) * (height - padding * 2);
    return { x, y, value, label: series[index]?.date || "" };
  });

  if (!series.length) {
    element.innerHTML = '<div class="empty-chart">Aucune donnée pour le moment.</div>';
    return;
  }

  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");
  const circles = points.map((point) => `
    <circle cx="${point.x}" cy="${point.y}" r="4">
      <title>${point.label}: ${point.value}${type === "accuracy" ? "%" : ""}</title>
    </circle>
  `).join("");
  element.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Graphique ${type}">
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" />
      <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" />
      <polyline points="${polyline}" />
      ${circles}
    </svg>
  `;
}

document.querySelectorAll("[data-chart]").forEach(renderChart);
