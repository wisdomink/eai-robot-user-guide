import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

export default function ChatPanelSdkBridge() {
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    return () => {
      window.FFRobotChat?.destroy()
    }
  }, [])

  useEffect(() => {
    if (location.pathname === '/admin') {
      window.FFRobotChat?.destroy()
      return
    }

    const handleEntityNavigate = ({ url }: FFRobotChatEntityNavigatePayload) => {
      navigate(`${url.pathname}${url.search}`)

      if (url.hash) {
        setTimeout(() => {
          document.getElementById(url.hash.slice(1))
            ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 300)
      }
    }

    window.FFRobotChat?.init({
      onEntityNavigate: handleEntityNavigate,
    }).catch((error: unknown) => {
      console.error('[ChatPanelSdkBridge] Failed to initialize SDK:', error)
    })
  }, [location.pathname, navigate])

  return null
}
