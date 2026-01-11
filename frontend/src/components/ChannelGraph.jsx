import React, { useMemo, useState } from 'react'

function parseDurationToSeconds(iso) {
  if (!iso || typeof iso !== 'string') return 0
  const m = iso.match(/^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/)
  if (m) {
    const h = parseInt(m[1] || '0', 10)
    const min = parseInt(m[2] || '0', 10)
    const s = parseInt(m[3] || '0', 10)
    return h * 3600 + min * 60 + s
  }
  const m2 = iso.match(/^P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/)
  if (m2) {
    const d = parseInt(m2[1] || '0', 10)
    const h = parseInt(m2[2] || '0', 10)
    const min = parseInt(m2[3] || '0', 10)
    const s = parseInt(m2[4] || '0', 10)
    return d * 86400 + h * 3600 + min * 60 + s
  }
  return 0
}

function computeDerived(items) {
  const parsed = (items || [])
    .map((it) => {
      const date = it?.snippet?.publishedAt ? new Date(it.snippet.publishedAt) : null
      const views = Number(it?.statistics?.viewCount ?? 0)
      const likes = Number(it?.statistics?.likeCount ?? 0)
      const comments = Number(it?.statistics?.commentCount ?? 0)
      const durationSec = parseDurationToSeconds(it?.contentDetails?.duration)
      const hour = date ? date.getUTCHours() : 0
      return {
        item: it,
        date,
        viewCount: views,
        likeCount: likes,
        commentCount: comments,
        durationSeconds: durationSec,
        hourOfDay: hour,
      }
    })
    .filter((p) => p.date)
    .sort((a, b) => a.date - b.date)

  if (parsed.length === 0) return []
  const firstDate = parsed[0].date
  return parsed.map((p) => ({
    ...p,
    daysSinceOrigination: Math.max(0, Math.floor((p.date - firstDate) / (24 * 3600 * 1000))),
  }))
}

export default function ChannelGraph({ items = [], xKey = 'daysSinceOrigination', yKey = 'viewCount', width = 640, height = 360, padding = 32 }) {
  const data = useMemo(() => computeDerived(items), [items])
  const n = data.length
  const innerW = width - padding * 2
  const innerH = height - padding * 2

  const getVal = (row, key) => {
    const v = row[key]
    return typeof v === 'number' && isFinite(v) ? v : 0
  }

  const minX = useMemo(() => (n ? Math.min(...data.map((d) => getVal(d, xKey))) : 0), [data, xKey, n])
  const maxX = useMemo(() => (n ? Math.max(...data.map((d) => getVal(d, xKey))) : 0), [data, xKey, n])
  const minY = useMemo(() => (n ? Math.min(...data.map((d) => getVal(d, yKey))) : 0), [data, yKey, n])
  const maxY = useMemo(() => (n ? Math.max(...data.map((d) => getVal(d, yKey))) : 0), [data, yKey, n])

  const xToPx = (x) => {
    if (maxX === minX) return width / 2
    return padding + ((x - minX) / (maxX - minX)) * innerW
  }
  const yToPx = (y) => {
    if (maxY === minY) return height / 2
    return height - padding - ((y - minY) / (maxY - minY)) * innerH
  }

  const points = data.map((d) => ({
    x: getVal(d, xKey),
    y: getVal(d, yKey),
    item: d.item,
    date: d.date,
  }))

  const polyline = points.map((p) => `${xToPx(p.x)},${yToPx(p.y)}`).join(' ')

  const [hover, setHover] = useState(null) // { p, px, py }

  return (
    <div style={{ position: 'relative', width, height }}>
      <svg width={width} height={height} style={{ border: '1px solid #ddd', background: '#fafafa' }}>
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#999" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#999" />

        {n > 0 && (
          <polyline points={polyline} fill="none" stroke="#1976d2" strokeWidth="2" />
        )}

        {points.map((p, i) => {
          const px = xToPx(p.x)
          const py = yToPx(p.y)
          return (
            <circle
              key={i}
              cx={px}
              cy={py}
              r={4}
              fill="#1976d2"
              onMouseEnter={() => setHover({ p, px, py })}
              onMouseLeave={() => setHover(null)}
            />
          )
        })}

        <text x={width / 2} y={height - 8} textAnchor="middle" fill="#666" fontSize="12">
          {xKey}
        </text>
        <text x={16} y={16} fill="#666" fontSize="12">
          {yKey}
        </text>
      </svg>

      {hover && (
        <div
          style={{
            position: 'absolute',
            left: Math.min(Math.max(hover.px + 10, 8), width - 220),
            top: Math.min(Math.max(hover.py - 10, 8), height - 140),
            width: 210,
            background: 'white',
            border: '1px solid #ddd',
            boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
            borderRadius: 6,
            padding: 10,
            fontSize: 12,
            color: '#333',
          }}
          onMouseLeave={() => setHover(null)}
        >
          <div style={{ fontWeight: 600, marginBottom: 6 }}>{hover.p.item?.snippet?.title || 'Untitled'}</div>
          <div style={{ marginBottom: 4, color: '#666' }}>
            Published: {hover.p.item?.snippet?.publishedAt ? new Date(hover.p.item.snippet.publishedAt).toLocaleString() : '—'}
          </div>
          <div>Likes: {Number(hover.p.item?.statistics?.likeCount ?? 0).toLocaleString()}</div>
          <div>Comments: {Number(hover.p.item?.statistics?.commentCount ?? 0).toLocaleString()}</div>
          <div style={{ marginTop: 6, display: 'flex', justifyContent: 'space-between' }}>
            <span>
              x={xKey}: {hover.p.x}
            </span>
            <span>
              y={yKey}: {hover.p.y}
            </span>
          </div>
          <div style={{ marginTop: 8, textAlign: 'right' }}>
            <a
              href={`https://www.youtube.com/watch?v=${hover.p.item?.id || ''}`}
              target="_blank"
              rel="noreferrer"
              style={{ color: '#1976d2' }}
            >
              Open episode ↗
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
