import { useState } from 'react'
import './App.css'

function App() {
  const [mode, setMode] = useState('manual') // 'manual' or 'upload'
  const [trade, setTrade] = useState('drywall')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // Manual input state
  const [rooms, setRooms] = useState([
    {
      name: 'Room 1',
      length: 20,
      width: 15,
      height: 9,
      doors: 1,
      windows: 2
    }
  ])

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setError(null)
  }

  const handleUploadEstimate = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('trade', trade)

    try {
      const response = await fetch('http://localhost:5000/estimate/upload', {
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

  const handleManualEstimate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    const payload = {
      trade: trade,
      rooms: rooms,
      project_type: 'commercial',
      finish_level: 4
    }

    try {
      const response = await fetch('http://localhost:5000/estimate/manual', {
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

  const addRoom = () => {
    setRooms([...rooms, {
      name: `Room ${rooms.length + 1}`,
      length: 12,
      width: 10,
      height: 9,
      doors: 1,
      windows: 1
    }])
  }

  const updateRoom = (index, field, value) => {
    const newRooms = [...rooms]
    newRooms[index][field] = value
    setRooms(newRooms)
  }

  const removeRoom = (index) => {
    setRooms(rooms.filter((_, i) => i !== index))
  }

  return (
    <div className="container">
      <header>
        <h1>🏗️ Construction Estimator</h1>
        <p>AI-Powered Takeoffs for Contractors</p>
      </header>

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
          Manual Input
        </button>
        <button
          className={mode === 'upload' ? 'active' : ''}
          onClick={() => setMode('upload')}
        >
          Upload Floor Plan
        </button>
      </div>

      {/* Manual Input Mode */}
      {mode === 'manual' && (
        <div className="manual-mode">
          <h2>Enter Room Dimensions</h2>

          {rooms.map((room, index) => (
            <div key={index} className="room-card">
              <div className="room-header">
                <input
                  type="text"
                  value={room.name}
                  onChange={(e) => updateRoom(index, 'name', e.target.value)}
                  placeholder="Room Name"
                />
                {rooms.length > 1 && (
                  <button
                    className="remove-btn"
                    onClick={() => removeRoom(index)}
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
                    onChange={(e) => updateRoom(index, 'length', parseFloat(e.target.value))}
                  />
                </div>

                <div className="input-group">
                  <label>Width (ft)</label>
                  <input
                    type="number"
                    value={room.width}
                    onChange={(e) => updateRoom(index, 'width', parseFloat(e.target.value))}
                  />
                </div>

                <div className="input-group">
                  <label>Height (ft)</label>
                  <input
                    type="number"
                    value={room.height}
                    onChange={(e) => updateRoom(index, 'height', parseFloat(e.target.value))}
                  />
                </div>

                <div className="input-group">
                  <label>Doors</label>
                  <input
                    type="number"
                    value={room.doors}
                    onChange={(e) => updateRoom(index, 'doors', parseInt(e.target.value))}
                  />
                </div>

                <div className="input-group">
                  <label>Windows</label>
                  <input
                    type="number"
                    value={room.windows}
                    onChange={(e) => updateRoom(index, 'windows', parseInt(e.target.value))}
                  />
                </div>
              </div>
            </div>
          ))}

          <button className="add-room-btn" onClick={addRoom}>
            + Add Another Room
          </button>

          <button
            className="estimate-btn"
            onClick={handleManualEstimate}
            disabled={loading || rooms.length === 0}
          >
            {loading ? 'Generating Estimate...' : 'Generate Estimate'}
          </button>
        </div>
      )}

      {/* Upload Mode */}
      {mode === 'upload' && (
        <div className="upload-mode">
          <h2>Upload Floor Plan</h2>
          <p>Upload a PDF floor plan and we'll analyze it to generate your estimate.</p>

          <div className="upload-section">
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              disabled={loading}
            />
            <button
              onClick={handleUploadEstimate}
              disabled={loading || !file}
              className="estimate-btn"
            >
              {loading ? 'Processing Floor Plan...' : 'Upload & Generate Estimate'}
            </button>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results Display */}
      {result && result.status === 'success' && (
        <div className="result">
          <h2>✅ Estimate Generated Successfully</h2>

          {result.estimate && (
            <div className="estimate-content">
              {/* Summary */}
              {result.estimate.summary && (
                <div className="section">
                  <h3>Project Summary</h3>
                  <div className="summary-grid">
                    {Object.entries(result.estimate.summary).map(([key, value]) => (
                      <div key={key} className="summary-item">
                        <span className="label">{key.replace(/_/g, ' ')}:</span>
                        <span className="value">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Materials */}
              {result.estimate.materials && (
                <div className="section">
                  <h3>Materials</h3>
                  <div className="materials-grid">
                    {Object.entries(result.estimate.materials).map(([key, value]) => (
                      <div key={key} className="material-item">
                        <span className="label">{key.replace(/_/g, ' ')}:</span>
                        <span className="value">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Labor */}
              {result.estimate.labor && (
                <div className="section">
                  <h3>Labor Breakdown</h3>
                  <div className="labor-grid">
                    {Object.entries(result.estimate.labor).map(([key, value]) => (
                      <div key={key} className="labor-item">
                        <span className="label">{key.replace(/_/g, ' ')}:</span>
                        <span className="value">{value} hrs</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Costs */}
              {result.estimate.costs && (
                <div className="section costs-section">
                  <h3>Cost Breakdown</h3>
                  <div className="costs-table">
                    {Object.entries(result.estimate.costs).map(([key, value]) => (
                      <div key={key} className={`cost-row ${key === 'total_cost' ? 'total' : ''}`}>
                        <span className="label">{key.replace(/_/g, ' ')}:</span>
                        <span className="value">
                          {key.includes('cost') || key.includes('total') || key.includes('overhead') || key.includes('profit')
                            ? `$${value.toLocaleString()}`
                            : `$${value}/sqft`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Raw JSON Toggle */}
          <details className="raw-json">
            <summary>View Raw JSON</summary>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}

      {/* Partial Results */}
      {result && result.status === 'partial' && (
        <div className="result partial">
          <h2>⚠️ Estimate Generated (Partial Format)</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default App
