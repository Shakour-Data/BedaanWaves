"use client";

interface SpiderChartProps {
  labels: string[];
  values: number[];
  max?: number;
  height?: number;
}

export function SpiderChart({ labels, values, max = 100, height = 320 }: SpiderChartProps) {
  const size = Math.min(height, 400);
  const center = size / 2;
  const radius = size * 0.38;
  const levels = 5;
  const angleStep = (2 * Math.PI) / labels.length;

  const points = labels.map((_, i) => {
    const angle = i * angleStep - Math.PI / 2;
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle) };
  });

  const valuePoints = values.map((v, i) => {
    const r = radius * (Math.min(v, max) / max);
    const angle = i * angleStep - Math.PI / 2;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle) };
  });

  const polygonPoints = valuePoints.map((p) => `${p.x},${p.y}`).join(" ");

  const gridLevels = Array.from({ length: levels }, (_, i) => (i + 1) / levels);

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="w-full" style={{ height: size }}>
      {gridLevels.map((level) => {
        const levelPoints = points
          .map((p) => {
            const dx = p.x - center;
            const dy = p.y - center;
            return `${center + dx * level},${center + dy * level}`;
          })
          .join(" ");
        return (
          <polygon
            key={level}
            points={levelPoints}
            fill="none"
            stroke="currentColor"
            strokeWidth="0.5"
            className="text-gray-300 dark:text-gray-600"
          />
        );
      })}

      {points.map((p, i) => (
        <line
          key={i}
          x1={center}
          y1={center}
          x2={p.x}
          y2={p.y}
          stroke="currentColor"
          strokeWidth="0.5"
          className="text-gray-300 dark:text-gray-600"
        />
      ))}

      <polygon points={polygonPoints} fill="rgba(37,99,235,0.15)" stroke="#2563EB" strokeWidth="2" />

      {valuePoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3" fill="#2563EB" />
      ))}

      {labels.map((label, i) => {
        const angle = i * angleStep - Math.PI / 2;
        const labelRadius = radius + 18;
        const x = center + labelRadius * Math.cos(angle);
        const y = center + labelRadius * Math.sin(angle);
        return (
          <text
            key={i}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-current text-xs text-gray-600 dark:text-gray-300"
          >
            {label}
          </text>
        );
      })}
    </svg>
  );
}
