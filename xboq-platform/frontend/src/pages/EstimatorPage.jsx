import { useState } from 'react'
import { Link } from 'react-router-dom'
import '../styles/EstimatorPage.css'

// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

function EstimatorPage() {
  const [trade, setTrade] = useState('drywall')
  const [mode, setMode] = useState('manual')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // Manual input state
  const [rooms, setRooms] = useState([
    {
      id: 1,
      name: 'Room 1',
      length: 20,
      width: 15,
      height: 9,
      doors: 1,
      windows: 2
    }
  ])

  const addRoom = () => {
    const newId = Math.max(...rooms.map(r => r.id), 0) + 1
    setRooms([...rooms, {
      id: newId,
      name: `Room ${newId}`,
      length: 12,
      width: 10,
      height: 9,
      doors: 1,
      windows: 1
    }])
  }

  const removeRoom = (id) => {
    if (rooms.length === 1) {
      alert('You must have at least one room')
      return
    }
    setRooms(rooms.filter(r => r.id !== id))
  }

  const updateRoom = (id, field, value) => {
    setRooms(rooms.map(r =>
      r.id === id ? { ...r, [field]: value } : r
    ))
  }

  const handleManualEstimate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    const payload = {
      trade: trade,
      rooms: rooms.map(r => ({
        name: r.name,
        length: parseFloat(r.length),
        width: parseFloat(r.width),
        height: parseFloat(r.height),
        doors: parseInt(r.doors),
        windows: parseInt(r.windows)
      })),
      finish_level: 4,
      project_type: 'commercial'
    }

    try {
      const response = await fetch(`${API_URL}/api/estimate/manual`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleUploadEstimate = async () => {
    if (!file) {
      setError('Please select a floor plan file')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('trade', trade)

    try {
      const response = await fetch(`${API_URL}/api/estimate/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="estimator-page">
      <nav className="tool-nav">
        <Link to="/" className="back-link">← Back to Home</Link>
        <h1>🏗️ Construction Estimator</h1>
      </nav>

      <div className="estimator-container">
        {/* Trade Selector */}
        <div className="trade-selector">
          <label>Select Trade:</label>
          <select value={trade} onChange={(e) => setTrade(e.target.value)}>
            <option value="drywall">Drywall</option>
            <option value="painting">Painting</option>
            <option value="concrete" disabled>Concrete (Coming Soon)</option>
          </select>
        </div>

        {/* Mode Toggle */}
        <div className="mode-toggle">
          <button
            className={mode === 'manual' ? 'active' : ''}
            onClick={() => setMode('manual')}
          >
            📝 Manual Input
          </button>
          <button
            className={mode === 'upload' ? 'active' : ''}
            onClick={() => setMode('upload')}
          >
            📄 Upload Floor Plan
          </button>
        </div>

        {/* Manual Mode */}
        {mode === 'manual' && (
          <div className="manual-mode">
            <h2>Enter Room Dimensions</h2>
            <p className="mode-description">
              Add one or more rooms and specify their dimensions
            </p>

            {rooms.map((room) => (
              <div key={room.id} className="room-card">
                <div className="room-header">
                  <input
                    type="text"
                    value={room.name}
                    onChange={(e) => updateRoom(room.id, 'name', e.target.value)}
                    className="room-name-input"
                  />
                  {rooms.length > 1 && (
                    <button
                      className="remove-room-btn"
                      onClick={() => removeRoom(room.id)}
                    >
                      ✕
                    </button>
                  )}
                </div>

                <div className="room-inputs">
                  <div className="input-group">
                    <label>Length (ft)</label>
                    <input
                      type="number"
                      value={room.length}
                      onChange={(e) => updateRoom(room.id, 'length', e.target.value)}
                      min="1"
                      step="0.1"
                    />
                  </div>

                  <div className="input-group">
                    <label>Width (ft)</label>
                    <input
                      type="number"
                      value={room.width}
                      onChange={(e) => updateRoom(room.id, 'width', e.target.value)}
                      min="1"
                      step="0.1"
                    />
                  </div>

                  <div className="input-group">
                    <label>Height (ft)</label>
                    <input
                      type="number"
                      value={room.height}
                      onChange={(e) => updateRoom(room.id, 'height', e.target.value)}
                      min="1"
                      step="0.1"
                    />
                  </div>

                  <div className="input-group">
                    <label>Doors</label>
                    <input
                      type="number"
                      value={room.doors}
                      onChange={(e) => updateRoom(room.id, 'doors', e.target.value)}
                      min="0"
                    />
                  </div>

                  <div className="input-group">
                    <label>Windows</label>
                    <input
                      type="number"
                      value={room.windows}
                      onChange={(e) => updateRoom(room.id, 'windows', e.target.value)}
                      min="0"
                    />
                  </div>
                </div>

                <div className="room-summary">
                  Perimeter: {2 * (parseFloat(room.length) + parseFloat(room.width))} ft |
                  Floor Area: {parseFloat(room.length) * parseFloat(room.width)} sqft
                </div>
              </div>
            ))}

            <button className="add-room-btn" onClick={addRoom}>
              + Add Another Room
            </button>

            <button
              className="generate-btn"
              onClick={handleManualEstimate}
              disabled={loading}
            >
              {loading ? '⏳ Generating Estimate...' : `🚀 Generate ${trade.charAt(0).toUpperCase() + trade.slice(1)} Estimate`}
            </button>
          </div>
        )}

        {/* Upload Mode */}
        {mode === 'upload' && (
          <div className="upload-mode">
            <h2>Upload Floor Plan</h2>
            <p className="mode-description">
              Upload a PDF floor plan and we'll analyze it to generate your estimate
            </p>

            <div className="upload-section">
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => setFile(e.target.files[0])}
                disabled={loading}
              />

              {file && (
                <div className="file-info">
                  <span className="file-icon">📄</span>
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
              )}

              <button
                className="generate-btn"
                onClick={handleUploadEstimate}
                disabled={loading || !file}
              >
                {loading ? '⏳ Processing Floor Plan...' : '🚀 Upload & Generate Estimate'}
              </button>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="error-box">
            <strong>❌ Error:</strong> {error}
          </div>
        )}

        {/* Results Display */}
        {result && result.status === 'success' && result.estimate && (
          <div className="results-section">
            <h2 className="results-title">
              ✅ {trade.charAt(0).toUpperCase() + trade.slice(1)} Estimate Generated
            </h2>

            {/* Summary */}
            {result.estimate.summary && (
              <div className="result-card summary-card">
                <h3>📊 Project Summary</h3>
                <div className="summary-grid">
                  {Object.entries(result.estimate.summary).map(([key, value]) => (
                    <div key={key} className="summary-item">
                      <span className="label">{formatLabel(key)}</span>
                      <span className="value">{formatValue(key, value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Materials */}
            {result.estimate.materials && (
              <div className="result-card materials-card">
                <h3>🧱 Materials Required</h3>
                <div className="materials-grid">
                  {Object.entries(result.estimate.materials).map(([key, value]) => (
                    <div key={key} className="material-item">
                      <span className="label">{formatLabel(key)}</span>
                      <span className="value">{formatValue(key, value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Labor */}
            {result.estimate.labor && (
              <div className="result-card labor-card">
                <h3>👷 Labor Breakdown</h3>
                <div className="labor-grid">
                  {Object.entries(result.estimate.labor).map(([key, value]) => (
                    <div key={key} className="labor-item">
                      <span className="label">{formatLabel(key)}</span>
                      <span className="value">{formatValue(key, value)} hrs</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Costs */}
            {result.estimate.costs && (
              <div className="result-card costs-card">
                <h3>💰 Cost Breakdown</h3>
                <div className="costs-table">
                  {Object.entries(result.estimate.costs).map(([key, value]) => (
                    <div key={key} className={`cost-row ${key === 'total_cost' ? 'total-row' : ''}`}>
                      <span className="label">{formatLabel(key)}</span>
                      <span className="value">{formatCost(key, value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Raw JSON Toggle */}
            <details className="raw-json-toggle">
              <summary>🔍 View Raw JSON</summary>
              <pre className="json-display">{JSON.stringify(result, null, 2)}</pre>
            </details>
          </div>
        )}

        {/* Partial Results */}
        {result && result.status === 'partial' && (
          <div className="results-section">
            <h2 className="results-title">⚠️ Estimate Generated (Partial)</h2>
            <div className="result-card">
              <pre className="json-display">{JSON.stringify(result, null, 2)}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Helper functions
function formatLabel(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

function formatValue(key, value) {
  if (key.includes('sqft') || key.includes('area')) {
    return `${value.toLocaleString()} sqft`
  }
  if (key.includes('lf') || key.includes('linear')) {
    return `${value.toLocaleString()} ft`
  }
  return value.toLocaleString()
}

function formatCost(key, value) {
  if (key === 'cost_per_sqft') {
    return `$${value.toFixed(2)}/sqft`
  }
  return `$${value.toLocaleString()}`
}

export default EstimatorPage
