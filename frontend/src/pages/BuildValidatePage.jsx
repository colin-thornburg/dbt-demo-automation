import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import {
  getBuildCliStatus,
  startBuildValidation,
  getBuildValidation,
} from '../api/client'
import {
  Loader2,
  CheckCircle,
  AlertCircle,
  Terminal,
  Wrench,
  Zap,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  SkipForward,
  Play,
  FileCode2,
  FolderOpen,
  GitBranch,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'

/* ------------------------------------------------------------------ */
/*  Log viewer — scrollable terminal-style output                      */
/* ------------------------------------------------------------------ */
function LogViewer({ logs, title }) {
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  if (!logs) return null

  return (
    <div className="mt-3">
      {title && (
        <div className="text-xs font-semibold text-dbt-gray-500 uppercase tracking-wide mb-1">
          {title}
        </div>
      )}
      <pre className="bg-dbt-gray-900 text-green-400 text-xs leading-relaxed p-4 rounded-lg overflow-auto max-h-80 whitespace-pre-wrap font-mono">
        {logs}
        <span ref={endRef} />
      </pre>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main page component                                                */
/* ------------------------------------------------------------------ */
export default function BuildValidatePage() {
  const { sessionId } = useSession()
  const navigate = useNavigate()

  const [cliStatus, setCliStatus] = useState(null)
  const [cliChecking, setCliChecking] = useState(true)
  const [building, setBuilding] = useState(false)
  const [result, setResult] = useState(null)
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState(null)
  const [expandedAttempt, setExpandedAttempt] = useState(null)
  const [showLogs, setShowLogs] = useState({})

  // Check CLI availability on mount
  useEffect(() => {
    const check = async () => {
      try {
        const data = await getBuildCliStatus(sessionId)
        setCliStatus(data)
      } catch (err) {
        console.error('CLI status check failed:', err)
        setCliStatus({ cli_available: false })
      } finally {
        setCliChecking(false)
      }
    }
    check()
  }, [sessionId])

  // Poll progress while building
  useEffect(() => {
    if (!building) return
    const interval = setInterval(async () => {
      try {
        const data = await getBuildValidation(sessionId)
        setProgress(data)
        if (
          data.status === 'completed' ||
          data.status === 'failed' ||
          data.status === 'error'
        ) {
          if (data.result) setResult(data.result)
          setBuilding(false)
        }
      } catch {
        // keep polling
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [building, sessionId])

  const handleStartBuild = async () => {
    setBuilding(true)
    setError(null)
    setResult(null)
    setExpandedAttempt(null)
    setShowLogs({})
    setProgress({
      status: 'in_progress',
      current_step: 'Starting build validation…',
      steps: [],
    })

    try {
      const data = await startBuildValidation(sessionId)
      setResult(data)
      // Auto-expand first attempt
      if (data.attempts?.length) setExpandedAttempt(data.attempts[0].attempt_number)
      setBuilding(false)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Build validation failed')
      setBuilding(false)
    }
  }

  const toggleLogs = (num) =>
    setShowLogs((prev) => ({ ...prev, [num]: !prev[num] }))

  // ---- CLI not available ----
  if (!cliChecking && cliStatus && !cliStatus.cli_available) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Terminal className="w-8 h-8 text-amber-600" />
            </div>
            <h2 className="text-2xl font-semibold text-dbt-gray-900 mb-2">
              dbt Cloud CLI Not Found
            </h2>
            <p className="text-dbt-gray-600 max-w-lg mx-auto">
              The dbt Cloud CLI is required to run local build validation with AI-powered
              auto-fixing. Install it to unlock this feature.
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-5 mb-6">
            <h3 className="text-sm font-semibold text-dbt-gray-900 mb-3">Install Options</h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-dbt-gray-500 font-medium mb-1">macOS (Homebrew)</div>
                <code className="block bg-dbt-gray-900 text-green-400 text-sm px-4 py-2 rounded">
                  brew tap dbt-labs/dbt-cli && brew install dbt
                </code>
              </div>
              <div>
                <div className="text-xs text-dbt-gray-500 font-medium mb-1">pip (all platforms)</div>
                <code className="block bg-dbt-gray-900 text-green-400 text-sm px-4 py-2 rounded">
                  pip install dbt --no-cache-dir
                </code>
              </div>
            </div>
            <a
              href="https://docs.getdbt.com/docs/cloud/cloud-cli-installation"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-1 text-sm text-dbt-orange hover:text-orange-600 mt-3"
            >
              <span>Full installation guide</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="flex justify-between">
            <button onClick={() => navigate('/provisioning')} className="btn-secondary">
              ← Back
            </button>
            <button onClick={() => navigate('/success')} className="btn-primary">
              Skip to Success →
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ---- Loading CLI check ----
  if (cliChecking) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card text-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-dbt-orange mx-auto mb-3" />
          <p className="text-dbt-gray-600">Checking dbt Cloud CLI availability…</p>
        </div>
      </div>
    )
  }

  // ---- Main view ----
  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-dbt-gray-900 mb-2">Build & Validate</h1>
        <p className="text-dbt-gray-600">
          Run{' '}
          <code className="bg-dbt-gray-100 px-1.5 py-0.5 rounded text-sm">dbt build</code>{' '}
          locally via the Cloud CLI. If errors are found, AI will automatically diagnose, fix,
          and push corrections to your GitHub repo.
        </p>
      </div>

      {/* CLI Info + Start */}
      {cliStatus?.cli_available && !building && !result && (
        <div className="card mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-dbt-green/10 rounded-lg flex items-center justify-center">
                <Terminal className="w-5 h-5 text-dbt-green" />
              </div>
              <div>
                <div className="font-medium text-dbt-gray-900">dbt Cloud CLI Ready</div>
                <div className="text-sm text-dbt-gray-500 space-x-2">
                  <span>
                    Path:{' '}
                    <code className="text-xs bg-gray-100 px-1 rounded">{cliStatus.cli_path}</code>
                  </span>
                  {cliStatus.cli_info?.type && (
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      cliStatus.cli_info.type === 'cloud_cli'
                        ? 'bg-green-100 text-dbt-green'
                        : cliStatus.cli_info.type === 'dbt_core'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {cliStatus.cli_info.type === 'cloud_cli'
                        ? 'Cloud CLI'
                        : cliStatus.cli_info.type === 'dbt_core'
                        ? 'dbt Core (not Cloud CLI)'
                        : cliStatus.cli_info.type}
                    </span>
                  )}
                  {cliStatus.cli_info?.version && (
                    <span className="text-xs text-dbt-gray-400">v{cliStatus.cli_info.version}</span>
                  )}
                </div>
              </div>
            </div>
            <button onClick={handleStartBuild} className="btn-primary flex items-center space-x-2">
              <Play className="w-4 h-4" />
              <span>Run Build Validation</span>
            </button>
          </div>

          {/* Warning if dbt Core detected */}
          {cliStatus.cli_info?.type === 'dbt_core' && (
            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-amber-800">
                <strong>Warning:</strong> You have dbt Core installed, not the dbt Cloud CLI.
                Local builds will not run against dbt Cloud infrastructure and may produce
                different results than your production job. Consider installing the{' '}
                <a
                  href="https://docs.getdbt.com/docs/cloud/cloud-cli-installation"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline font-medium"
                >
                  dbt Cloud CLI
                </a>
                .
              </div>
            </div>
          )}

          {/* Feature explanation */}
          <div className="mt-5 pt-5 border-t border-gray-100">
            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-start space-x-2">
                <Zap className="w-4 h-4 text-dbt-orange mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-sm font-medium text-dbt-gray-900">Cloud CLI Build</div>
                  <div className="text-xs text-dbt-gray-500">
                    Runs against dbt Cloud infrastructure with secure credentials
                  </div>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <Wrench className="w-4 h-4 text-dbt-orange mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-sm font-medium text-dbt-gray-900">AI Auto-Fix</div>
                  <div className="text-xs text-dbt-gray-500">
                    Powered by dbt agent skills for best-practice fixes
                  </div>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <GitBranch className="w-4 h-4 text-dbt-orange mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-sm font-medium text-dbt-gray-900">Auto Push</div>
                  <div className="text-xs text-dbt-gray-500">
                    Fixes are committed and pushed to your GitHub repo automatically
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Building / Progress */}
      {building && progress && (
        <div className="card mb-6">
          <div className="text-center mb-6">
            <Loader2 className="w-12 h-12 animate-spin text-dbt-orange mx-auto mb-3" />
            <h2 className="text-xl font-semibold text-dbt-gray-900 mb-1">
              Building & Validating
            </h2>
            <p className="text-dbt-gray-600 text-sm">
              Running dbt build with AI-powered auto-fixing. This may take a few minutes.
            </p>
          </div>

          {/* Current step */}
          {progress.current_step && (
            <div className="p-4 bg-gradient-to-r from-dbt-orange/10 to-orange-50 border-l-4 border-dbt-orange rounded-r-lg mb-4">
              <div className="flex items-center space-x-3">
                <Loader2 className="w-4 h-4 animate-spin text-dbt-orange flex-shrink-0" />
                <span className="text-sm font-medium text-dbt-gray-900">
                  {progress.current_step}
                </span>
              </div>
            </div>
          )}

          {/* Completed steps */}
          {progress.steps?.length > 0 && (
            <div className="space-y-2">
              {progress.steps.map((step, idx) => (
                <div
                  key={idx}
                  className={`flex items-center space-x-3 p-2 rounded-lg text-sm ${
                    step.status === 'completed'
                      ? 'bg-green-50 text-dbt-green'
                      : step.status === 'error'
                      ? 'bg-red-50 text-red-600'
                      : 'bg-gray-50 text-gray-600'
                  }`}
                >
                  {step.status === 'completed' ? (
                    <CheckCircle className="w-4 h-4 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  )}
                  <span>{step.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card mb-6 border-red-200 bg-red-50">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-medium text-red-800">Build Validation Error</h3>
              <pre className="text-sm text-red-700 mt-2 whitespace-pre-wrap overflow-x-auto max-h-64">
                {error}
              </pre>
            </div>
          </div>
          <div className="mt-4 flex space-x-3">
            <button onClick={handleStartBuild} className="btn-secondary text-sm flex items-center space-x-2">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
            <button onClick={() => navigate('/success')} className="btn-secondary text-sm">
              Skip to Success
            </button>
          </div>
        </div>
      )}

      {/* ============ RESULT ============ */}
      {result && !building && (
        <div className="space-y-6">
          {/* Success / Failure banner */}
          <div className={`card ${result.success ? 'border-green-200' : 'border-amber-200'}`}>
            <div className="flex items-start space-x-4">
              <div
                className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  result.success ? 'bg-dbt-green/10' : 'bg-amber-100'
                }`}
              >
                {result.success ? (
                  <CheckCircle className="w-6 h-6 text-dbt-green" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-amber-600" />
                )}
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-dbt-gray-900">
                  {result.success ? 'Build Passed!' : 'Build Issues Found'}
                </h2>
                <p className="text-dbt-gray-600 text-sm mt-1">{result.message}</p>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-sm text-dbt-gray-500">
                  <span>{result.total_attempts} attempt(s)</span>
                  <span>•</span>
                  <span>{result.elapsed_seconds?.toFixed(1)}s elapsed</span>
                  {result.files_modified?.length > 0 && (
                    <>
                      <span>•</span>
                      <span className="text-dbt-orange font-medium">
                        {result.files_modified.length} file(s) auto-fixed
                      </span>
                    </>
                  )}
                  <span>•</span>
                  {result.pushed_to_github ? (
                    <span className="flex items-center space-x-1 text-dbt-green font-medium">
                      <GitBranch className="w-3.5 h-3.5" />
                      <span>Pushed to GitHub</span>
                    </span>
                  ) : result.files_modified?.length > 0 ? (
                    <span className="flex items-center space-x-1 text-red-500 font-medium">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>NOT pushed to GitHub</span>
                    </span>
                  ) : (
                    <span className="text-dbt-gray-400">No push needed</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Metadata: project dir + CLI info */}
          <div className="card bg-gray-50">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {result.project_dir && (
                <div className="flex items-start space-x-2">
                  <FolderOpen className="w-4 h-4 text-dbt-gray-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="text-xs font-semibold text-dbt-gray-500 uppercase tracking-wide">
                      Local Project
                    </div>
                    <code className="text-xs text-dbt-gray-700 break-all">{result.project_dir}</code>
                  </div>
                </div>
              )}
              {result.cli_info && (
                <div className="flex items-start space-x-2">
                  <Terminal className="w-4 h-4 text-dbt-gray-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="text-xs font-semibold text-dbt-gray-500 uppercase tracking-wide">
                      CLI Type
                    </div>
                    <span className="text-xs text-dbt-gray-700">
                      {result.cli_info.type === 'cloud_cli'
                        ? 'dbt Cloud CLI'
                        : result.cli_info.type === 'dbt_core'
                        ? 'dbt Core'
                        : result.cli_info.type}
                      {result.cli_info.version ? ` v${result.cli_info.version}` : ''}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Attempt details */}
          {result.attempts?.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-dbt-gray-900 mb-4">Build Attempts</h3>
              <div className="space-y-3">
                {result.attempts.map((attempt) => {
                  const isExpanded = expandedAttempt === attempt.attempt_number
                  const logsVisible = showLogs[attempt.attempt_number]

                  return (
                    <div key={attempt.attempt_number} className="border border-gray-200 rounded-lg overflow-hidden">
                      {/* Attempt header */}
                      <button
                        onClick={() =>
                          setExpandedAttempt(isExpanded ? null : attempt.attempt_number)
                        }
                        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center space-x-3">
                          {attempt.status === 'success' ? (
                            <CheckCircle className="w-5 h-5 text-dbt-green" />
                          ) : attempt.status === 'fixed' ? (
                            <Wrench className="w-5 h-5 text-dbt-orange" />
                          ) : (
                            <AlertCircle className="w-5 h-5 text-red-500" />
                          )}
                          <span className="font-medium text-dbt-gray-900">
                            Attempt {attempt.attempt_number}
                          </span>
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              attempt.status === 'success'
                                ? 'bg-green-100 text-dbt-green'
                                : attempt.status === 'fixed'
                                ? 'bg-orange-100 text-dbt-orange'
                                : 'bg-red-100 text-red-600'
                            }`}
                          >
                            {attempt.status}
                          </span>
                        </div>
                        <div className="flex items-center space-x-3 text-sm text-dbt-gray-500">
                          {attempt.error_count > 0 && (
                            <span>{attempt.error_count} error(s)</span>
                          )}
                          {attempt.fixes_count > 0 && (
                            <span className="text-dbt-orange">{attempt.fixes_count} fix(es)</span>
                          )}
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </div>
                      </button>

                      {/* Expanded content */}
                      {isExpanded && (
                        <div className="border-t border-gray-200 bg-gray-50 p-4 space-y-4">
                          {/* Parsed errors for this attempt */}
                          {attempt.errors?.length > 0 && (
                            <div>
                              <h4 className="text-sm font-semibold text-red-700 mb-2">
                                Errors Detected ({attempt.errors.length})
                              </h4>
                              <div className="space-y-2">
                                {attempt.errors.map((err, idx) => (
                                  <div
                                    key={idx}
                                    className="p-2 bg-red-50 border border-red-100 rounded text-xs"
                                  >
                                    <div className="flex items-center space-x-2 mb-0.5">
                                      <span className="font-semibold text-red-600 uppercase">
                                        {err.category}
                                      </span>
                                      {err.model_name && (
                                        <code className="text-red-800 bg-red-100 px-1 rounded">
                                          {err.model_name}
                                        </code>
                                      )}
                                    </div>
                                    <p className="text-red-700 whitespace-pre-wrap">{err.message}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* AI fixes applied */}
                          {attempt.fixes?.length > 0 && (
                            <div>
                              <h4 className="text-sm font-semibold text-dbt-orange mb-2">
                                AI Fixes Applied ({attempt.fixes.length})
                              </h4>
                              <div className="space-y-2">
                                {attempt.fixes.map((fix, idx) => (
                                  <div
                                    key={idx}
                                    className="flex items-start space-x-2 text-sm bg-orange-50 border border-orange-100 p-2 rounded"
                                  >
                                    <Wrench className="w-3.5 h-3.5 text-dbt-orange mt-0.5 flex-shrink-0" />
                                    <div>
                                      <code className="text-xs bg-white px-1 py-0.5 rounded border">
                                        {fix.file}
                                      </code>
                                      <span className="text-dbt-gray-600 ml-2 text-xs">
                                        {fix.explanation}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Full dbt output (collapsible) */}
                          {attempt.logs && (
                            <div>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  toggleLogs(attempt.attempt_number)
                                }}
                                className="flex items-center space-x-2 text-sm font-medium text-dbt-gray-700 hover:text-dbt-gray-900 transition-colors"
                              >
                                <Terminal className="w-4 h-4" />
                                <span>
                                  {logsVisible ? 'Hide' : 'Show'} Full dbt Output
                                </span>
                                {logsVisible ? (
                                  <ChevronDown className="w-3 h-3" />
                                ) : (
                                  <ChevronRight className="w-3 h-3" />
                                )}
                              </button>
                              {logsVisible && (
                                <LogViewer logs={attempt.logs} />
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Remaining errors (final) */}
          {!result.success && result.final_errors?.length > 0 && (
            <div className="card border-red-200">
              <h3 className="text-lg font-semibold text-red-800 mb-3">
                Remaining Errors ({result.final_errors.length})
              </h3>
              <div className="space-y-2">
                {result.final_errors.map((err, idx) => (
                  <div key={idx} className="p-3 bg-red-50 rounded-lg text-sm">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-xs font-medium text-red-600 uppercase bg-red-100 px-1.5 py-0.5 rounded">
                        {err.category}
                      </span>
                      {err.model_name && (
                        <code className="text-xs text-red-800">{err.model_name}</code>
                      )}
                      {err.file_path && (
                        <code className="text-xs text-red-600">{err.file_path}</code>
                      )}
                    </div>
                    <p className="text-red-700 text-xs whitespace-pre-wrap">{err.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between">
            <div className="flex space-x-3">
              <button
                onClick={handleStartBuild}
                className="btn-secondary flex items-center space-x-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>{result.success ? 'Run Again' : 'Retry Build'}</span>
              </button>
            </div>
            <button onClick={() => navigate('/success')} className="btn-primary">
              {result.success ? 'Continue to Success →' : 'Skip to Success →'}
            </button>
          </div>
        </div>
      )}

      {/* Initial state — no result yet, not building */}
      {!building && !result && !error && cliStatus?.cli_available && (
        <div className="flex justify-between mt-6">
          <button onClick={() => navigate('/provisioning')} className="btn-secondary">
            ← Back
          </button>
          <button
            onClick={() => navigate('/success')}
            className="btn-secondary flex items-center space-x-2"
          >
            <SkipForward className="w-4 h-4" />
            <span>Skip Validation</span>
          </button>
        </div>
      )}
    </div>
  )
}
