export function drawWaveChart(waves, canvasId = "waveChart") {
  const c = document.getElementById(canvasId);
  if (!c) return;
  const ctx = c.getContext("2d");
  c.width = c.clientWidth || 800;
  c.height = c.clientHeight || 150;
  ctx.clearRect(0, 0, c.width, c.height);
  if (!waves || !waves.length) return;

  const maxW = Math.max(5.0, ...waves.map(w => w.wave_height_m || 0));
  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 3;
  ctx.beginPath();

  waves.forEach((w, i) => {
    const x = 30 + (i / Math.max(1, waves.length - 1)) * (c.width - 60);
    const y = c.height - 20 - ((w.wave_height_m || 0) / maxW) * (c.height - 40);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);

    ctx.fillStyle = "#bae6fd";
    ctx.font = "11px sans-serif";
    ctx.fillText(`${(w.wave_height_m || 0).toFixed(1)}m`, x - 10, y - 6);
  });
  ctx.stroke();
}
