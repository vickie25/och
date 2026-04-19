'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useAuth } from '@/hooks/useAuth'
import { curriculumClient } from '@/services/curriculumClient'
import { apiGateway } from '@/services/apiGateway'

interface ProgramFormData {
  name: string
  category: string
  categories: string[]
  description: string
  duration_months: number
  default_price: number
  currency: string
  outcomes: string[]
  missions_registry_link: string
  structure?: Record<string, any>
}

export default function CreateProgramClient() {
  const router = useRouter()
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState<ProgramFormData>({
    name: '',
    category: 'technical',
    categories: [],
    description: '',
    duration_months: 12,
    default_price: 0,
    currency: 'KSh',
    outcomes: [''],
    missions_registry_link: '',
    structure: undefined
  })
  const [tracks, setTracks] = useState<any[]>([])
  const [tracksLoading, setTracksLoading] = useState(true)
  const [tracksError, setTracksError] = useState<string | null>(null)
  const [selectedTrackCodes, setSelectedTrackCodes] = useState<string[]>([])

  useEffect(() => {
    const loadTracks = async () => {
      try {
        setTracksLoading(true)
        setTracksError(null)
        const data = await curriculumClient.getTracks()
        setTracks(Array.isArray(data) ? data : [])
      } catch (err: any) {
        console.error('Failed to load curriculum tracks:', err)
        setTracksError(err?.message || 'Failed to load tracks')
        setTracks([])
      } finally {
        setTracksLoading(false)
      }
    }

    loadTracks()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess(false)

    try {
      const payload: any = {
        ...formData,
        outcomes: formData.outcomes.filter(o => o.trim() !== '')
      }

      if (selectedTrackCodes.length > 0) {
        payload.structure = {
          ...(formData.structure || {}),
          curriculum_tracks: selectedTrackCodes
        }
      }

      const program = await apiGateway.post<any>('/director/programs/', payload)
      
      setSuccess(true)
      setTimeout(() => {
        router.push(`/dashboard/director/programs/${program.id}`)
      }, 2000)
    } catch (err: any) {
      console.error('Failed to create program:', err)
      setError(err?.data?.message || err?.data?.error || err.message || 'Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const addOutcome = () => {
    setFormData(prev => ({
      ...prev,
      outcomes: [...prev.outcomes, '']
    }))
  }

  const updateOutcome = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      outcomes: prev.outcomes.map((outcome, i) => i === index ? value : outcome)
    }))
  }

  const removeOutcome = (index: number) => {
    setFormData(prev => ({
      ...prev,
      outcomes: prev.outcomes.filter((_, i) => i !== index)
    }))
  }

  const toggleCategory = (category: string) => {
    setFormData(prev => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter(c => c !== category)
        : [...prev.categories, category]
    }))
  }

  const toggleTrack = (code: string) => {
    setSelectedTrackCodes(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Create New Program</h1>
        <p className="text-och-steel">Define a new program with tracks, competencies, and learning outcomes</p>
      </div>

      {success && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-och-midnight border border-och-mint/50 rounded-lg p-8 max-w-md mx-4 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-och-mint/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-och-mint" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Success!</h3>
            <p className="text-och-mint mb-4">Program created successfully</p>
            <p className="text-och-steel text-sm">Redirecting to program details...</p>
          </div>
        </div>
      )}

      {error && (
        <Card className="mb-6 border-och-orange/50 bg-och-orange/10">
          <div className="p-4 flex items-center gap-3">
            <svg className="w-5 h-5 text-och-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-och-orange">{error}</p>
          </div>
        </Card>
      )}

      <form onSubmit={handleSubmit}>
        <Card className="mb-6">
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Basic Information</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Program Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white focus:border-och-defender focus:outline-none"
                  placeholder="e.g., Cyber Security Foundations"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Duration (Months) *
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  max="24"
                  value={formData.duration_months}
                  onChange={(e) => setFormData(prev => ({ ...prev, duration_months: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white focus:border-och-defender focus:outline-none"
                />
              </div>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-och-steel mb-2">
                Description
              </label>
              <textarea
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white focus:border-och-defender focus:outline-none"
                placeholder="Describe the program objectives and target audience..."
              />
            </div>
          </div>
        </Card>

        <Card className="mb-6">
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Tracks</h2>

            {tracksLoading ? (
              <p className="text-och-steel text-sm">Loading tracks...</p>
            ) : tracksError ? (
              <p className="text-och-orange text-sm">{tracksError}</p>
            ) : tracks.length === 0 ? (
              <p className="text-och-steel text-sm">No curriculum tracks available.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {tracks.map((track: any) => {
                  const code = (track.code || track.slug || track.id || '').toString()
                  const title = track.title || track.name || track.code || 'Track'
                  const description = track.description || ''
                  const selected = selectedTrackCodes.includes(code)

                  return (
                    <button
                      key={code}
                      type="button"
                      onClick={() => toggleTrack(code)}
                      className={`text-left p-3 rounded-lg border-2 transition-all ${
                        selected
                          ? 'border-och-defender bg-och-defender/20'
                          : 'border-och-steel/30 hover:border-och-steel/50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-white text-sm">{title}</span>
                        {track.tier != null && (
                          <Badge variant="outline" className="text-xs text-och-steel border-och-steel/40">
                            Tier {track.tier}
                          </Badge>
                        )}
                      </div>
                      {description && (
                        <p className="text-xs text-och-steel line-clamp-2">
                          {description}
                        </p>
                      )}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </Card>

        <Card className="mb-6">
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Learning Outcomes</h2>
            
            <div className="space-y-3">
              {formData.outcomes.map((outcome, index) => (
                <div key={index} className="flex gap-3">
                  <input
                    type="text"
                    value={outcome}
                    onChange={(e) => updateOutcome(index, e.target.value)}
                    className="flex-1 px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white focus:border-och-defender focus:outline-none"
                    placeholder="e.g., Master incident response procedures"
                  />
                  {formData.outcomes.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => removeOutcome(index)}
                    >
                      Remove
                    </Button>
                  )}
                </div>
              ))}
            </div>
            
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addOutcome}
              className="mt-3"
            >
              + Add Learning Outcome
            </Button>
          </div>
        </Card>

        <Card className="mb-6">
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Pricing & Resources</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Default Price
                </label>
                <div className="flex">
                  <select
                    value={formData.currency}
                    onChange={(e) => setFormData(prev => ({ ...prev, currency: e.target.value }))}
                    className="px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-l-lg text-white focus:border-och-defender focus:outline-none"
                  >
                    <option value="KSh">KSh</option>
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                  </select>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.default_price}
                    onChange={(e) => setFormData(prev => ({ ...prev, default_price: parseFloat(e.target.value) }))}
                    className="flex-1 px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-r-lg text-white focus:border-och-defender focus:outline-none"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Missions Registry Link
                </label>
                <input
                  type="url"
                  value={formData.missions_registry_link}
                  onChange={(e) => setFormData(prev => ({ ...prev, missions_registry_link: e.target.value }))}
                  className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white focus:border-och-defender focus:outline-none"
                  placeholder="https://missions.ongoza.com/registry/..."
                />
              </div>
            </div>
          </div>
        </Card>

        <div className="flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="defender"
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Program'}
          </Button>
        </div>
      </form>
    </div>
  )
}