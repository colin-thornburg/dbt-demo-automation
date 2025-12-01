import { useNavigate } from 'react-router-dom'
import { CheckCircle2, Sparkles } from 'lucide-react'

export default function SuccessPage() {
  const navigate = useNavigate()

  return (
    <div className="max-w-3xl mx-auto text-center">
      <div className="mb-8">
        <div className="w-20 h-20 bg-dbt-green/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 className="w-12 h-12 text-dbt-green" />
        </div>
        <h1 className="text-4xl font-bold text-dbt-gray-900 mb-4">Demo Ready!</h1>
        <p className="text-xl text-dbt-gray-600">
          Your dbt Cloud demo has been successfully set up and is ready to use.
        </p>
      </div>

      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-dbt-gray-900 mb-4">What's Next?</h2>
        <div className="text-left space-y-4 text-dbt-gray-700">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-dbt-orange/10 rounded-full flex items-center justify-center">
              <span className="text-dbt-orange font-semibold text-sm">1</span>
            </div>
            <div>
              <div className="font-medium">Open the dbt Cloud IDE</div>
              <div className="text-sm text-dbt-gray-600 mt-1">
                Navigate to your project and open the IDE to explore the generated models
              </div>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-dbt-orange/10 rounded-full flex items-center justify-center">
              <span className="text-dbt-orange font-semibold text-sm">2</span>
            </div>
            <div>
              <div className="font-medium">Run the project</div>
              <div className="text-sm text-dbt-gray-600 mt-1">
                Execute <code className="bg-dbt-gray-100 px-1 py-0.5 rounded">dbt deps && dbt seed && dbt run && dbt test</code> in the IDE
              </div>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-dbt-orange/10 rounded-full flex items-center justify-center">
              <span className="text-dbt-orange font-semibold text-sm">3</span>
            </div>
            <div>
              <div className="font-medium">Explore the lineage</div>
              <div className="text-sm text-dbt-gray-600 mt-1">
                Use the lineage graph to visualize data flow and dependencies
              </div>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-dbt-orange/10 rounded-full flex items-center justify-center">
              <span className="text-dbt-orange font-semibold text-sm">4</span>
            </div>
            <div>
              <div className="font-medium">Start your presentation</div>
              <div className="text-sm text-dbt-gray-600 mt-1">
                Use the generated talking points and metrics to guide your demo
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-center space-x-3">
        <button onClick={() => navigate('/setup')} className="btn-secondary">
          Create Another Demo
        </button>
      </div>
    </div>
  )
}

