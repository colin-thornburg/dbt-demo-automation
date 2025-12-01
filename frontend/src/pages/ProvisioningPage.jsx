import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import { getProvisioningResult, getProvisioningProgress } from '../api/client'
import { Loader2, CheckCircle2, ExternalLink, Cloud, CheckCircle, Clock, AlertCircle } from 'lucide-react'

export default function ProvisioningPage() {
  const { sessionId } = useSession()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [progress, setProgress] = useState(null)

  useEffect(() => {
    // Poll for progress updates
    const fetchProgress = async () => {
      try {
        const data = await getProvisioningProgress(sessionId)
        setProgress(data)
      } catch (error) {
        console.error('Failed to fetch provisioning progress:', error)
      }
    }

    // Fetch progress immediately and then every 2 seconds
    fetchProgress()
    const progressInterval = setInterval(fetchProgress, 2000)

    // Also check for final result
    const fetchResult = async () => {
      try {
        const data = await getProvisioningResult(sessionId)
        setResult(data)
        setLoading(false)
        clearInterval(progressInterval)
      } catch (error) {
        // Keep polling if not found yet
        if (error.response?.status === 404) {
          // Still provisioning, keep checking
        } else {
          console.error('Failed to fetch provisioning result:', error)
        }
      }
    }

    // Check for result every 2 seconds
    const resultInterval = setInterval(fetchResult, 2000)
    fetchResult() // Initial check

    return () => {
      clearInterval(progressInterval)
      clearInterval(resultInterval)
    }
  }, [sessionId])

  if (loading && !result) {
    const totalSteps = 12 // Total expected steps in provisioning
    const completedSteps = progress?.steps?.filter(s => s.status === 'completed').length || 0
    const progressPercent = Math.round((completedSteps / totalSteps) * 100)
    
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="relative inline-flex items-center justify-center mb-4">
              <div className="absolute inset-0 flex items-center justify-center">
                <Loader2 className="w-16 h-16 animate-spin text-dbt-orange opacity-20" />
              </div>
              <div className="relative w-16 h-16 flex items-center justify-center bg-dbt-orange/10 rounded-full">
                <Cloud className="w-8 h-8 text-dbt-orange" />
              </div>
            </div>
            <h2 className="text-2xl font-semibold text-dbt-gray-900 mb-2">Provisioning dbt Cloud</h2>
            <p className="text-dbt-gray-600 mb-4">
              Setting up your project infrastructure. This typically takes 2-3 minutes.
            </p>
            
            {/* Progress Bar */}
            {progress && completedSteps > 0 && (
              <div className="max-w-md mx-auto">
                <div className="flex items-center justify-between text-sm text-dbt-gray-600 mb-2">
                  <span>{completedSteps} of {totalSteps} steps complete</span>
                  <span className="font-semibold text-dbt-orange">{progressPercent}%</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-dbt-orange to-orange-500 transition-all duration-500 ease-out"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Current Step Highlight */}
          {progress && progress.current_step && (
            <div className="mb-6 p-4 bg-gradient-to-r from-dbt-orange/10 to-orange-50 border-l-4 border-dbt-orange rounded-r-lg">
              <div className="flex items-center space-x-3">
                <Loader2 className="w-5 h-5 animate-spin text-dbt-orange flex-shrink-0" />
                <div>
                  <div className="text-xs font-medium text-dbt-orange uppercase tracking-wide mb-1">
                    Currently Running
                  </div>
                  <div className="text-sm font-semibold text-dbt-gray-900">
                    {progress.current_step}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Detailed Progress Steps */}
          {progress && (progress.steps?.length > 0 || progress.current_step) && (
            <div>
              <h3 className="text-sm font-semibold text-dbt-gray-900 mb-4 flex items-center">
                <span className="flex-shrink-0 w-6 h-6 bg-dbt-gray-900 text-white rounded-full flex items-center justify-center text-xs mr-2">
                  {completedSteps}
                </span>
                Provisioning Steps
              </h3>
              <div className="space-y-2">
                {progress.steps && progress.steps.map((step, idx) => (
                  <div 
                    key={idx} 
                    className={`flex items-start space-x-3 p-3 rounded-lg transition-all duration-300 ${
                      step.status === 'completed' ? 'bg-green-50' :
                      step.status === 'error' ? 'bg-red-50' :
                      'bg-gray-50'
                    }`}
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      {step.status === 'completed' ? (
                        <div className="w-6 h-6 bg-dbt-green rounded-full flex items-center justify-center">
                          <CheckCircle className="w-4 h-4 text-white" />
                        </div>
                      ) : step.status === 'error' ? (
                        <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                          <AlertCircle className="w-4 h-4 text-white" />
                        </div>
                      ) : (
                        <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center">
                          <Clock className="w-4 h-4 text-gray-600" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm font-medium ${
                        step.status === 'completed' ? 'text-dbt-green' :
                        step.status === 'error' ? 'text-red-600' :
                        'text-gray-600'
                      }`}>
                        {step.name}
                      </div>
                      {step.status === 'completed' && (
                        <div className="text-xs text-gray-500 mt-0.5">
                          Completed successfully
                        </div>
                      )}
                    </div>
                    {step.status === 'completed' && (
                      <div className="flex-shrink-0 text-xs text-dbt-green font-medium">
                        ✓
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Info Box */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex space-x-3">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-medium text-blue-900 mb-1">What's happening?</h4>
                <p className="text-xs text-blue-700">
                  We're using Terraform to provision your dbt Cloud project, connect your GitHub repository, 
                  configure Snowflake connections, set up development and production environments, and create 
                  a production job. Your project will be ready to use as soon as this completes.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="card">
        <p className="text-dbt-gray-600">Provisioning in progress. Please wait...</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dbt-gray-900 mb-2">
          {result.message || 'Provisioning Complete'}
        </h1>
        <p className="text-dbt-gray-600">
          {result.instructions || 'Your dbt Cloud project has been successfully provisioned'}
        </p>
      </div>

      {/* Automatic Provisioning Success */}
      {result.project_url && (
        <>
          <div className="card mb-6">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-dbt-green/10 rounded-lg flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-dbt-green" />
                </div>
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-dbt-gray-900 mb-2">dbt Cloud Ready</h2>
                <p className="text-dbt-gray-600 mb-4">
                  Your dbt Cloud project is ready to use.
                </p>
                {result.project_url && (
                  <a
                    href={result.project_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-2 text-dbt-orange hover:text-orange-600 font-medium"
                  >
                    <Cloud className="w-4 h-4" />
                    <span>Open in dbt Cloud</span>
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
          </div>

          <div className="card mb-6">
            <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Project Details</h2>
            <div className="space-y-3">
              {result.project_id && (
                <div className="flex justify-between">
                  <span className="text-dbt-gray-600">Project ID:</span>
                  <span className="font-mono text-sm text-dbt-gray-900">{result.project_id}</span>
                </div>
              )}
              {result.project_name && (
                <div className="flex justify-between">
                  <span className="text-dbt-gray-600">Project Name:</span>
                  <span className="text-sm text-dbt-gray-900">{result.project_name}</span>
                </div>
              )}
              {result.dev_environment_id && (
                <div className="flex justify-between">
                  <span className="text-dbt-gray-600">Development Environment:</span>
                  <span className="font-mono text-sm text-dbt-gray-900">{result.dev_environment_id}</span>
                </div>
              )}
              {result.prod_environment_id && (
                <div className="flex justify-between">
                  <span className="text-dbt-gray-600">Production Environment:</span>
                  <span className="font-mono text-sm text-dbt-gray-900">{result.prod_environment_id}</span>
                </div>
              )}
              {result.production_job_id && (
                <div className="flex justify-between">
                  <span className="text-dbt-gray-600">Production Job ID:</span>
                  <span className="font-mono text-sm text-dbt-gray-900">{result.production_job_id}</span>
                </div>
              )}
              {result.job_run_id && (
                <div className="flex justify-between items-center">
                  <span className="text-dbt-gray-600">Initial Job Run:</span>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-sm text-dbt-gray-900">{result.job_run_id}</span>
                    {result.job_run_url && (
                      <a
                        href={result.job_run_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-dbt-orange hover:text-orange-600"
                        title="View run in dbt Cloud"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>
              )}
              {result.repository_id && (
                <div className="flex justify-between">
                  <span className="text-dbt-gray-600">Repository ID:</span>
                  <span className="font-mono text-sm text-dbt-gray-900">{result.repository_id}</span>
                </div>
              )}
              {result.connection_id && (
                <div className="flex justify-between">
                  <span className="text-dbt-gray-600">Snowflake Connection ID:</span>
                  <span className="font-mono text-sm text-dbt-gray-900">{result.connection_id}</span>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      <div className="flex justify-end">
        <button onClick={() => navigate('/success')} className="btn-primary">
          View Success Page →
        </button>
      </div>
    </div>
  )
}

