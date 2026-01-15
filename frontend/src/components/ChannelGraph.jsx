import React, { useMemo, useState, useEffect, useRef } from 'react'

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

export default function ChannelGraph({ items = [], yKey = 'viewCount', width, height = 360, padding = 32 }) {
  const containerRef = useRef(null)
  const [containerW, setContainerW] = useState(640)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const update = () => setContainerW(el.clientWidth)
    update()

    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(() => update())
      ro.observe(el)
      return () => ro.disconnect()
    } else {
      window.addEventListener('resize', update)
      return () => window.removeEventListener('resize', update)
    }
  }, [])

  const svgW = typeof width === 'number' ? width : containerW
  // Provide extra left padding for y-axis tick labels to avoid clipping
  const padLeft = padding + 32
  const padRight = padding
  const padTop = padding
  const padBottom = padding + 24
  const xKey = 'daysSinceOrigination'
  const data = useMemo(() => computeDerived(items), [items])
  const n = data.length
  const innerW = svgW - padLeft - padRight
  const innerH = height - padTop - padBottom

  const getVal = (row, key) => {
    const v = row[key]
    return typeof v === 'number' && isFinite(v) ? v : 0
  }

  const minX = useMemo(() => (n ? Math.min(...data.map((d) => getVal(d, xKey))) : 0), [data, xKey, n])
  const maxX = useMemo(() => (n ? Math.max(...data.map((d) => getVal(d, xKey))) : 0), [data, xKey, n])
  const minY = useMemo(() => (n ? Math.min(...data.map((d) => getVal(d, yKey))) : 0), [data, yKey, n])
  const maxY = useMemo(() => (n ? Math.max(...data.map((d) => getVal(d, yKey))) : 0), [data, yKey, n])

  const xToPx = (x) => {
    if (maxX === minX) return padLeft + innerW / 2
    return padLeft + ((x - minX) / (maxX - minX)) * innerW
  }
  const yToPx = (y) => {
    if (maxY === minY) return height / 2
    return height - padBottom - ((y - minY) / (maxY - minY)) * innerH
  }

  const points = data.map((d) => ({
    x: getVal(d, xKey),
    y: getVal(d, yKey),
    item: d.item,
    date: d.date,
  }))

  const bestFit = useMemo(() => {
    if (!points || points.length < 2) return null
    const xs = points.map((p) => p.x).filter((x) => typeof x === 'number' && isFinite(x))
    if (new Set(xs).size < 2) return null

    let nFit = 0
    let sumX = 0
    let sumY = 0
    let sumXY = 0
    let sumXX = 0

    for (const p of points) {
      const x = p.x
      const y = p.y
      if (typeof x !== 'number' || !isFinite(x) || typeof y !== 'number' || !isFinite(y)) continue
      nFit += 1
      sumX += x
      sumY += y
      sumXY += x * y
      sumXX += x * x
    }

    if (nFit < 2) return null
    const denom = nFit * sumXX - sumX * sumX
    if (denom === 0) return null

    const slope = (nFit * sumXY - sumX * sumY) / denom
    const intercept = (sumY - slope * sumX) / nFit
    return { slope, intercept, n: nFit }
  }, [points])

  const polyline = points.map((p) => `${xToPx(p.x)},${yToPx(p.y)}`).join(' ')

  const fitLine = useMemo(() => {
    if (!bestFit || n < 2) return null
    const x1 = minX
    const x2 = maxX
    if (!isFinite(x1) || !isFinite(x2) || x1 === x2) return null
    const y1 = bestFit.slope * x1 + bestFit.intercept
    const y2 = bestFit.slope * x2 + bestFit.intercept
    return {
      x1Px: xToPx(x1),
      y1Px: yToPx(y1),
      x2Px: xToPx(x2),
      y2Px: yToPx(y2),
    }
  }, [bestFit, minX, maxX, n, xToPx, yToPx])

  const labelMap = {
    viewCount: 'Views',
    likeCount: 'Likes',
    commentCount: 'Comments',
    durationSeconds: 'Duration (sec)',
    hourOfDay: 'Hour of Day (UTC)',
    daysSinceOrigination: 'Days Since Origination (days)',
  }
  const xLabel = labelMap[xKey] || xKey
  const yLabel = labelMap[yKey] || yKey

  const computeTicks = (min, max, count = 5) => {
    if (!isFinite(min) || !isFinite(max)) return []
    if (max === min) return [min]
    const step = (max - min) / (count - 1)
    const ticks = []
    for (let i = 0; i < count; i++) ticks.push(min + i * step)
    return ticks
  }

  const formatTick = (val, key) => {
    const v = Math.round(val)
    if (key === 'durationSeconds') return `${v}s`
    if (key === 'hourOfDay') return `${v}h`
    if (key === 'daysSinceOrigination') return `${v}d`
    return Number(v).toLocaleString()
  }

  const xTicks = computeTicks(minX, maxX)
  const yTicks = computeTicks(minY, maxY)

  const [hover, setHover] = useState(null) // { p, px, py }

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', height }}>
      <svg width={svgW} height={height} className="graph-frame">
        <line x1={padLeft} y1={height - padBottom} x2={svgW - padRight} y2={height - padBottom} stroke="#999" />
        <line x1={padLeft} y1={padTop} x2={padLeft} y2={height - padBottom} stroke="#999" />

        {/* X-axis ticks with units */}
        {xTicks.map((t, i) => {
          const tx = xToPx(t)
          return (
            <g key={`xt-${i}`}>
              <line x1={tx} y1={height - padBottom} x2={tx} y2={height - padBottom + 6} stroke="#bbb" />
              <text x={tx} y={height - padBottom + 16} textAnchor="middle" className="tick-text" fontSize="11">
                {formatTick(t, xKey)}
              </text>
            </g>
          )
        })}

        {/* Y-axis ticks with units */}
        {yTicks.map((t, i) => {
          const ty = yToPx(t)
          return (
            <g key={`yt-${i}`}>
              <line x1={padLeft - 6} y1={ty} x2={padLeft} y2={ty} stroke="#bbb" />
              <text x={padLeft - 8} y={ty + 4} textAnchor="end" className="tick-text" fontSize="11">
                {formatTick(t, yKey)}
              </text>
            </g>
          )
        })}

        {n > 0 && (
          <polyline points={polyline} fill="none" className="line-primary" strokeWidth="2" />
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
              className="point"
              onMouseEnter={() => setHover({ p, px, py })}
              onMouseLeave={() => setHover(null)}
            />
          )
        })}

        {/* Draw trend line last so it sits on top of series + points */}
        {fitLine && (
          <g pointerEvents="none">
            {/* underlay for contrast */}
            <line
              x1={fitLine.x1Px}
              y1={fitLine.y1Px}
              x2={fitLine.x2Px}
              y2={fitLine.y2Px}
              stroke="#000"
              strokeOpacity="0.45"
              strokeWidth="6"
              strokeLinecap="round"
            />
            {/* visible dashed trend */}
            <line
              x1={fitLine.x1Px}
              y1={fitLine.y1Px}
              x2={fitLine.x2Px}
              y2={fitLine.y2Px}
              className="line-fit"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </g>
        )}

        <text x={svgW / 2} y={height - 8} textAnchor="middle" className="axis-text" fontSize="12">
          {xLabel}
        </text>
        <text x={16} y={16} className="axis-text" fontSize="12">
          {yLabel}
        </text>
      </svg>

      {hover && (
        <div
          style={{
            position: 'absolute',
            left: Math.min(Math.max(hover.px + 10, 8), svgW - 220),
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
            Published (UTC): {hover.p.item?.snippet?.publishedAt
              ? new Date(hover.p.item.snippet.publishedAt).toLocaleString(undefined, { timeZone: 'UTC' })
              : '—'}
          </div>
          <div>Likes: {Number(hover.p.item?.statistics?.likeCount ?? 0).toLocaleString()}</div>
          <div>Comments: {Number(hover.p.item?.statistics?.commentCount ?? 0).toLocaleString()}</div>
          <div style={{ marginTop: 6, display: 'flex', justifyContent: 'space-between' }}>
            <span>
              X: {xLabel}: {hover.p.x}
            </span>
            <span>
              Y: {yLabel}: {yKey === 'durationSeconds' ? `${hover.p.y}s` : hover.p.y}
            </span>
          </div>
          <div style={{ marginTop: 8, textAlign: 'right' }}>
            <a
              href={`https://www.youtube.com/watch?v=${hover.p.item?.id || ''}`}
              target="_blank"
              rel="noreferrer"
              className="link"
            >
              Open episode ↗
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
