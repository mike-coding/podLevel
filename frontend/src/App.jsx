import React, { useEffect, useState } from 'react'

export default function App() {
  const [message, setMessage] = useState('...')

  useEffect(() => {
    fetch('/api/hello')
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch(() => setMessage('Failed to fetch'))
  }, [])

  return (
    <div style={{ fontFamily: 'system-ui', padding: 24 }}>
      <h1>React + Flask</h1>
      <p>{message}</p>
    </div>
  )
}
