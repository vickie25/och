'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { AfricaCountrySelect } from '@/components/ui/AfricaCountrySelect'
import { useAuth } from '@/hooks/useAuth'
import { apiGateway } from '@/services/apiGateway'

export default function OnboardingSetCountryPage() {
  const router = useRouter()
  const { user, reloadUser, isAuthenticated } = useAuth()
  const [country, setCountry] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    if (!isAuthenticated || user === undefined) {
      setChecking(false)
      return
    }
    if (user?.country && user.country.length === 2) {
      router.push('/onboarding/ai-profiler')
      return
    }
    setChecking(false)
  }, [isAuthenticated, user, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!country || country.length !== 2) {
      setError('Please select your country')
      return
    }
    if (!user?.id) {
      setError('You must be logged in to continue')
      return
    }
    setLoading(true)
    try {
      await apiGateway.patch(`/users/${user.id}/`, {
        country: country.trim().toUpperCase(),
      })
      await reloadUser?.()
      router.push('/onboarding/ai-profiler')
    } catch (err: any) {
      setError(err?.data?.detail || err?.message || 'Failed to save country. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (checking) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <Card className="p-8 max-w-md w-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-och-mint mx-auto mb-4" />
            <p className="text-och-steel">Loading...</p>
          </div>
        </Card>
      </div>
    )
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
        <Card className="p-8 max-w-md w-full">
          <div className="text-center">
            <p className="text-och-steel mb-4">You need to log in to continue onboarding.</p>
            <Button variant="defender" onClick={() => router.push('/login/student')}>
              Go to Login
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2 text-och-gold">Where are you from?</h1>
          <p className="text-och-steel">Select your country to continue. This helps us show prices in your currency.</p>
        </div>

        <Card className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-och-orange/20 border border-och-orange/40 rounded-lg text-och-orange text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <AfricaCountrySelect
              id="country"
              label="Country"
              value={country}
              onChange={setCountry}
              placeholder="Select your country"
              disabled={loading}
              required
            />
            <Button
              type="submit"
              variant="defender"
              className="w-full"
              glow
              disabled={loading || !country || country.length !== 2}
            >
              {loading ? 'Saving...' : 'Continue'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}
