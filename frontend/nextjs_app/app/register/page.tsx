'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { CheckCircle2 } from 'lucide-react'
import { djangoClient } from '@/services/djangoClient'
import { GoogleSignInButton } from '../login/[role]/components/GoogleSignInButton'

export default function RegisterPage() {
  const router = useRouter()
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [country, setCountry] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleEmailSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!firstName || !lastName) {
      setError('First name and last name are required')
      return
    }

    setLoading(true)
    try {
      const payload: any = {
        email,
        first_name: firstName,
        last_name: lastName,
        passwordless: true,
        role: 'student',
      }
      if (country.trim()) {
        payload.country = country.trim().toUpperCase().slice(0, 2)
      }

      await djangoClient.auth.signup(payload)
      setSuccess('Account created. Please check your email to set your password and complete onboarding.')
      setFirstName('')
      setLastName('')
      setEmail('')
      setCountry('')
    } catch (err: any) {
      setError(err?.data?.detail || err.message || 'Signup failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 text-och-gold">Create Your Account</h1>
          <p className="text-och-steel">Start your cybersecurity journey today</p>
        </div>

        <Card className="mb-6">
          {error && (
            <div className="mb-4 p-3 bg-och-orange/20 border border-och-orange/40 rounded-lg text-och-orange text-sm">
              {error}
            </div>
          )}

          <div className="space-y-4 mb-6">
            <GoogleSignInButton role="student" />
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-och-steel/20"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-och-midnight text-och-steel">or continue with email</span>
            </div>
          </div>

          <form onSubmit={handleEmailSignup} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-och-steel mb-1">
                  First Name
                </label>
                <input
                  id="firstName"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-defender"
                  placeholder="John"
                  required
                  disabled={loading}
                />
              </div>
              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-och-steel mb-1">
                  Last Name
                </label>
                <input
                  id="lastName"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-defender"
                  placeholder="Doe"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-och-steel mb-1">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-defender"
                placeholder="your.email@example.com"
                required
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="country" className="block text-sm font-medium text-och-steel mb-1">
                Country (Optional)
              </label>
              <input
                id="country"
                type="text"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-defender"
                placeholder="BW"
                disabled={loading}
              />
              <p className="mt-1 text-xs text-och-steel">2-letter ISO code (e.g., BW, US, KE)</p>
            </div>

            <Button
              type="submit"
              variant="defender"
              className="w-full"
              glow
              disabled={loading}
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </form>
        </Card>

        <div className="text-center">
          <p className="text-och-steel text-sm">
            Already have an account?{' '}
            <Link href="/login" className="text-och-defender hover:text-och-mint transition">
              Sign In
            </Link>
          </p>
        </div>

        <Dialog open={!!success} onOpenChange={(open) => { if (!open) setSuccess('') }}>
          <DialogContent className="bg-och-midnight border-och-mint/40">
            <DialogHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-full bg-och-mint/20 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-och-mint" />
                </div>
                <DialogTitle className="text-och-mint">
                  Account created
                </DialogTitle>
              </div>
              <DialogDescription className="text-och-steel">
                Please check your email to set your password and complete onboarding.
              </DialogDescription>
            </DialogHeader>
            <div className="mt-4 flex justify-end">
              <Button variant="defender" size="sm" onClick={() => setSuccess('')}>
                OK
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}

