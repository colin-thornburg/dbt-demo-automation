import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import {
  setDemoInputs,
  setAIConfig,
  setGitHubConfig,
  setDbtConfig,
  getStatus,
  getMissingFields,
  generateScenario,
  getPromptPreview,
} from '../api/client'
import { Loader2, AlertCircle, Bot, Sparkles, TerminalSquare } from 'lucide-react'
import ErrorAlert from '../components/ErrorAlert'

export default function SetupPage() {
  const { sessionId, config } = useSession()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState(null)
  const [missingFields, setMissingFields] = useState([])
  const [promptPreview, setPromptPreview] = useState(null)
  const [promptPreviewLoading, setPromptPreviewLoading] = useState(false)

  // Demo inputs
  const [companyName, setCompanyName] = useState('Jaffle Shop')
  const [industry, setIndustry] = useState('Candy Retailer')
  const [discoveryNotes, setDiscoveryNotes] = useState('')
  const [painPoints, setPainPoints] = useState('')
  const [includeSemanticLayer, setIncludeSemanticLayer] = useState(false)
  const [meshDemo, setMeshDemo] = useState(false)
  const [numDownstream, setNumDownstream] = useState(1)

  // AI config
  const [aiProvider, setAiProvider] = useState('claude')
  const [aiApiKey, setAiApiKey] = useState('')
  const [aiModel, setAiModel] = useState('')

  // GitHub config
  const [githubUsername, setGithubUsername] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [templateRepo, setTemplateRepo] = useState('')

  // dbt Cloud config
  const [dbtAccountId, setDbtAccountId] = useState('')
  const [dbtServiceToken, setDbtServiceToken] = useState('')
  const [dbtWarehouse, setDbtWarehouse] = useState('snowflake')
  const [dbtProjectId, setDbtProjectId] = useState('')
  const [dbtHost, setDbtHost] = useState('cloud.getdbt.com')
  const [snowflakeUser, setSnowflakeUser] = useState('')
  const [snowflakePassword, setSnowflakePassword] = useState('')

  // Load config from backend and auto-populate form fields
  useEffect(() => {
    if (config) {
      // Set AI provider defaults
      if (config.default_ai_provider) {
        setAiProvider(config.default_ai_provider)
      }
      
      // Set AI model based on provider
      const defaultModel = config.default_ai_provider === 'claude'
        ? config.default_claude_model || 'claude-opus-4-6'
        : config.default_openai_model || 'gpt-4o-mini'
      setAiModel(defaultModel)
      
      // Set GitHub defaults
      if (config.default_github_org) {
        setGithubUsername(config.default_github_org)
      }
      if (config.dbt_template_repo_url) {
        setTemplateRepo(config.dbt_template_repo_url)
      } else {
        setTemplateRepo('https://github.com/colin-thornburg/demo-automation-template.git')
      }
      
      // Set dbt Cloud defaults
      if (config.default_dbt_account_id) {
        setDbtAccountId(config.default_dbt_account_id)
      }
      if (config.default_warehouse_type) {
        setDbtWarehouse(config.default_warehouse_type)
      }
      if (config.default_dbt_cloud_project_id) {
        setDbtProjectId(config.default_dbt_cloud_project_id)
      }
      if (config.default_dbt_cloud_host) {
        setDbtHost(config.default_dbt_cloud_host)
      }
      if (config.snowflake_user) {
        setSnowflakeUser(config.snowflake_user)
      }
    }
  }, [config])
  
  // Update model when provider changes
  useEffect(() => {
    if (config && aiProvider) {
      const newModel = aiProvider === 'claude'
        ? config.default_claude_model || 'claude-opus-4-6'
        : config.default_openai_model || 'gpt-4o-mini'
      setAiModel(newModel)
    }
  }, [aiProvider, config])

  // Fetch missing fields from backend (considers .env defaults)
  useEffect(() => {
    const fetchMissingFields = async () => {
      if (sessionId) {
        try {
          // Save current form state to backend first
          await setDemoInputs(sessionId, {
            company_name: companyName,
            industry,
            discovery_notes: discoveryNotes,
            pain_points: painPoints,
            include_semantic_layer: includeSemanticLayer,
            mesh_demo: meshDemo,
            num_downstream_projects: numDownstream,
          })

          await setAIConfig(sessionId, {
            provider: aiProvider,
            api_key: aiApiKey,
            model: aiModel,
          })

          await setGitHubConfig(sessionId, {
            username: githubUsername,
            token: githubToken,
            template_repo_url: templateRepo,
          })

          await setDbtConfig(sessionId, {
            account_id: dbtAccountId,
            service_token: dbtServiceToken,
            warehouse_type: dbtWarehouse,
            project_id: dbtProjectId,
            host: dbtHost,
            snowflake_user: snowflakeUser,
            snowflake_password: snowflakePassword,
          })

          // Then get missing fields (backend checks .env)
          const result = await getMissingFields(sessionId)
          setMissingFields(result.missing_fields || [])
        } catch (error) {
          console.error('Failed to fetch missing fields:', error)
        }
      }
    }

    // Debounce the check
    const timeoutId = setTimeout(fetchMissingFields, 500)
    return () => clearTimeout(timeoutId)
  }, [
    sessionId,
    companyName,
    industry,
    aiProvider,
    aiApiKey,
    githubUsername,
    githubToken,
    dbtAccountId,
    dbtServiceToken,
    snowflakeUser,
    snowflakePassword,
  ])

  useEffect(() => {
    const fetchStatus = async () => {
      if (sessionId) {
        try {
          const s = await getStatus(sessionId)
          setStatus(s)
        } catch (error) {
          console.error('Failed to fetch status:', error)
        }
      }
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 2000)
    return () => clearInterval(interval)
  }, [sessionId])

  // Prompt preview for transparency
  useEffect(() => {
    const fetchPromptPreview = async () => {
      if (!sessionId || !companyName || !industry) {
        setPromptPreview(null)
        return
      }
      try {
        setPromptPreviewLoading(true)
        const preview = await getPromptPreview(sessionId, {
          company_name: companyName,
          industry,
          discovery_notes: discoveryNotes,
          pain_points: painPoints,
          include_semantic_layer: includeSemanticLayer,
        })
        setPromptPreview(preview)
      } catch (error) {
        console.error('Failed to fetch prompt preview:', error)
      } finally {
        setPromptPreviewLoading(false)
      }
    }

    const timeoutId = setTimeout(fetchPromptPreview, 350)
    return () => clearTimeout(timeoutId)
  }, [
    sessionId,
    companyName,
    industry,
    discoveryNotes,
    painPoints,
    includeSemanticLayer,
  ])

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)

    try {
      // Save all configs
      await setDemoInputs(sessionId, {
        company_name: companyName,
        industry,
        discovery_notes: discoveryNotes,
        pain_points: painPoints,
        include_semantic_layer: includeSemanticLayer,
        mesh_demo: meshDemo,
        num_downstream_projects: numDownstream,
      })

      await setAIConfig(sessionId, {
        provider: aiProvider,
        api_key: aiApiKey,
        model: aiModel,
      })

      await setGitHubConfig(sessionId, {
        username: githubUsername,
        token: githubToken,
        template_repo_url: templateRepo,
      })

      await setDbtConfig(sessionId, {
        account_id: dbtAccountId,
        service_token: dbtServiceToken,
        warehouse_type: dbtWarehouse,
        project_id: dbtProjectId,
        host: dbtHost,
            snowflake_user: snowflakeUser,
            snowflake_password: snowflakePassword,
      })

      // Generate scenario
      await generateScenario(sessionId)
      navigate('/review')
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to generate scenario')
    } finally {
      setLoading(false)
    }
  }

  const canGenerate = missingFields.length === 0

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dbt-gray-900 mb-2">Demo Setup</h1>
        <p className="text-dbt-gray-600">Configure your prospect demo and API settings</p>
      </div>

      {/* Missing Fields Alert */}
      {!canGenerate && missingFields.length > 0 && (
        <div className="mb-6 p-4 bg-yellow-50 border-2 border-yellow-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <div className="font-semibold text-yellow-900 mb-2">
                Missing Required Fields
              </div>
              <div className="text-sm text-yellow-800 mb-2">
                Please fill in the following required fields before generating your demo. Fields available in your .env file are automatically used and won't appear here.
              </div>
              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800">
                {missingFields.map((field, idx) => (
                  <li key={idx} className="font-medium">{field}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {error && <ErrorAlert error={error} context="ai" />}

      {/* Demo Inputs */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">1. Demo Context</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Company Name *
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="input-field"
              placeholder="e.g., Acme Corporation"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Industry / Vertical *
            </label>
            <input
              type="text"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="input-field"
              placeholder="e.g., E-commerce, Healthcare"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Discovery Call Notes (Optional)
            </label>
            <textarea
              value={discoveryNotes}
              onChange={(e) => setDiscoveryNotes(e.target.value)}
              className="input-field"
              rows={4}
              placeholder="Key insights from your discovery call..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Technical Pain Points (Optional)
            </label>
            <textarea
              value={painPoints}
              onChange={(e) => setPainPoints(e.target.value)}
              className="input-field"
              rows={4}
              placeholder="Specific pain points with current data tooling..."
            />
          </div>

          <div className="pt-4 border-t border-dbt-gray-200">
            <div className="rounded-xl border border-slate-700 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-4 shadow-lg">
              <div className="flex items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-2">
                  <div className="inline-flex items-center gap-1.5 rounded-full bg-violet-500/20 px-2.5 py-1 text-[11px] font-semibold text-violet-200">
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Prompt Preview
                  </div>
                  <div className="inline-flex items-center gap-1.5 rounded-full bg-cyan-500/20 px-2.5 py-1 text-[11px] font-semibold text-cyan-200">
                    <Bot className="w-3.5 h-3.5" />
                    Live
                  </div>
                </div>
                {promptPreviewLoading && (
                  <div className="text-xs text-slate-300">Syncing...</div>
                )}
              </div>

              <p className="text-xs text-slate-300 mb-3">
                This is the exact prompt payload generated from your discovery notes and pain points.
              </p>

              <label className="block text-[11px] uppercase tracking-wide font-semibold text-slate-300 mb-1.5">
                User Prompt
              </label>
              <div className="relative">
                <TerminalSquare className="w-4 h-4 text-slate-500 absolute top-2.5 left-2.5" />
                <textarea
                  readOnly
                  value={promptPreview?.user_prompt || 'Enter company and industry to preview prompt...'}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 text-slate-100 font-mono text-xs leading-relaxed pl-8 pr-3 py-2.5 focus:outline-none"
                  rows={10}
                />
              </div>

              <details className="mt-3">
                <summary className="text-xs font-medium text-slate-300 cursor-pointer hover:text-white transition-colors">
                  Show system prompt
                </summary>
                <textarea
                  readOnly
                  value={promptPreview?.system_prompt || 'System prompt will appear here...'}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 text-slate-100 font-mono text-xs leading-relaxed px-3 py-2.5 mt-2 focus:outline-none"
                  rows={8}
                />
              </details>
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="semantic-layer"
              checked={includeSemanticLayer}
              onChange={(e) => setIncludeSemanticLayer(e.target.checked)}
              className="w-4 h-4 text-dbt-orange border-dbt-gray-300 rounded focus:ring-dbt-orange"
            />
            <label htmlFor="semantic-layer" className="ml-2 text-sm text-dbt-gray-700">
              Include Semantic Layer in Demo
            </label>
          </div>

          <div className="pt-4 border-t border-dbt-gray-200">
            <div className="flex items-center mb-3">
              <input
                type="checkbox"
                id="mesh-demo"
                checked={meshDemo}
                onChange={(e) => setMeshDemo(e.target.checked)}
                className="w-4 h-4 text-dbt-orange border-dbt-gray-300 rounded focus:ring-dbt-orange"
              />
              <label htmlFor="mesh-demo" className="ml-2 text-sm font-medium text-dbt-gray-700">
                Enable dbt Mesh Demo (Cross-Project References)
              </label>
            </div>
            {meshDemo && (
              <div className="ml-6">
                <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
                  Number of Downstream Projects
                </label>
                <input
                  type="number"
                  min="1"
                  max="3"
                  value={numDownstream}
                  onChange={(e) => setNumDownstream(parseInt(e.target.value))}
                  className="input-field w-32"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Configuration */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">2. AI Provider Configuration</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              AI Provider *
            </label>
            <select
              value={aiProvider}
              onChange={(e) => {
                setAiProvider(e.target.value)
                if (e.target.value === 'claude') {
                  setAiModel(config?.default_claude_model || 'claude-opus-4-6')
                } else {
                  setAiModel(config?.default_openai_model || 'gpt-4o-mini')
                }
              }}
              className="input-field"
            >
              <option value="claude">Claude (Anthropic)</option>
              <option value="openai">OpenAI</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              API Key *
            </label>
            <input
              type="password"
              value={aiApiKey}
              onChange={(e) => setAiApiKey(e.target.value)}
              className="input-field"
              placeholder="sk-... or dbt_cloud_token_..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Model *
            </label>
            <select
              value={aiModel}
              onChange={(e) => setAiModel(e.target.value)}
              className="input-field"
            >
              {aiProvider === 'claude' ? (
                <>
                  <option value="claude-opus-4-6">claude-opus-4-6 — Latest, highest capability (recommended)</option>
                  <option value="claude-opus-4-5-20251101">claude-opus-4-5 (Nov 2025) — High capability</option>
                  <option value="claude-sonnet-4-5-20250929">claude-sonnet-4.5 (Sep 2025) — Balanced speed &amp; quality</option>
                </>
              ) : (
                <>
                  <option value="gpt-4o-mini">gpt-4o-mini — Fast, inexpensive, reliable default</option>
                  <option value="gpt-4.1">gpt-4.1 — Strong quality for longer generation tasks</option>
                  <option value="o3-mini">o3-mini — Reasoning-focused with good speed/cost</option>
                  <option value="gpt-5.2-thinking">gpt-5.2-thinking — Deepest reasoning</option>
                  <option value="gpt-5.2-codex">gpt-5.2-codex — Optimized for code generation</option>
                  <option value="gpt-5.2-instant">gpt-5.2-instant — Fastest, lowest cost</option>
                </>
              )}
            </select>
          </div>
        </div>
      </div>

      {/* GitHub Configuration */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">3. GitHub Configuration</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              GitHub Owner (Username or Organization) *
            </label>
            <input
              type="text"
              value={githubUsername}
              onChange={(e) => setGithubUsername(e.target.value)}
              className="input-field"
              placeholder="e.g. dbt-labs or your-username"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Personal Access Token *
            </label>
            <input
              type="password"
              value={githubToken}
              onChange={(e) => setGithubToken(e.target.value)}
              className="input-field"
              placeholder="ghp_..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Template Repository URL
            </label>
            <input
              type="text"
              value={templateRepo}
              onChange={(e) => setTemplateRepo(e.target.value)}
              className="input-field"
            />
          </div>
        </div>
      </div>

      {/* dbt Cloud Configuration */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">4. dbt Cloud Configuration</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              dbt Cloud Account ID *
            </label>
            <input
              type="text"
              value={dbtAccountId}
              onChange={(e) => setDbtAccountId(e.target.value)}
              className="input-field"
              placeholder="12345"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Service Token *
            </label>
            <input
              type="password"
              value={dbtServiceToken}
              onChange={(e) => setDbtServiceToken(e.target.value)}
              className="input-field"
              placeholder="dbt_cloud_token_..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              Target Warehouse
            </label>
            <select
              value={dbtWarehouse}
              onChange={(e) => setDbtWarehouse(e.target.value)}
              className="input-field"
            >
              <option value="snowflake">Snowflake</option>
              <option value="bigquery">BigQuery</option>
              <option value="databricks">Databricks</option>
              <option value="redshift">Redshift</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              dbt Cloud Project ID (Optional)
            </label>
            <input
              type="text"
              value={dbtProjectId}
              onChange={(e) => setDbtProjectId(e.target.value)}
              className="input-field"
              placeholder="Optional"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
              dbt Cloud Host
            </label>
            <input
              type="text"
              value={dbtHost}
              onChange={(e) => setDbtHost(e.target.value)}
              className="input-field"
              placeholder="cloud.getdbt.com"
            />
          </div>

          <div className="pt-2 border-t border-dbt-gray-200">
            <div className="text-sm font-semibold text-dbt-gray-900 mb-3">
              Snowflake Credentials (for dbt Cloud dev env)
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
                  Snowflake Username
                </label>
                <input
                  type="text"
                  value={snowflakeUser}
                  onChange={(e) => setSnowflakeUser(e.target.value)}
                  className="input-field"
                  placeholder="user@company.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dbt-gray-700 mb-1">
                  Snowflake Password
                </label>
                <input
                  type="password"
                  value={snowflakePassword}
                  onChange={(e) => setSnowflakePassword(e.target.value)}
                  className="input-field"
                  placeholder="••••••••"
                />
              </div>
            </div>
            <div className="text-xs text-dbt-gray-500 mt-2">
              Leave blank to use the defaults from your `.env`.
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end space-x-3">
        <button
          onClick={handleGenerate}
          disabled={!canGenerate || loading}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Generating...</span>
            </>
          ) : (
            <>
              <span>Generate Demo</span>
              <span>→</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}

