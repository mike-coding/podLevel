import React from 'react'

export default function ChannelGraph({ items = [], width = 640, height = 320, padding = 32, getY }) {
  const parsed = (items || [])
    .map((it) => ({
      date: it?.snippet?.publishedAt ? new Date(it.snippet.publishedAt) : null,
      views: Number(it?.statistics?.viewCount ?? 0),
    }))
    .filter((p) => p.date)
    .sort((a, b) => a.date - b.date)

  const points = parsed.map((p, i) => ({ x: i, y: getY ? getY(p) : p.views }))
  const n = points.length
  const maxY = points.reduce((m, p) => (p.y > m ? p.y : m), 0)

  const innerW = width - padding * 2
  const innerH = height - padding * 2

  const xToPx = (x) => (n > 1 ? (x / (n - 1)) * innerW + padding : width / 2)
  const yToPx = (y) => height - padding - (maxY > 0 ? (y / maxY) * innerH : 0)

  const polyline = points.map((p) => `${xToPx(p.x)},${yToPx(p.y)}`).join(' ')

  return (
    <svg width={width} height={height} style={{ border: '1px solid #ddd', background: '#fafafa' }}>
      <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#999" />
      <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#999" />

      {n > 0 && (
        <polyline points={polyline} fill="none" stroke="#1976d2" strokeWidth="2" />
      )}

      {points.map((p, i) => (
        <circle key={i} cx={xToPx(p.x)} cy={yToPx(p.y)} r={3} fill="#1976d2" />
      ))}

      <text x={width / 2} y={height - 8} textAnchor="middle" fill="#666" fontSize="12">
        Chronological order (older → newer)
      </text>
      <text x={16} y={16} fill="#666" fontSize="12">
        Views
      </text>
    </svg>
  )
}
