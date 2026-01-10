import React, { useState } from 'react'
import ChannelGraph from './components/ChannelGraph.jsx'

export default function App() {
  const [channelId, setChannelId] = useState('')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  return (
    <div style={{ fontFamily: 'system-ui', padding: 24 }}>
      <h1>Pod Level YouTube Channel Lookup</h1>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 16 }}>
        <input
          type="text"
          placeholder="Enter channel ID"
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          style={{ padding: 8, width: 320 }}
        />
        <button
          onClick={async () => {
            setError('')
            setLoading(true)
            setItems([])
            try {
              const res = await fetch(`/api/channel/${encodeURIComponent(channelId)}/videos`)
              const data = await res.json()
              setItems(Array.isArray(data.items) ? data.items : [])
            } catch (e) {
              setError('Lookup failed')
            } finally {
              setLoading(false)
            }
          }}
          disabled={!channelId || loading}
          style={{ padding: '8px 12px' }}
        >
          {loading ? 'Looking up…' : 'Lookup'}
        </button>
        {error && <span style={{ color: 'crimson' }}>{error}</span>}
      </div>

      <div style={{ marginTop: 24 }}>
        <ChannelGraph items={items} width={800} height={360} />
        <div style={{ marginTop: 8, color: '#666' }}>
          {items.length > 0 ? `Loaded ${items.length} videos` : 'No videos loaded'}
        </div>
      </div>
    </div>
  )
}
