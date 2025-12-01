import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import { getRepository, provisionDbtCloud } from '../api/client'
import { Loader2, ExternalLink, CheckCircle2, GitBranch } from 'lucide-react'
import ErrorAlert from '../components/ErrorAlert'

export default function RepositoryPage() {
  const { sessionId } = useSession()
  const navigate = useNavigate()
  const [repoInfo, setRepoInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [provisioning, setProvisioning] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchRepository = async () => {
      try {
        const data = await getRepository(sessionId)
        setRepoInfo(data)
      } catch (error) {
        console.error('Failed to fetch repository:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchRepository()
  }, [sessionId])

  const handleProvision = async () => {
    setProvisioning(true)
    setError(null)
    try {
      await provisionDbtCloud(sessionId)
      navigate('/provisioning')
    } catch (error) {
      console.error('Failed to provision:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred'
      setError(errorMessage)
    } finally {
      setProvisioning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-dbt-orange" />
      </div>
    )
  }

  if (!repoInfo) {
    return (
      <div className="card">
        <p className="text-dbt-gray-600">No repository found. Please go back and create a repository.</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dbt-gray-900 mb-2">Repository Created</h1>
        <p className="text-dbt-gray-600">Your GitHub repository has been successfully created</p>
      </div>

      <div className="card mb-6">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-dbt-green/10 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-dbt-green" />
            </div>
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-dbt-gray-900 mb-2">Repository Ready</h2>
            <p className="text-dbt-gray-600 mb-4">
              Your dbt project has been pushed to GitHub successfully.
            </p>
            {repoInfo.url && (
              <a
                href={repoInfo.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-2 text-dbt-orange hover:text-orange-600 font-medium"
              >
                <span>View on GitHub</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>
      </div>

      {repoInfo.repositories && (
        <div className="card mb-6">
          <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Mesh Demo Repositories</h2>
          <div className="space-y-3">
            {Object.entries(repoInfo.repositories).map(([key, repo]) => (
              <div key={key} className="p-3 bg-dbt-gray-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <GitBranch className="w-4 h-4 text-dbt-gray-500" />
                    <span className="font-medium text-dbt-gray-900">{key}</span>
                  </div>
                  {repo.url && (
                    <a
                      href={repo.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-dbt-orange hover:text-orange-600 flex items-center space-x-1"
                    >
                      <span>View</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Provision dbt Cloud */}
      <div className="card">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Next Step: Provision dbt Cloud</h2>
        <p className="text-dbt-gray-600 mb-4">
          Automatically provision a dbt Cloud project with Terraform. This will create:
        </p>
        <ul className="list-disc list-inside text-dbt-gray-700 mb-6 space-y-2">
          <li>dbt Cloud project</li>
          <li>Snowflake connection</li>
          <li>Development & Production environments</li>
          <li>Scheduled jobs and CI configuration</li>
        </ul>
        
        {error && <ErrorAlert error={error} context="provisioning" />}
        
        <button
          onClick={handleProvision}
          disabled={provisioning}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {provisioning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Provisioning...</span>
            </>
          ) : (
            <>
              <span>Provision dbt Cloud</span>
              <span>→</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}

