import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import { getScenario, regenerateScenario, generateFiles } from '../api/client'
import { Loader2, ChevronDown, ChevronUp, CheckCircle2 } from 'lucide-react'

export default function ReviewPage() {
  const { sessionId } = useSession()
  const navigate = useNavigate()
  const [scenario, setScenario] = useState(null)
  const [loading, setLoading] = useState(true)
  const [regenerating, setRegenerating] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [expandedSections, setExpandedSections] = useState({
    sources: true,
    staging: true,
    intermediate: true,
    marts: true,
  })

  useEffect(() => {
    const fetchScenario = async () => {
      try {
        const data = await getScenario(sessionId)
        setScenario(data)
      } catch (error) {
        console.error('Failed to fetch scenario:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchScenario()
  }, [sessionId])

  const handleRegenerate = async () => {
    if (!feedback.trim()) return
    setRegenerating(true)
    try {
      const newScenario = await regenerateScenario(sessionId, feedback)
      setScenario(newScenario)
      setFeedback('')
    } catch (error) {
      console.error('Failed to regenerate:', error)
    } finally {
      setRegenerating(false)
    }
  }

  const handleConfirm = async () => {
    setGenerating(true)
    try {
      await generateFiles(sessionId)
      navigate('/files')
    } catch (error) {
      console.error('Failed to generate files:', error)
    } finally {
      setGenerating(false)
    }
  }

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-dbt-orange" />
      </div>
    )
  }

  if (!scenario) {
    return (
      <div className="card">
        <p className="text-dbt-gray-600">No scenario found. Please go back to Setup and generate a scenario.</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dbt-gray-900 mb-2">Demo Scenario Review</h1>
        <p className="text-dbt-gray-600">Review the AI-generated demo scenario and proceed or regenerate</p>
      </div>

      <div className="mb-6 p-4 bg-dbt-gray-50 rounded-lg">
        <div className="text-sm text-dbt-gray-700">
          <span className="font-medium">Company:</span> {scenario.company_name} |{' '}
          <span className="font-medium">Industry:</span> {scenario.industry}
        </div>
      </div>

      {/* Demo Overview */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Demo Overview</h2>
        <p className="text-dbt-gray-700 whitespace-pre-wrap">{scenario.demo_overview}</p>
      </div>

      {/* Business Context */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Business Context</h2>
        <p className="text-dbt-gray-700 whitespace-pre-wrap">{scenario.business_context}</p>
      </div>

      {/* Data Architecture */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Data Architecture</h2>

        {/* Source Tables */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection('sources')}
            className="flex items-center justify-between w-full text-left font-medium text-dbt-gray-900 mb-2"
          >
            <span>Source Tables</span>
            {expandedSections.sources ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
          {expandedSections.sources && (
            <div className="space-y-3 pl-4 border-l-2 border-dbt-gray-200">
              {scenario.data_sources?.map((source, idx) => (
                <div key={idx} className="py-2">
                  <div className="font-mono text-sm font-medium text-dbt-gray-900">{source.name}</div>
                  <div className="text-sm text-dbt-gray-600 mt-1">{source.description}</div>
                  <div className="text-xs text-dbt-gray-500 mt-1">
                    Columns: {source.columns?.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Staging Models */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection('staging')}
            className="flex items-center justify-between w-full text-left font-medium text-dbt-gray-900 mb-2"
          >
            <span>Staging Models (stg_)</span>
            {expandedSections.staging ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
          {expandedSections.staging && (
            <div className="space-y-3 pl-4 border-l-2 border-dbt-gray-200">
              {scenario.staging_models?.map((model, idx) => (
                <div key={idx} className="py-2">
                  <div className="font-mono text-sm font-medium text-dbt-gray-900">{model.name}</div>
                  <div className="text-sm text-dbt-gray-600 mt-1">{model.description}</div>
                  <div className="text-xs text-dbt-gray-500 mt-1">Source: {model.source_table}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Intermediate Models */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection('intermediate')}
            className="flex items-center justify-between w-full text-left font-medium text-dbt-gray-900 mb-2"
          >
            <span>Intermediate Models (int_)</span>
            {expandedSections.intermediate ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
          {expandedSections.intermediate && (
            <div className="space-y-3 pl-4 border-l-2 border-dbt-gray-200">
              {scenario.intermediate_models?.map((model, idx) => (
                <div key={idx} className="py-2">
                  <div className="font-mono text-sm font-medium text-dbt-gray-900">{model.name}</div>
                  <div className="text-sm text-dbt-gray-600 mt-1">{model.description}</div>
                  <div className="text-xs text-dbt-gray-500 mt-1">
                    Depends on: {model.depends_on?.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Marts Models */}
        <div>
          <button
            onClick={() => toggleSection('marts')}
            className="flex items-center justify-between w-full text-left font-medium text-dbt-gray-900 mb-2"
          >
            <span>Marts Models (final analytics tables)</span>
            {expandedSections.marts ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
          {expandedSections.marts && (
            <div className="space-y-3 pl-4 border-l-2 border-dbt-gray-200">
              {scenario.marts_models?.map((model, idx) => (
                <div key={idx} className="py-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-sm font-medium text-dbt-gray-900">{model.name}</span>
                    {model.is_incremental && (
                      <span className="badge badge-purple">INCREMENTAL</span>
                    )}
                  </div>
                  <div className="text-sm text-dbt-gray-600 mt-1">{model.description}</div>
                  <div className="text-xs text-dbt-gray-500 mt-1">
                    Depends on: {model.depends_on?.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Metrics and Talking Points */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <div className="card">
          <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Key Metrics</h2>
          <div className="space-y-4">
            {scenario.key_metrics?.map((metric, idx) => (
              <div key={idx}>
                <div className="font-medium text-dbt-gray-900">{metric.name}</div>
                <div className="text-sm text-dbt-gray-600 mt-1">{metric.description}</div>
                <div className="text-xs font-mono text-dbt-gray-500 mt-1">
                  {metric.calculation}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Demo Talking Points</h2>
          <ol className="list-decimal list-inside space-y-2 text-dbt-gray-700">
            {scenario.talking_points?.map((point, idx) => (
              <li key={idx}>{point}</li>
            ))}
          </ol>
        </div>
      </div>

      {/* Regeneration */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">Want to Adjust This Scenario?</h2>
        <div className="space-y-4">
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            className="input-field"
            rows={4}
            placeholder="E.g., 'Add more focus on data quality', 'Include customer churn metrics'..."
          />
          <button
            onClick={handleRegenerate}
            disabled={!feedback.trim() || regenerating}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {regenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Regenerating...</span>
              </>
            ) : (
              <span>Regenerate</span>
            )}
          </button>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-dbt-gray-600">
          Scenario looks good? Click Confirm to proceed with file generation.
        </div>
        <div className="flex space-x-3">
          <button onClick={() => navigate('/setup')} className="btn-secondary">
            ← Back to Setup
          </button>
          <button
            onClick={handleConfirm}
            disabled={generating}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <span>Confirm Scenario</span>
                <span>→</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

