import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SessionProvider } from './contexts/SessionContext'
import Layout from './components/Layout'
import SetupPage from './pages/SetupPage'
import ReviewPage from './pages/ReviewPage'
import FilesPage from './pages/FilesPage'
import RepositoryPage from './pages/RepositoryPage'
import ProvisioningPage from './pages/ProvisioningPage'
import SuccessPage from './pages/SuccessPage'

function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/setup" replace />} />
            <Route path="/setup" element={<SetupPage />} />
            <Route path="/review" element={<ReviewPage />} />
            <Route path="/files" element={<FilesPage />} />
            <Route path="/repository" element={<RepositoryPage />} />
            <Route path="/provisioning" element={<ProvisioningPage />} />
            <Route path="/success" element={<SuccessPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </SessionProvider>
  )
}

export default App

