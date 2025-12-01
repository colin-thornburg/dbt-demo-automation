import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { 
  Home, 
  FileText, 
  FolderOpen, 
  GitBranch, 
  Cloud, 
  CheckCircle,
  Menu,
  X,
  RotateCw
} from 'lucide-react'
import { useSession } from '../contexts/SessionContext'
import { getStatus } from '../api/client'
import { useEffect } from 'react'

const navigation = [
  { name: 'Setup', href: '/setup', icon: Home },
  { name: 'Review', href: '/review', icon: FileText },
  { name: 'Files', href: '/files', icon: FolderOpen },
  { name: 'Repository', href: '/repository', icon: GitBranch },
  { name: 'Provision', href: '/provisioning', icon: Cloud },
  { name: 'Success', href: '/success', icon: CheckCircle },
]

export default function Layout({ children }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { sessionId, resetSession } = useSession()
  const [status, setStatus] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  const handleResetSession = async () => {
    if (confirm('Are you sure you want to reset the session? This will clear all progress.')) {
      await resetSession()
      navigate('/setup')
    }
  }

  useEffect(() => {
    const fetchStatus = async () => {
      if (sessionId) {
        try {
          const s = await getStatus(sessionId)
          setStatus(s)
        } catch (error) {
          // If session is not found (404), it will be handled by SessionContext
          // Just silently fail here to avoid console spam
          if (error.response?.status !== 404) {
            console.error('Failed to fetch status:', error)
          }
        }
      }
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000) // Reduced from 2s to 5s to be less aggressive
    return () => clearInterval(interval)
  }, [sessionId])
  
  // Keyboard shortcut: Ctrl/Cmd + Shift + R to reset session
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'R') {
        e.preventDefault()
        handleResetSession()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleResetSession])

  const progress = status ? (
    (status.demo_inputs + status.ai_config + status.github_config + status.dbt_config) / 4 * 100
  ) : 0

  return (
    <div className="min-h-screen bg-dbt-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-dbt-gray-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-4 border-b border-dbt-gray-200">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-dbt-orange rounded flex items-center justify-center">
                  <span className="text-white font-bold text-sm">dbt</span>
                </div>
                <span className="font-semibold text-dbt-gray-900">Demo Automation</span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden text-dbt-gray-500 hover:text-dbt-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <button
              onClick={handleResetSession}
              className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm text-dbt-gray-700 bg-dbt-gray-100 hover:bg-dbt-gray-200 rounded-lg transition-colors"
              title="Reset session and start over"
            >
              <RotateCw className="w-4 h-4" />
              <span>Reset Session</span>
            </button>
            {sessionId && (
              <div className="mt-2 text-xs text-dbt-gray-500 font-mono truncate" title={sessionId}>
                Session: {sessionId.substring(0, 8)}...
              </div>
            )}
          </div>

          {/* Progress */}
          {status && (
            <div className="p-4 border-b border-dbt-gray-200">
              <div className="text-sm font-medium text-dbt-gray-700 mb-2">Configuration Progress</div>
              <div className="w-full bg-dbt-gray-200 rounded-full h-2 mb-3">
                <div
                  className="bg-dbt-green h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="space-y-1 text-xs text-dbt-gray-600">
                <div className="flex items-center">
                  {status.demo_inputs ? (
                    <span className="text-dbt-green mr-2">✓</span>
                  ) : (
                    <span className="text-dbt-gray-400 mr-2">○</span>
                  )}
                  Demo Inputs
                </div>
                <div className="flex items-center">
                  {status.ai_config ? (
                    <span className="text-dbt-green mr-2">✓</span>
                  ) : (
                    <span className="text-dbt-gray-400 mr-2">○</span>
                  )}
                  AI Provider
                </div>
                <div className="flex items-center">
                  {status.github_config ? (
                    <span className="text-dbt-green mr-2">✓</span>
                  ) : (
                    <span className="text-dbt-gray-400 mr-2">○</span>
                  )}
                  GitHub
                </div>
                <div className="flex items-center">
                  {status.dbt_config ? (
                    <span className="text-dbt-green mr-2">✓</span>
                  ) : (
                    <span className="text-dbt-gray-400 mr-2">○</span>
                  )}
                  dbt Cloud
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-dbt-orange/10 text-dbt-orange'
                      : 'text-dbt-gray-700 hover:bg-dbt-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <header className="lg:hidden bg-white border-b border-dbt-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-dbt-orange rounded flex items-center justify-center">
              <span className="text-white font-bold text-sm">dbt</span>
            </div>
            <span className="font-semibold text-dbt-gray-900">Demo Automation</span>
          </div>
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-dbt-gray-500 hover:text-dbt-gray-700"
          >
            <Menu className="w-6 h-6" />
          </button>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-8 max-w-7xl mx-auto">
          {children}
        </main>
      </div>
    </div>
  )
}

