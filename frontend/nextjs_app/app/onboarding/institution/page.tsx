'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { apiGateway } from '@/services/apiGateway'
import { Eye, EyeOff } from 'lucide-react'

function InstitutionOnboardingPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const organization = searchParams.get('organization') || ''
  const contract = searchParams.get('contract') || ''
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<any>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    termsAccepted: false,
  })

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const data = await apiGateway.get(
          `/finance/contracts/institution-onboarding-preview/?organization=${encodeURIComponent(organization)}&contract=${encodeURIComponent(contract)}`
        )
        setPreview(data)
        if (data?.contract?.type === 'employer') {
          setError('This link is for an employer contract. Use the employer onboarding URL from your invitation email.')
          return
        }
        const contactName = String(data?.organization?.contact_person_name || '').trim()
        const contactEmail = String(data?.organization?.contact_email || '').trim()
        const [first = '', ...rest] = contactName.split(/\s+/)
        const last = rest.join(' ')
        setForm((prev) => ({
          ...prev,
          first_name: prev.first_name || first,
          last_name: prev.last_name || last,
          email: contactEmail,
        }))
      } catch (e: any) {
        setError(e?.message || 'Failed to load contract onboarding details.')
      } finally {
        setLoading(false)
      }
    }
    if (organization && contract) load()
    else {
      setLoading(false)
      setError('Invalid onboarding link.')
    }
  }, [organization, contract])

  const handleComplete = async () => {
    setError(null)
    if (!form.password || form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (!form.termsAccepted) {
      setError('You must accept the Terms and Conditions.')
      return
    }
    setSubmitting(true)
    try {
      const result = await apiGateway.post('/finance/contracts/institution-onboarding-complete/', {
        organization,
        contract,
        email: form.email,
        first_name: form.first_name,
        last_name: form.last_name,
        password: form.password,
        terms_accepted: form.termsAccepted,
      }) as any

      const loginRes = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: result.email,
          password: form.password,
          device_fingerprint: `institution-onboarding-${Date.now()}`,
          device_name: 'Institution Onboarding',
        }),
      })
      if (!loginRes.ok) {
        const loginErr = await loginRes.json().catch(() => ({}))
        throw new Error(loginErr?.detail || 'Password set, but login failed.')
      }
      const nextUrl = result.next || `/dashboard/institution?organization=${organization}&contract=${contract}`
      const separator = nextUrl.includes('?') ? '&' : '?'
      router.replace(`${nextUrl}${separator}created=1`)
    } catch (e: any) {
      setError(e?.message || 'Failed to complete onboarding.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-och-midnight flex items-center justify-center p-6">
      <Card className="w-full max-w-3xl p-8 bg-och-midnight border border-och-steel/20">
        <h1 className="text-2xl font-bold text-white mb-3">Institution Onboarding</h1>
        <p className="text-och-steel mb-6">
          Review contract details, set your account password, then continue to your institution portal to review
          contract status, choose plan/tier, and generate invoice.
        </p>

        {loading ? (
          <p className="text-och-steel">Loading onboarding details...</p>
        ) : (
          <>
            <div className="space-y-2 text-sm mb-6">
              <p className="text-och-steel">Organization: <span className="text-white">{preview?.organization?.name || organization || '—'}</span></p>
              <p className="text-och-steel">Contract: <span className="text-white">{contract || '—'}</span></p>
              <p className="text-och-steel">Type: <span className="text-white">{preview?.contract?.type || 'institution'}</span></p>
              <p className="text-och-steel">Duration: <span className="text-white">{preview?.contract?.start_date} to {preview?.contract?.end_date}</span></p>
              <p className="text-och-steel">Status: <span className="text-white">{preview?.contract?.status || 'proposal'}</span></p>
            </div>

            <div className="rounded-lg border border-och-steel/20 bg-och-steel/10 p-4 mb-6">
              <p className="text-white font-medium mb-3">Organization details</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <label className="block text-och-steel mb-1">Organization name</label>
                  <Input value={preview?.organization?.name || ''} readOnly />
                </div>
                <div>
                  <label className="block text-och-steel mb-1">Contact email</label>
                  <Input value={preview?.organization?.contact_email || ''} readOnly />
                </div>
                <div>
                  <label className="block text-och-steel mb-1">Contact person</label>
                  <Input value={preview?.organization?.contact_person_name || ''} readOnly />
                </div>
                <div>
                  <label className="block text-och-steel mb-1">Contract ID</label>
                  <Input value={contract} readOnly />
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-och-steel/20 bg-och-steel/10 p-4 text-sm text-och-steel mb-6">
              <p className="mb-2 text-white font-medium">Next steps after account setup</p>
              <p>1) Review contract pending approval details</p>
              <p>2) Fill institution profile and expected student volume</p>
              <p>3) Choose plan/tier and billing cycle</p>
              <p>4) Generate invoice and complete payment</p>
              <p>5) Add students in your institution portal</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">First Name</label>
                <Input
                  value={form.first_name}
                  onChange={(e) => setForm((prev) => ({ ...prev, first_name: e.target.value }))}
                  placeholder="First name"
                  autoComplete="given-name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">Last Name</label>
                <Input
                  value={form.last_name}
                  onChange={(e) => setForm((prev) => ({ ...prev, last_name: e.target.value }))}
                  placeholder="Last name"
                  autoComplete="family-name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">Email</label>
                <Input
                  value={form.email}
                  onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
                  placeholder="Email"
                  autoComplete="email"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">Password</label>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={form.password}
                    onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
                    placeholder="Set password"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-3 flex items-center text-och-steel hover:text-white"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">Confirm Password</label>
                <div className="relative">
                  <Input
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={form.confirmPassword}
                    onChange={(e) => setForm((prev) => ({ ...prev, confirmPassword: e.target.value }))}
                    placeholder="Confirm password"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-3 flex items-center text-och-steel hover:text-white"
                    aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>

            {error && <p className="text-sm text-och-orange mb-4">{error}</p>}

            <label className="flex items-start gap-3 text-sm text-och-steel mb-4">
              <input
                type="checkbox"
                checked={form.termsAccepted}
                onChange={(e) => setForm((prev) => ({ ...prev, termsAccepted: e.target.checked }))}
                className="mt-0.5"
              />
              <span>
                I agree to the{' '}
                <Link href="/terms-and-conditions" target="_blank" className="text-och-mint hover:underline">
                  Terms and Conditions
                </Link>.
              </span>
            </label>

            <div className="flex gap-3">
              <Button
                className="bg-och-mint hover:bg-och-mint/80"
                onClick={() => void handleComplete()}
                disabled={submitting}
              >
                {submitting ? 'Setting up account...' : 'Set Password & Continue'}
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}

export default function InstitutionOnboardingPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-och-midnight flex items-center justify-center p-8 text-och-steel">
          Loading onboarding…
        </div>
      }
    >
      <InstitutionOnboardingPageContent />
    </Suspense>
  )
}
