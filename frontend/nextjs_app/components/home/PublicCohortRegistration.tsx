'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GraduationCap, Users, X } from 'lucide-react'
import { apiGateway } from '@/services/apiGateway'

interface FormField {
  key: string
  label: string
  type: string
  required: boolean
}

interface PublishedCohort {
  id: string
  name: string
  start_date: string
  end_date: string
  mode: string
  track: { id: string; name: string }
  program: { id: string; name: string } | null
  profile_image_url: string | null
  student_form_fields: FormField[]
  sponsor_form_fields: FormField[]
  seat_cap: number
  enrollment_count: number
}

type ApplicantType = 'student' | 'sponsor'

export function PublicCohortRegistration() {
  const [cohorts, setCohorts] = useState<PublishedCohort[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCohort, setSelectedCohort] = useState<PublishedCohort | null>(null)
  const [applicantType, setApplicantType] = useState<ApplicantType | null>(null)
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCohorts()
  }, [])

  const fetchCohorts = async () => {
    try {
      const res = await apiGateway.get('/public/cohorts/', { skipAuth: true })
      const data = res as any
      setCohorts(data || [])
    } catch {
      setCohorts([])
    } finally {
      setLoading(false)
    }
  }

  const openForm = (cohort: PublishedCohort, type: ApplicantType) => {
    setSelectedCohort(cohort)
    setApplicantType(type)
    setFormData({})
    setSuccess(null)
    setError(null)
  }

  const closeForm = () => {
    setSelectedCohort(null)
    setApplicantType(null)
    setFormData({})
    setSuccess(null)
    setError(null)
  }

  const getFields = () => {
    if (!selectedCohort || !applicantType) return []
    return applicantType === 'student'
      ? selectedCohort.student_form_fields
      : selectedCohort.sponsor_form_fields
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCohort || !applicantType) return
    setSubmitting(true)
    setError(null)
    try {
      const endpoint =
        applicantType === 'student'
          ? `/public/cohorts/${selectedCohort.id}/apply/student/`
          : `/public/cohorts/${selectedCohort.id}/apply/sponsor/`
      const res = await apiGateway.post(endpoint, { form_data: formData }, { skipAuth: true })
      const data = res as any
      setSuccess(data?.message || 'Application submitted successfully!')
      setFormData({})
    } catch (err: any) {
      const msg =
        err?.data?.error || err?.data?.detail || err?.message || 'Submission failed. Please try again.'
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return null
  if (cohorts.length === 0) return null

  const fields = getFields()

  return (
    <section className="py-8 sm:py-10 px-4 sm:px-6">
      <div className="max-w-[1140px] mx-auto">
        <div className="text-center mb-8 space-y-3">
          <p className="text-[11px] uppercase tracking-[0.24em] text-[#FBBF24] font-semibold">Available Cohorts</p>
          <h2 className="font-heading text-[clamp(32px,4vw,48px)] font-bold tracking-[-1.5px] text-[#E2E8F0]">
            Apply to a <span className="text-[#F59E0B]">Cohort</span>
          </h2>
          <p className="text-[14px] sm:text-[16px] text-[#94A3B8] max-w-2xl mx-auto leading-[1.7]">
            Join an upcoming cohort as a student or sponsor your talent development
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {cohorts.map((cohort) => (
            <div
              key={cohort.id}
              className="relative rounded-[18px] border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.03)] backdrop-blur-xl shadow-[0_18px_60px_rgba(0,0,0,0.85)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_22px_70px_rgba(0,0,0,0.95)] hover:border-[rgba(245,158,11,0.3)] overflow-hidden"
            >
              <div className="aspect-video bg-[rgba(6,9,15,0.8)] flex items-center justify-center overflow-hidden border-b border-[rgba(255,255,255,0.05)]">
                {cohort.profile_image_url ? (
                  <img
                    src={cohort.profile_image_url}
                    alt={cohort.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-[#F59E0B]/30">
                    <GraduationCap className="w-16 h-16 mx-auto" />
                  </div>
                )}
              </div>
              <div className="p-5 sm:p-6">
                <h3 className="text-[18px] sm:text-xl font-bold text-[#E2E8F0] mb-2">{cohort.name}</h3>
                <p className="text-[13px] sm:text-sm text-[#F59E0B] mb-1 font-medium">
                  {cohort.track?.name} {cohort.program && `• ${cohort.program.name}`}
                </p>
                <p className="text-[11px] sm:text-xs text-[#94A3B8] mb-4">
                  {cohort.start_date} – {cohort.end_date} • {cohort.mode}
                </p>
                <div className="flex flex-col gap-2">
                  <button
                    type="button"
                    className="w-full inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[#F59E0B] to-[#D97706] px-4 py-2.5 text-[13px] font-bold text-[#0A0E1A] shadow-[0_0_24px_rgba(245,158,11,0.55)] hover:shadow-[0_0_30px_rgba(245,158,11,0.7)] hover:-translate-y-0.5 transition-all duration-200"
                    onClick={() => openForm(cohort, 'student')}
                  >
                    <GraduationCap className="w-4 h-4" />
                    Apply as Student
                  </button>
                  <button
                    type="button"
                    className="w-full inline-flex items-center justify-center gap-2 rounded-full border border-[rgba(255,255,255,0.15)] bg-[rgba(6,9,15,0.6)] px-4 py-2.5 text-[13px] font-medium text-[#E2E8F0] hover:border-[rgba(245,158,11,0.6)] hover:text-[#F59E0B] transition-colors duration-200"
                    onClick={() => openForm(cohort, 'sponsor')}
                  >
                    <Users className="w-4 h-4" />
                    Join as Sponsor
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <AnimatePresence>
          {selectedCohort && applicantType && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xl"
              onClick={closeForm}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="w-full max-w-md"
              >
                <div className="relative rounded-[18px] border border-[rgba(255,255,255,0.1)] bg-slate-950/80 backdrop-blur-xl shadow-[0_18px_60px_rgba(0,0,0,0.85)] p-5 sm:p-6 max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-[18px] sm:text-xl font-bold text-[#E2E8F0]">
                      {applicantType === 'student' ? 'Apply as Student' : 'Join as Sponsor'} –{' '}
                      {selectedCohort.name}
                    </h3>
                    <button
                      type="button"
                      onClick={closeForm}
                      className="rounded-full border border-white/10 bg-slate-900/80 p-1.5 text-slate-400 hover:text-amber-300 hover:border-amber-400/50 transition-colors"
                      aria-label="Close"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {success ? (
                    <div className="p-4 bg-emerald-500/10 border border-emerald-400/30 rounded-lg text-emerald-300">
                      {success}
                    </div>
                  ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                      {error && (
                        <div className="p-3 bg-rose-500/10 border border-rose-400/30 rounded-lg text-rose-300 text-sm">
                          {error}
                        </div>
                      )}
                      {fields.map((field) => (
                        <div key={field.key}>
                          <label className="block text-[13px] font-medium text-[#E2E8F0] mb-1.5">
                            {field.label}
                            {field.required && <span className="text-[#F59E0B]">*</span>}
                          </label>
                          {field.type === 'textarea' ? (
                            <textarea
                              required={field.required}
                              value={formData[field.key] || ''}
                              onChange={(e) =>
                                setFormData((prev) => ({ ...prev, [field.key]: e.target.value }))
                              }
                              className="w-full px-3 py-2 bg-slate-950/70 border border-white/10 rounded-lg text-[#E2E8F0] text-[13px] placeholder:text-slate-600 focus:outline-none focus:border-amber-400/70 focus:ring-1 focus:ring-amber-400/60 min-h-[80px]"
                              placeholder={field.label}
                              rows={3}
                            />
                          ) : (
                            <input
                              type={field.type === 'url' ? 'url' : field.type || 'text'}
                              required={field.required}
                              value={formData[field.key] || ''}
                              onChange={(e) =>
                                setFormData((prev) => ({ ...prev, [field.key]: e.target.value }))
                              }
                              className="w-full px-3 py-2 bg-slate-950/70 border border-white/10 rounded-lg text-[#E2E8F0] text-[13px] placeholder:text-slate-600 focus:outline-none focus:border-amber-400/70 focus:ring-1 focus:ring-amber-400/60"
                              placeholder={field.label}
                            />
                          )}
                        </div>
                      ))}
                      <div className="flex gap-2 pt-4">
                        <button
                          type="button"
                          onClick={closeForm}
                          className="flex-1 inline-flex items-center justify-center rounded-full border border-[rgba(255,255,255,0.15)] bg-[rgba(6,9,15,0.6)] px-4 py-2.5 text-[13px] font-medium text-[#E2E8F0] hover:border-[rgba(245,158,11,0.6)] hover:text-[#F59E0B] transition-colors duration-200"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={submitting}
                          className="flex-1 inline-flex items-center justify-center rounded-full bg-gradient-to-r from-[#F59E0B] to-[#D97706] px-4 py-2.5 text-[13px] font-bold text-[#0A0E1A] shadow-[0_0_24px_rgba(245,158,11,0.55)] hover:shadow-[0_0_30px_rgba(245,158,11,0.7)] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                        >
                          {submitting ? 'Submitting...' : 'Submit'}
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  )
}
