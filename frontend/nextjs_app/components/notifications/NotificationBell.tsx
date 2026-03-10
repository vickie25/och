'use client'

import { useState, useEffect } from 'react'
import { Bell } from 'lucide-react'
import { apiGateway } from '@/services/apiGateway'
import { NotificationPanel } from './NotificationPanel'

export function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0)
  const [showPanel, setShowPanel] = useState(false)

  useEffect(() => {
    fetchUnreadCount()
    const interval = setInterval(fetchUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchUnreadCount = async () => {
    try {
      const data = await apiGateway.get<{ count: number }>('/notifications/unread_count')
      setUnreadCount(data.count)
    } catch (error) {
      console.error('Failed to fetch unread count:', error)
    }
  }

  return (
    <>
      <button
        onClick={() => setShowPanel(!showPanel)}
        className="relative p-2 text-och-steel hover:text-white transition-colors"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 bg-och-orange text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>
      
      {showPanel && (
        <NotificationPanel 
          onClose={() => setShowPanel(false)} 
          onCountChange={setUnreadCount}
        />
      )}
    </>
  )
}
