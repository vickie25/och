'use client'

import { useState, useEffect } from 'react'
import { X, Check, CheckCheck } from 'lucide-react'
import { apiGateway } from '@/services/apiGateway'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useRouter } from 'next/navigation'

interface Notification {
  id: string
  notification_type: string
  title: string
  message: string
  priority: string
  action_url?: string
  action_label?: string
  is_read: boolean
  created_at: string
}

interface NotificationPanelProps {
  onClose: () => void
  onCountChange: (count: number) => void
}

export function NotificationPanel({ onClose, onCountChange }: NotificationPanelProps) {
  const router = useRouter()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchNotifications()
  }, [])

  const fetchNotifications = async () => {
    try {
      const data = await apiGateway.get<Notification[]>('/notifications/')
      setNotifications(data)
      const unreadCount = data.filter(n => !n.is_read).length
      onCountChange(unreadCount)
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = async (id: string) => {
    try {
      await apiGateway.post(`/notifications/${id}/mark_read/`)
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
      onCountChange(notifications.filter(n => !n.is_read && n.id !== id).length)
    } catch (error) {
      console.error('Failed to mark as read:', error)
    }
  }

  const markAllAsRead = async () => {
    try {
      await apiGateway.post('/notifications/mark_all_read/')
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
      onCountChange(0)
    } catch (error) {
      console.error('Failed to mark all as read:', error)
    }
  }

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id)
    }
    if (notification.action_url) {
      router.push(notification.action_url)
      onClose()
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-l-4 border-och-orange'
      case 'medium': return 'border-l-4 border-och-defender'
      case 'low': return 'border-l-4 border-och-steel'
      default: return ''
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-end p-4">
      <Card className="w-full max-w-md bg-och-midnight border-och-steel/20 max-h-[80vh] flex flex-col">
        <div className="p-4 border-b border-och-steel/20 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">Notifications</h2>
          <div className="flex items-center gap-2">
            {notifications.some(n => !n.is_read) && (
              <Button variant="ghost" size="sm" onClick={markAllAsRead}>
                <CheckCheck className="w-4 h-4 mr-1" />
                Mark all read
              </Button>
            )}
            <button onClick={onClose} className="text-och-steel hover:text-white">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading ? (
            <div className="text-center py-8 text-och-steel">Loading...</div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-8 text-och-steel">No notifications</div>
          ) : (
            notifications.map(notification => (
              <div
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  notification.is_read 
                    ? 'bg-och-midnight/50 hover:bg-och-midnight/70' 
                    : 'bg-och-defender/10 hover:bg-och-defender/20'
                } ${getPriorityColor(notification.priority)}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <h3 className={`text-sm font-semibold ${notification.is_read ? 'text-och-steel' : 'text-white'}`}>
                      {notification.title}
                    </h3>
                    <p className="text-xs text-och-steel mt-1">{notification.message}</p>
                    {notification.action_label && (
                      <span className="text-xs text-och-mint mt-2 inline-block">
                        {notification.action_label} →
                      </span>
                    )}
                  </div>
                  {!notification.is_read && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        markAsRead(notification.id)
                      }}
                      className="text-och-steel hover:text-white"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <div className="text-xs text-och-steel/50 mt-2">
                  {new Date(notification.created_at).toLocaleString()}
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
