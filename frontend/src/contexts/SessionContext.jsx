import { createContext, useContext, useState, useEffect } from 'react'
import { createSession, getConfig } from '../api/client'

const SessionContext = createContext()

export const useSession = () => {
  const context = useContext(SessionContext)
  if (!context) {
    throw new Error('useSession must be used within SessionProvider')
  }
  return context
}

export const SessionProvider = ({ children }) => {
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('sessionId')
  })
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initializeSession = async () => {
      try {
        let id = sessionId
        
        // Try to get config for existing session
        if (id) {
          try {
            const sessionConfig = await getConfig(id)
            setConfig(sessionConfig)
            return // Success with existing session
          } catch (error) {
            // Session doesn't exist (404), need to create new one
            console.warn('Stored session invalid, creating new session')
            localStorage.removeItem('sessionId')
            id = null
          }
        }
        
        // Create new session if no valid session exists
        if (!id) {
          id = await createSession()
          setSessionId(id)
          localStorage.setItem('sessionId', id)
          const sessionConfig = await getConfig(id)
          setConfig(sessionConfig)
        }
      } catch (error) {
        console.error('Failed to initialize session:', error)
      } finally {
        setLoading(false)
      }
    }

    initializeSession()
  }, [])

  const resetSession = async () => {
    const id = await createSession()
    setSessionId(id)
    localStorage.setItem('sessionId', id)
    const sessionConfig = await getConfig(id)
    setConfig(sessionConfig)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-dbt-gray-500">Loading...</div>
      </div>
    )
  }

  return (
    <SessionContext.Provider value={{ sessionId, config, resetSession }}>
      {children}
    </SessionContext.Provider>
  )
}

