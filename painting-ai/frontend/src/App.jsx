import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ProjectView from './pages/ProjectView'
import NewProject from './pages/NewProject'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="new" element={<NewProject />} />
          <Route path="projects/:projectId" element={<ProjectView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
