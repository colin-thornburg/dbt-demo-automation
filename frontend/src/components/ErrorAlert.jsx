import { AlertCircle, ExternalLink } from 'lucide-react'

/**
 * Enhanced error alert component that provides helpful troubleshooting information
 * based on the type of error encountered.
 */
export default function ErrorAlert({ error, context = 'general' }) {
  if (!error) return null

  const errorString = typeof error === 'string' ? error : error.message || 'Unknown error'
  
  // Parse common error patterns and provide helpful guidance
  const getErrorDetails = (errorMsg, ctx) => {
    const msg = errorMsg.toLowerCase()
    
    // GitHub Authentication Errors
    if (msg.includes('bad credentials') || msg.includes('github') && msg.includes('401')) {
      return {
        title: 'GitHub Authentication Failed',
        description: errorMsg,
        cause: 'Your GitHub Personal Access Token (PAT) is invalid, expired, or has insufficient permissions.',
        solutions: [
          {
            text: 'Verify your token has the required "repo" scope for creating repositories',
            important: true
          },
          {
            text: 'Check if your token has expired and generate a new one if needed',
            link: 'https://github.com/settings/tokens'
          },
          {
            text: 'Ensure you\'re using a classic Personal Access Token (not fine-grained)',
            info: 'Fine-grained tokens may have additional restrictions'
          },
          {
            text: 'If using SSO, authorize the token for your organization',
            link: 'https://docs.github.com/en/authentication/authenticating-with-saml-single-sign-on/authorizing-a-personal-access-token-for-use-with-saml-single-sign-on'
          }
        ],
        nextSteps: [
          'Go back to Setup',
          'Update your GitHub Personal Access Token',
          'Try again'
        ]
      }
    }
    
    // AI Provider Authentication Errors
    if (msg.includes('authentication_error') || msg.includes('invalid x-api-key') || msg.includes('invalid api key')) {
      const provider = msg.includes('anthropic') || msg.includes('claude') ? 'Claude (Anthropic)' : 'OpenAI'
      return {
        title: `${provider} Authentication Failed`,
        description: errorMsg,
        cause: `Your ${provider} API key is invalid or missing.`,
        solutions: [
          {
            text: `Get a valid API key from ${provider === 'Claude (Anthropic)' ? 'Anthropic Console' : 'OpenAI Platform'}`,
            link: provider === 'Claude (Anthropic)' ? 'https://console.anthropic.com/settings/keys' : 'https://platform.openai.com/api-keys',
            important: true
          },
          {
            text: 'Ensure the API key starts with the correct prefix',
            info: provider === 'Claude (Anthropic)' ? 'Should start with "sk-ant-"' : 'Should start with "sk-"'
          },
          {
            text: 'Check that your account has sufficient credits/quota',
          }
        ],
        nextSteps: [
          'Go back to Setup',
          `Update your ${provider} API Key`,
          'Try again'
        ]
      }
    }
    
    // dbt Cloud Authentication Errors
    if (msg.includes('dbt cloud') && (msg.includes('401') || msg.includes('unauthorized') || msg.includes('authentication'))) {
      return {
        title: 'dbt Cloud Authentication Failed',
        description: errorMsg,
        cause: 'Your dbt Cloud Service Token is invalid or has insufficient permissions.',
        solutions: [
          {
            text: 'Generate a new Service Token in dbt Cloud with Account Admin permissions',
            link: 'https://cloud.getdbt.com',
            important: true
          },
          {
            text: 'Verify the Account ID matches your dbt Cloud account',
            info: 'Found in dbt Cloud URL: cloud.getdbt.com/deploy/[account_id]'
          },
          {
            text: 'Ensure the token hasn\'t expired',
          }
        ],
        nextSteps: [
          'Go to dbt Cloud → Account Settings → Service Tokens',
          'Create a new token with appropriate permissions',
          'Update the token in Setup and try again'
        ]
      }
    }
    
    // Terraform/Provisioning Errors
    if (msg.includes('terraform') || msg.includes('provision')) {
      return {
        title: 'Provisioning Failed',
        description: errorMsg,
        cause: 'There was an issue with the Terraform provisioning process.',
        solutions: [
          {
            text: 'Check that all required environment variables are set in your .env file',
            important: true
          },
          {
            text: 'Verify Snowflake credentials are correct',
          },
          {
            text: 'Ensure GitHub App Installation ID is valid',
          },
          {
            text: 'Check the backend logs for detailed Terraform output',
          }
        ],
        nextSteps: [
          'Review the error message above for specific details',
          'Check your .env file configuration',
          'Try the provisioning step again'
        ]
      }
    }
    
    // Network/Connection Errors
    if (msg.includes('network') || msg.includes('connection') || msg.includes('timeout')) {
      return {
        title: 'Connection Error',
        description: errorMsg,
        cause: 'Unable to connect to the required service.',
        solutions: [
          {
            text: 'Check your internet connection',
          },
          {
            text: 'Verify the API endpoint is accessible',
          },
          {
            text: 'Check if there are any firewall or proxy issues',
          }
        ],
        nextSteps: [
          'Wait a moment and try again',
          'If the issue persists, check service status pages'
        ]
      }
    }
    
    // Generic error
    return {
      title: 'Error Occurred',
      description: errorMsg,
      cause: 'An unexpected error occurred.',
      solutions: [
        {
          text: 'Review the error message for details',
        },
        {
          text: 'Check that all configuration values are correct',
        },
        {
          text: 'Verify all API keys and tokens are valid',
        }
      ],
      nextSteps: [
        'Try the operation again',
        'If the error persists, check the backend logs'
      ]
    }
  }

  const details = getErrorDetails(errorString, context)

  return (
    <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-start space-x-3 mb-4">
        <div className="flex-shrink-0">
          <AlertCircle className="w-6 h-6 text-red-600" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-red-900">{details.title}</h3>
        </div>
      </div>

      {/* Error Message */}
      <div className="mb-4 p-3 bg-red-100 border border-red-200 rounded-lg">
        <p className="text-sm font-mono text-red-800 break-words">{details.description}</p>
      </div>

      {/* Cause */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-red-900 mb-2">Why this happened:</h4>
        <p className="text-sm text-red-800">{details.cause}</p>
      </div>

      {/* Solutions */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-red-900 mb-2">How to fix it:</h4>
        <ul className="space-y-2">
          {details.solutions.map((solution, idx) => (
            <li key={idx} className="flex items-start space-x-2 text-sm">
              <span className="text-red-600 mt-0.5">
                {solution.important ? '⚠️' : '•'}
              </span>
              <div className="flex-1">
                <span className="text-red-800">{solution.text}</span>
                {solution.info && (
                  <div className="text-xs text-red-700 mt-1 italic">
                    {solution.info}
                  </div>
                )}
                {solution.link && (
                  <a
                    href={solution.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1 text-xs text-red-700 hover:text-red-900 underline mt-1"
                  >
                    <span>Open link</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Next Steps */}
      <div className="border-t border-red-200 pt-4">
        <h4 className="text-sm font-semibold text-red-900 mb-2">Next steps:</h4>
        <ol className="space-y-1">
          {details.nextSteps.map((step, idx) => (
            <li key={idx} className="flex items-start space-x-2 text-sm text-red-800">
              <span className="font-semibold">{idx + 1}.</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}




