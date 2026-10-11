import { useEffect, useRef, useState } from 'react';

// Measures the container so SVG charts stay crisp at any width.
function useWidth() {
  const ref = useRef(null);
  const [width, setWidth] = useState(600);
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    if (ref.current) ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  return [ref, width];
}

const PAD = { top: 12, right: 12, bottom: 26, left: 36 };

function niceMax(v) {
  if (v <= 0) return 1;
  const p = 10 ** Math.floor(Math.log10(v));
  return Math.ceil(v / p) * p;
}

function Grid({ max, w, h, format = (v) => v }) {
  const ticks = [0, 0.5, 1].map((t) => t * max);
  return ticks.map((t) => {
    const y = PAD.top + h - (t / max) * h;
    return (
      <g key={t}>
        <line x1={PAD.left} x2={PAD.left + w} y1={y} y2={y} className={t === 0 ? 'axis' : 'gridline'} />
        <text x={PAD.left - 8} y={y + 4} textAnchor="end" className="tick">{format(t)}</text>
      </g>
    );
  });
}

function Tooltip({ x, y, title, rows, containerWidth }) {
  const left = Math.min(x + 12, containerWidth - 170);
  return (
    <div className="chart-tip" style={{ left, top: y }}>
      <div className="chart-tip-title">{title}</div>
      {rows.map((r) => (
        <div key={r.label} className="chart-tip-row">
          {r.color && <i style={{ background: r.color }} />}
          <span>{r.label}</span>
          <b>{r.value}</b>
        </div>
      ))}
    </div>
  );
}

export function Legend({ series }) {
  return (
    <div className="legend">
      {series.map((s) => (
        <span key={s.key}><i style={{ background: s.color }} />{s.label}</span>
      ))}
    </div>
  );
}

// Stacked vertical bars. series[0] sits on the baseline.
export function StackedBars({ data, series, height = 220 }) {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState(null);
  const w = width - PAD.left - PAD.right;
  const h = height - PAD.top - PAD.bottom;
  const max = niceMax(Math.max(...data.map((d) => series.reduce((s, k) => s + d[k.key], 0))));
  const slot = w / data.length;
  const barW = Math.max(4, slot - 6);

  return (
    <div ref={ref} className="chart" onMouseLeave={() => setHover(null)}>
      <svg width={width} height={height}>
        <Grid max={max} w={w} h={h} />
        {data.map((d, i) => {
          const x = PAD.left + i * slot + (slot - barW) / 2;
          let base = PAD.top + h;
          const total = series.reduce((s, k) => s + d[k.key], 0);
          const visible = series.filter((s) => d[s.key] > 0);
          return (
            <g key={i} className={hover && hover.i !== i ? 'dim' : ''}>
              {series.map((s) => {
                const v = d[s.key];
                if (!v) return null;
                const bh = (v / max) * h;
                const isTop = s.key === visible[visible.length - 1].key;
                base -= bh;
                const y = base;
                // 2px surface gap between stacked segments
                const gap = isTop ? 0 : 2;
                return isTop ? (
                  <path
                    key={s.key}
                    fill={s.color}
                    d={`M${x},${y + bh} V${y + Math.min(4, bh)} Q${x},${y} ${x + Math.min(4, barW / 2)},${y} H${x + barW - Math.min(4, barW / 2)} Q${x + barW},${y} ${x + barW},${y + Math.min(4, bh)} V${y + bh} Z`}
                  />
                ) : (
                  <rect key={s.key} x={x} y={y + gap} width={barW} height={Math.max(0, bh - gap)} fill={s.color} />
                );
              })}
              {/* hit target is the full column, larger than the bar */}
              <rect
                x={PAD.left + i * slot}
                y={PAD.top}
                width={slot}
                height={h}
                fill="transparent"
                onMouseEnter={() => setHover({ i, x: PAD.left + i * slot + slot / 2, y: PAD.top + h - (total / max) * h })}
              />
              {i % 6 === 0 && (
                <text x={PAD.left + i * slot + slot / 2} y={height - 8} textAnchor="middle" className="tick">{d.label}</text>
              )}
            </g>
          );
        })}
      </svg>
      {hover && (
        <Tooltip
          x={hover.x}
          y={Math.max(0, hover.y - 20)}
          containerWidth={width}
          title={data[hover.i].label}
          rows={[
            ...series.map((s) => ({ label: s.label, value: data[hover.i][s.key], color: s.color })),
            { label: 'Total', value: series.reduce((t, s) => t + data[hover.i][s.key], 0) },
          ]}
        />
      )}
    </div>
  );
}

// Single-series line with crosshair hover. null values break the line.
export function LineChart({ data, dataKey, color, unit = '', height = 220 }) {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState(null);
  const w = width - PAD.left - PAD.right;
  const h = height - PAD.top - PAD.bottom;
  const values = data.map((d) => d[dataKey]).filter((v) => v != null);
  const max = niceMax(Math.max(1, ...values));
  const xAt = (i) => PAD.left + (i / (data.length - 1)) * w;
  const yAt = (v) => PAD.top + h - (v / max) * h;

  let path = '';
  data.forEach((d, i) => {
    const v = d[dataKey];
    if (v == null) return;
    const prev = data[i - 1]?.[dataKey];
    path += `${prev == null ? 'M' : 'L'}${xAt(i)},${yAt(v)} `;
  });

  function onMove(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    const i = Math.round(((e.clientX - rect.left - PAD.left) / w) * (data.length - 1));
    if (i >= 0 && i < data.length) setHover(i);
  }

  const hv = hover != null ? data[hover][dataKey] : null;

  return (
    <div ref={ref} className="chart" onMouseLeave={() => setHover(null)}>
      <svg width={width} height={height} onMouseMove={onMove}>
        <Grid max={max} w={w} h={h} format={(v) => (v >= 1000 ? `${v / 1000}k` : v)} />
        <path d={path} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        {data.map((d, i) => i % 6 === 0 && (
          <text key={i} x={xAt(i)} y={height - 8} textAnchor="middle" className="tick">{d.label}</text>
        ))}
        {hover != null && (
          <g>
            <line x1={xAt(hover)} x2={xAt(hover)} y1={PAD.top} y2={PAD.top + h} className="crosshair" />
            {hv != null && <circle cx={xAt(hover)} cy={yAt(hv)} r="5" fill={color} className="marker" />}
          </g>
        )}
      </svg>
      {hover != null && (
        <Tooltip
          x={xAt(hover)}
          y={hv != null ? Math.max(0, yAt(hv) - 30) : PAD.top}
          containerWidth={width}
          title={data[hover].label}
          rows={[{ label: 'Avg latency', value: hv != null ? `${hv}${unit}` : 'no live calls', color }]}
        />
      )}
    </div>
  );
}

// Horizontal bars for a single measure across categories, direct-labeled.
export function HBars({ data, color, unit = '' }) {
  const [hover, setHover] = useState(null);
  const max = Math.max(1, ...data.map((d) => d.value));
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  return (
    <div className="hbars">
      {data.map((d) => (
        <div
          key={d.name}
          className={`hbar-row ${hover && hover !== d.name ? 'dim' : ''}`}
          onMouseEnter={() => setHover(d.name)}
          onMouseLeave={() => setHover(null)}
          title={`${d.name}: ${d.value}${unit} (${Math.round((d.value / total) * 100)}%)`}
        >
          <span className="hbar-label">{d.name}</span>
          <div className="hbar-track">
            <div className="hbar-fill" style={{ width: `${(d.value / max) * 100}%`, background: color }} />
          </div>
          <span className="hbar-value">{d.value}{unit} <em>{Math.round((d.value / total) * 100)}%</em></span>
        </div>
      ))}
    </div>
  );
}
