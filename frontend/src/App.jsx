import React, { useState } from 'react'
import ChannelGraph from './components/ChannelGraph.jsx'
import Statistics from './components/Statistics.jsx'

export default function App() {
  const [channelId, setChannelId] = useState('')
  const [items, setItems] = useState([])
  const [mlData, setMlData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const yAxisOptions = [
    { key: 'viewCount', label: 'Views' },
    { key: 'likeCount', label: 'Likes' },
    { key: 'commentCount', label: 'Comments' },
    { key: 'durationSeconds', label: 'Duration (sec)' },
    { key: 'hourOfDay', label: 'Hour of Day (UTC)' },
  ]
  const [yKey, setYKey] = useState('viewCount')

  return (
    <div className="app">
      <div className="app-header">
        <h1 className="app-title">Pod Level</h1>
        <div className="subtitle">YouTube Channel Insights</div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-body">
          <div className="controls-row">
            <input
              type="text"
              className="input"
              placeholder="Enter channel ID or @handle"
              value={channelId}
              onChange={(e) => setChannelId(e.target.value)}
            />
            <button
              className="btn btn-primary"
              onClick={async () => {
                setError('')
                setLoading(true)
                setItems([])
                setMlData(null)
                try {
                  const res = await fetch(`/api/channel/${encodeURIComponent(channelId)}/videos`)
                  const data = await res.json()
                  setItems(Array.isArray(data.items) ? data.items : [])
                  setMlData(data.data_ml ?? null)
                } catch (e) {
                  setError('Lookup failed')
                } finally {
                  setLoading(false)
                }
              }}
              disabled={!channelId || loading}
            >
              {loading ? 'Looking up…' : 'Lookup'}
            </button>
            {error && <span className="error">{error}</span>}
          </div>
          <div className="controls-row" style={{ marginTop: 12 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              Y:
              <select className="select" value={yKey} onChange={(e) => setYKey(e.target.value)}>
                {yAxisOptions.map(opt => (
                  <option key={opt.key} value={opt.key}>{opt.label}</option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </div>

      <div className="content-grid">
        <div className="panel-card panel">
          <h3 className="panel-title">Channel Graph</h3>
          <ChannelGraph items={items} yKey={yKey} height={380} />
          <div className="subtitle" style={{ marginTop: 8 }}>
            {items.length > 0 ? `Loaded ${items.length} videos` : 'No videos loaded'}
          </div>
        </div>
        <div className="panel-card panel">
          <h3 className="panel-title">Statistics</h3>
          <Statistics mlData={mlData} />
        </div>
      </div>
    </div>
  )
}
