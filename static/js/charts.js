// Simple bar chart renderer
const Charts = {
  renderBar(containerId, data, labelKey, valueKey, prefix = '') {
    const el = document.getElementById(containerId);
    if (!el || !data.length) return;
    const max = Math.max(...data.map(d => d[valueKey])) || 1;
    el.innerHTML = data.map(d => {
      const pct = Math.max((d[valueKey] / max) * 100, 2);
      const val = typeof d[valueKey] === 'number' ? prefix + d[valueKey].toLocaleString() : d[valueKey];
      return `<div class="chart-bar-wrapper">
        <span class="chart-bar-value">${val}</span>
        <div class="chart-bar" style="height:${pct}%"></div>
        <span class="chart-bar-label">${d[labelKey]}</span>
      </div>`;
    }).join('');
  },
  monthName(m) {
    return ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m - 1] || m;
  }
};
