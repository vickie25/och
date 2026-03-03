'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import { LogOut, Clock } from 'lucide-react'

const STORAGE_KEY = 'impersonation_expires_at'

function formatRemaining(seconds: number): string {
  if (seconds <= 0) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function ImpersonationBanner() {
  const [expiresAt, setExpiresAt] = useState<string | null>(null)
  const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null)
  const [ending, setEnding] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const parsed = new Date(raw).getTime()
    if (isNaN(parsed)) {
      sessionStorage.removeItem(STORAGE_KEY)
      return
    }
    setExpiresAt(raw)
  }, [])

  useEffect(() => {
    if (!expiresAt) return
    let intervalId: ReturnType<typeof setInterval>
    const tick = () => {
      const end = new Date(expiresAt).getTime()
      const now = Date.now()
      const sec = Math.max(0, Math.floor((end - now) / 1000))
      setRemainingSeconds(sec)
      if (sec <= 0) {
        clearInterval(intervalId)
        endImpersonation()
      }
    }
    tick()
    intervalId = setInterval(tick, 1000)
    return () => clearInterval(intervalId)
  }, [expiresAt])

  async function endImpersonation() {
    if (ending) return
    setEnding(true)
    try {
      sessionStorage.removeItem(STORAGE_KEY)
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
    } catch {
      // continue
    }
    window.location.href = '/support/tickets'
  }

  if (expiresAt === null || remainingSeconds === null) return null
  if (remainingSeconds <= 0) return null

  return (
    <div className="sticky top-0 z-50 w-full bg-och-defender/20 border-b border-och-defender/40 px-4 py-2 flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-3 text-sm">
        <span className="font-semibold text-och-defender">Support view</span>
        <span className="text-och-steel flex items-center gap-1.5">
          <Clock className="w-4 h-4" aria-hidden />
          Session expires in <strong className="text-white tabular-nums">{formatRemaining(remainingSeconds)}</strong>
        </span>
      </div>
      <Button
        variant="outline"
        size="sm"
        onClick={() => endImpersonation()}
        disabled={ending}
        className="border-och-defender/50 text-och-defender hover:bg-och-defender/10"
      >
        <LogOut className="w-4 h-4 mr-2" aria-hidden />
        {ending ? 'Ending…' : 'End session'}
      </Button>
    </div>
  )
}
