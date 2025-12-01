import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import { getFiles, createRepository } from '../api/client'
import { Loader2, FileText, Folder, CheckCircle2 } from 'lucide-react'
import ErrorAlert from '../components/ErrorAlert'

export default function FilesPage() {
  const { sessionId } = useSession()
  const navigate = useNavigate()
  const [files, setFiles] = useState(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [repoName, setRepoName] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const data = await getFiles(sessionId)
        setFiles(data)
        // Generate default repo name from company name if available
        if (!repoName && data.company_name) {
          const defaultName = data.company_name.toLowerCase().replace(/[^a-z0-9]/g, '-') + '-dbt-demo'
          setRepoName(defaultName)
        }
      } catch (error) {
        console.error('Failed to fetch files:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchFiles()
  }, [sessionId])

  const handleCreateRepository = async () => {
    setCreating(true)
    setError(null)
    try {
      await createRepository(sessionId, repoName)
      navigate('/repository')
    } catch (err) {
      console.error('Failed to create repository:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create repository'
      setError(errorMessage)
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-dbt-orange" />
      </div>
    )
  }

  if (!files) {
    return (
      <div className="card">
        <p className="text-dbt-gray-600">No files found. Please go back and generate files.</p>
      </div>
    )
  }

  const summary = {
    seeds: files.seeds ? Object.keys(files.seeds).length : 0,
    models: files.models ? Object.keys(files.models).length : 0,
    schemas: files.schemas ? Object.keys(files.schemas).length : 0,
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dbt-gray-900 mb-2">Generated Files</h1>
        <p className="text-dbt-gray-600">Review the generated dbt project files</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card text-center">
          <div className="text-2xl font-bold text-dbt-gray-900">{summary.seeds}</div>
          <div className="text-sm text-dbt-gray-600 mt-1">Seed Files</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-dbt-gray-900">{summary.models}</div>
          <div className="text-sm text-dbt-gray-600 mt-1">Model Files</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-dbt-gray-900">{summary.schemas}</div>
          <div className="text-sm text-dbt-gray-600 mt-1">Schema Files</div>
        </div>
      </div>

      {/* Files List */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">File Structure</h2>
        <div className="space-y-4">
          {files.seeds && Object.keys(files.seeds).length > 0 && (
            <div>
              <h3 className="font-medium text-dbt-gray-900 mb-2 flex items-center">
                <Folder className="w-4 h-4 mr-2" />
                Seeds
              </h3>
              <div className="pl-6 space-y-1">
                {Object.entries(files.seeds).map(([filename, content], idx) => (
                  <div key={idx} className="text-sm text-dbt-gray-600 flex items-center">
                    <FileText className="w-3 h-3 mr-2" />
                    seeds/{filename}
                  </div>
                ))}
              </div>
            </div>
          )}

          {files.models && Object.keys(files.models).length > 0 && (
            <div>
              <h3 className="font-medium text-dbt-gray-900 mb-2 flex items-center">
                <Folder className="w-4 h-4 mr-2" />
                Models
              </h3>
              <div className="pl-6 space-y-1">
                {Object.entries(files.models).map(([filepath, content], idx) => (
                  <div key={idx} className="text-sm text-dbt-gray-600 flex items-center">
                    <FileText className="w-3 h-3 mr-2" />
                    {filepath}
                  </div>
                ))}
              </div>
            </div>
          )}

          {files.schemas && Object.keys(files.schemas).length > 0 && (
            <div>
              <h3 className="font-medium text-dbt-gray-900 mb-2 flex items-center">
                <Folder className="w-4 h-4 mr-2" />
                Schemas
              </h3>
              <div className="pl-6 space-y-1">
                {Object.entries(files.schemas).map(([filepath, content], idx) => (
                  <div key={idx} className="text-sm text-dbt-gray-600 flex items-center">
                    <FileText className="w-3 h-3 mr-2" />
                    {filepath}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && <ErrorAlert error={error} context="github" />}

      {/* Create Repository */}
      <div className="card">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Create GitHub Repository</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Repository Name
            </label>
            <input
              type="text"
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              className="input-field"
              placeholder="my-dbt-demo"
            />
          </div>
          <button
            onClick={handleCreateRepository}
            disabled={!repoName.trim() || creating}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {creating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Creating...</span>
              </>
            ) : (
              <>
                <span>Create Repository</span>
                <span>→</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

