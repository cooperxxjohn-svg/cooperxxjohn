import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import EstimatorPage from './pages/EstimatorPage'
import './App.css'

// ============================================================================
// HOMEPAGE - Product Selector
// ============================================================================

function HomePage() {
  const navigate = useNavigate()

  const products = [
    {
      id: 'boq',
      icon: '📋',
      name: 'BOQ Generator',
      tagline: 'Extract Bill of Quantities from tender documents',
      description: 'Upload tender PDFs and get detailed BOQ organized by construction phase. Perfect for government and commercial bidding.',
      features: [
        'AI-powered extraction',
        'Organized by section',
        'Quantities & units',
        'Ready for bidding'
      ],
      route: '/boq',
      color: '#667eea'
    },
    {
      id: 'estimator',
      icon: '🏗️',
      name: 'Construction Estimator',
      tagline: 'Generate detailed estimates for construction trades',
      description: 'Get professional estimates for drywall, painting, and concrete projects in 40 seconds instead of 4 hours.',
      features: [
        'Drywall & painting estimates',
        'Material quantities',
        'Labor breakdown',
        'Complete cost analysis'
      ],
      route: '/estimator',
      color: '#764ba2'
    }
  ]

  return (
    <div className="homepage">
      <header className="hero">
        <h1>XBOQ.AI</h1>
        <p className="tagline">AI-Powered Construction Intelligence</p>
        <p className="subtitle">From Tenders to Takeoffs - AI That Understands Construction</p>
      </header>

      <div className="products-grid">
        {products.map(product => (
          <div
            key={product.id}
            className="product-card"
            style={{ borderTopColor: product.color }}
          >
            <div className="product-icon">{product.icon}</div>
            <h2>{product.name}</h2>
            <p className="product-tagline">{product.tagline}</p>
            <p className="product-description">{product.description}</p>

            <ul className="features-list">
              {product.features.map((feature, idx) => (
                <li key={idx}>✓ {feature}</li>
              ))}
            </ul>

            <button
              className="launch-btn"
              style={{ background: product.color }}
              onClick={() => navigate(product.route)}
            >
              Launch {product.name} →
            </button>
          </div>
        ))}
      </div>

      <section className="use-cases">
        <h2>Built For</h2>
        <div className="use-cases-grid">
          <div className="use-case">
            <h3>📋 Government Contractors</h3>
            <p>Extract BOQ from tender documents for accurate bidding</p>
          </div>
          <div className="use-case">
            <h3>🏗️ Drywall Contractors</h3>
            <p>Generate instant estimates with exact material quantities</p>
          </div>
          <div className="use-case">
            <h3>🎨 Painting Companies</h3>
            <p>Calculate coverage, labor hours, and costs in seconds</p>
          </div>
          <div className="use-case">
            <h3>👷 General Contractors</h3>
            <p>Multi-trade estimates for complete project planning</p>
          </div>
        </div>
      </section>

      <footer className="homepage-footer">
        <p>© 2026 XBOQ.AI - AI-Powered Construction Tools</p>
      </footer>
    </div>
  )
}

// ============================================================================
// BOQ PAGE
// ============================================================================

function BOQPage() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a tender PDF file')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:5000/api/boq/upload', {
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
    <div className="tool-page">
      <nav className="tool-nav">
        <Link to="/" className="back-link">← Back to Home</Link>
        <h1>📋 BOQ Generator</h1>
      </nav>

      <div className="tool-container">
        <div className="upload-section">
          <h2>Upload Tender Document</h2>
          <p>Upload a PDF tender document to extract the Bill of Quantities</p>

          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            disabled={loading}
          />

          {file && <p className="file-info">Selected: {file.name}</p>}

          <button
            onClick={handleUpload}
            disabled={loading || !file}
            className="process-btn"
          >
            {loading ? 'Processing Tender...' : 'Extract BOQ'}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {result && result.status === 'success' && (
          <div className="result">
            <h2>✅ BOQ Extracted Successfully</h2>
            <pre>{JSON.stringify(result.boq, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// MAIN APP - Router
// ============================================================================

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/boq" element={<BOQPage />} />
        <Route path="/estimator" element={<EstimatorPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
