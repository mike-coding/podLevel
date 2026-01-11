import React from 'react'

export default function Statistics({ mlData }) {
  if (!mlData || typeof mlData !== 'object') {
    return <div className="subtitle">ML data unavailable</div>
  }

  const { metrics = {}, intercept, coefficients = {}, n_train, n_test } = mlData

  const coefEntries = Object.entries(coefficients || {})
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))

  return (
    <div>
      <div className="stats-section">
        <div className="stats-box">
          <h3 className="panel-title">Metrics</h3>
          <ul className="stats-list">
            {Object.entries(metrics).map(([key, val]) => (
              <li key={key}><strong>{key}:</strong> {typeof val === 'number' ? val.toFixed(4) : String(val)}</li>
            ))}
            {typeof intercept === 'number' && (
              <li><strong>intercept:</strong> {intercept.toFixed(4)}</li>
            )}
            {(typeof n_train === 'number' || typeof n_test === 'number') && (
              <li><strong>samples:</strong> train {n_train ?? '-'}, test {n_test ?? '-'}
              </li>
            )}
          </ul>
        </div>

        <div className="stats-box">
          <h3 className="panel-title">Top Coefficients</h3>
          {coefEntries.length === 0 ? (
            <div className="subtitle">No coefficients</div>
          ) : (
            <table className="stats-table">
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>Feature</th>
                  <th style={{ textAlign: 'right' }}>Coefficient</th>
                </tr>
              </thead>
              <tbody>
                {coefEntries.slice(0, 10).map(({ name, value }) => (
                  <tr key={name}>
                    <td>{name}</td>
                    <td style={{ textAlign: 'right' }}>{value.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
