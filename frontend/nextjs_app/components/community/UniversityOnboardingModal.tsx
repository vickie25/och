'use client'

import { useEffect, useMemo, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { apiGateway } from '@/services/apiGateway'
import { useRouter } from 'next/navigation'

interface University {
  id: string
  name: string
  short_name?: string
  code?: string
  slug?: string
}

const COUNTRIES: Array<{ code: string; name: string; defaultTimezone: string }> = [
  { code: 'KE', name: 'Kenya', defaultTimezone: 'Africa/Nairobi' },
  { code: 'UG', name: 'Uganda', defaultTimezone: 'Africa/Kampala' },
  { code: 'TZ', name: 'Tanzania', defaultTimezone: 'Africa/Dar_es_Salaam' },
  { code: 'RW', name: 'Rwanda', defaultTimezone: 'Africa/Kigali' },
  { code: 'ET', name: 'Ethiopia', defaultTimezone: 'Africa/Addis_Ababa' },
  { code: 'NG', name: 'Nigeria', defaultTimezone: 'Africa/Lagos' },
  { code: 'GH', name: 'Ghana', defaultTimezone: 'Africa/Accra' },
  { code: 'ZA', name: 'South Africa', defaultTimezone: 'Africa/Johannesburg' },
  { code: 'US', name: 'United States', defaultTimezone: 'America/New_York' },
  { code: 'GB', name: 'United Kingdom', defaultTimezone: 'Europe/London' },
]

interface UniversityOnboardingModalProps {
  isOpen: boolean
  onClose: () => void
  onCompleted: () => Promise<void> | void
}

export function UniversityOnboardingModal({
  isOpen,
  onClose,
  onCompleted,
}: UniversityOnboardingModalProps) {
  const router = useRouter()
  const [universities, setUniversities] = useState<University[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [country, setCountry] = useState<string>('KE')
  const [timezone, setTimezone] = useState<string>('Africa/Nairobi')
  const [search, setSearch] = useState('')
  const [selectedUniversity, setSelectedUniversity] = useState<University | null>(null)
  const [communityDisplayName, setCommunityDisplayName] = useState('')

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return universities
    return universities.filter((u) => {
      return (
        u.name.toLowerCase().includes(q) ||
        (u.short_name || '').toLowerCase().includes(q) ||
        (u.code || '').toLowerCase().includes(q)
      )
    })
  }, [universities, search])

  useEffect(() => {
    if (!isOpen) return

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const settings = await apiGateway.get<any>(`/settings/`).catch(() => null)
        if (settings?.communityDisplayName && typeof settings.communityDisplayName === 'string') {
          setCommunityDisplayName(settings.communityDisplayName)
        }

        if (settings?.country && typeof settings.country === 'string') {
          setCountry(settings.country.toUpperCase())
        }

        if (settings?.timezone && typeof settings.timezone === 'string') {
          setTimezone(settings.timezone)
        } else {
          const inferred = COUNTRIES.find((c) => c.code === (settings?.country || 'KE').toUpperCase())
          setTimezone(inferred?.defaultTimezone || 'UTC')
        }

        const selectedCountry = (settings?.country && typeof settings.country === 'string')
          ? settings.country.toUpperCase()
          : 'KE'

        const raw = await apiGateway.get<any>(`/community/universities/?country=${selectedCountry}&page_size=300`)
        let list = Array.isArray(raw) ? raw : (raw?.results ?? [])

        // Data currently may only be seeded for some countries (e.g. KE).
        // If the selected country has no universities, fall back to showing all.
        if (Array.isArray(list) && list.length === 0) {
          const fallbackRaw = await apiGateway.get<any>(`/community/universities/?page_size=300`)
          list = Array.isArray(fallbackRaw) ? fallbackRaw : (fallbackRaw?.results ?? [])
        }

        setUniversities(list)
      } catch (e: any) {
        setError(e?.message || 'Failed to load universities')
      } finally {
        setLoading(false)
      }
    }

    void load()
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return

    const loadForCountry = async () => {
      setLoading(true)
      setError(null)
      try {
        const raw = await apiGateway.get<any>(`/community/universities/?country=${country}&page_size=300`)
        let list = Array.isArray(raw) ? raw : (raw?.results ?? [])

        // If nothing is available for this country yet, show all universities so search still works.
        if (Array.isArray(list) && list.length === 0) {
          const fallbackRaw = await apiGateway.get<any>(`/community/universities/?page_size=300`)
          list = Array.isArray(fallbackRaw) ? fallbackRaw : (fallbackRaw?.results ?? [])
        }

        setUniversities(list)
        setSelectedUniversity(null)
        setSearch('')
      } catch (e: any) {
        setError(e?.message || 'Failed to load universities')
      } finally {
        setLoading(false)
      }
    }

    void loadForCountry()
  }, [country, isOpen])

  useEffect(() => {
    const inferred = COUNTRIES.find((c) => c.code === country)
    if (inferred && inferred.defaultTimezone && (!timezone || timezone === 'UTC')) {
      setTimezone(inferred.defaultTimezone)
    }
  }, [country])

  const handleSave = async () => {
    if (!selectedUniversity) return

    setSaving(true)
    setError(null)
    try {
      // Save community display name (optional)
      await apiGateway.patch(`/settings/`, {
        communityDisplayName: communityDisplayName?.trim() ? communityDisplayName.trim() : null,
        country,
        timezone,
      })

      // Create university membership (Option 1 enforced server-side)
      await apiGateway.post(`/community/memberships/`, {
        university_id: selectedUniversity.id,
        role: 'student',
        status: 'active',
        is_primary: true,
      })

      await onCompleted()
      // Parent controls visibility via `onCompleted` (Option 1 modal is not dismissible).
      // After completing, take the user to the community page.
      router.push('/dashboard/student/community')
    } catch (e: any) {
      const msg = e?.data?.detail || e?.message || 'Failed to complete university setup'
      setError(msg)
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-white">Set up your University Community</h2>
              <p className="text-och-steel text-sm mt-1">
                Choose your country and one university. You won&apos;t be able to select another later.
              </p>
            </div>
            <Button variant="outline" onClick={onClose} disabled={saving}>
              Cancel
            </Button>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-white mb-2">Country</label>
              <Select
                value={country}
                onValueChange={(v) => {
                  setCountry(v)
                  const inferred = COUNTRIES.find((c) => c.code === v)
                  if (inferred) setTimezone(inferred.defaultTimezone)
                }}
                disabled={loading || saving}
              >
                <SelectTrigger className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender">
                  <SelectValue placeholder="Select country" />
                </SelectTrigger>
                <SelectContent>
                  {COUNTRIES.map((c) => (
                    <SelectItem key={c.code} value={c.code}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-och-steel text-xs mt-2">
                This filters your university list.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">Timezone</label>
              <input
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                placeholder="e.g. Africa/Nairobi"
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                disabled={saving}
              />
              <p className="text-och-steel text-xs mt-2">
                Used to show others your local time in global community chats.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">Community display name</label>
              <input
                value={communityDisplayName}
                onChange={(e) => setCommunityDisplayName(e.target.value)}
                placeholder="How your name should appear in community"
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
              />
              <p className="text-och-steel text-xs mt-2">
                If blank, your profile name/email will be used.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">Choose your university</label>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name or code"
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                disabled={loading || saving}
              />

              {selectedUniversity && (
                <div className="mt-3 p-3 rounded-lg border border-och-defender/40 bg-och-defender/10">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-white font-semibold text-sm">Selected</div>
                      <div className="text-white font-medium text-sm mt-1">{selectedUniversity.name}</div>
                      {(selectedUniversity.short_name || selectedUniversity.code || selectedUniversity.slug) ? (
                        <div className="text-och-steel text-xs mt-1">
                          {selectedUniversity.short_name || selectedUniversity.code || selectedUniversity.slug}
                        </div>
                      ) : null}
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setSelectedUniversity(null)
                        setSearch('')
                      }}
                      disabled={saving}
                    >
                      Change
                    </Button>
                  </div>
                </div>
              )}

              <div className="mt-3 max-h-72 overflow-y-auto space-y-2">
                {loading ? (
                  <div className="text-och-steel text-sm">Loading universities...</div>
                ) : (
                  filtered.slice(0, 60).map((u) => {
                    const selected = selectedUniversity?.id === u.id
                    return (
                      <button
                        key={u.id}
                        onClick={() => {
                          setSelectedUniversity(u)
                          setSearch(u.name)
                        }}
                        className={`w-full text-left p-3 rounded-lg border transition-colors ${
                          selected
                            ? 'border-och-defender bg-och-defender/10'
                            : 'border-och-steel/20 bg-och-midnight/30 hover:border-och-defender/40'
                        }`}
                        disabled={saving}
                      >
                        <div className="text-white font-medium text-sm">{u.name}</div>
                        <div className="text-och-steel text-xs mt-1">
                          {(u.short_name || u.code || u.slug) ? (u.short_name || u.code || u.slug) : ''}
                        </div>
                      </button>
                    )
                  })
                )}

                {!loading && filtered.length === 0 && (
                  <div className="text-och-steel text-sm">No universities match your search.</div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={onClose} disabled={saving}>
                Close
              </Button>
              <Button variant="defender" onClick={handleSave} disabled={!selectedUniversity || saving}>
                {saving ? 'Saving...' : 'Save & Continue'}
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
