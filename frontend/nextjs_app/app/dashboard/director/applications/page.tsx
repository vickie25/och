'use client'

import { useState, useEffect, useMemo, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { DirectorLayout } from '@/components/director/DirectorLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { fastapiApi } from '@/services/fastapi_api'
import { programsClient } from '@/services/programsClient'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { GraduationCap, Users, Filter, ExternalLink, Eye, UserPlus, Award, UserCheck, FileQuestion, MessageSquare, Gauge, MoreHorizontal, Trash2, Send } from 'lucide-react'

interface Application {
  id: string
  cohort_id: string
  cohort_name: string
  applicant_type: string
  status: string
  form_data: Record<string, string>
  email: string
  name: string
  notes: string
  created_at: string
  reviewer_mentor_id?: number | null
  reviewer_mentor_name?: string | null
  review_score?: number | null
  review_status?: string
  interview_mentor_name?: string | null
  interview_score?: number | null
  interview_status?: string | null
  enrollment_status?: string
}

interface MentorAssignment {
  id: string
  mentor: number | { id: number; email: string; first_name?: string; last_name?: string }
  mentor_email?: string
  mentor_name?: string
}

interface Cohort {
  id: string
  name: string
}

function ApplicationDetailsModal({
  application,
  open,
  onOpenChange,
  getStatusVariant,
  getApplicationStatusLabel,
  getStatusBadgeClass,
  onEnroll,
  onReject,
  onSendCredentials,
  onGradeTest,
  isGradeTestInProgress,
}: {
  application: Application | null
  open: boolean
  onOpenChange: (open: boolean) => void
  getStatusVariant: (s: string) => 'defender' | 'orange' | 'steel'
  getApplicationStatusLabel: (s: string, app?: Application) => string
  getStatusBadgeClass: (label: string) => string
  onEnroll?: (application: Application) => void
  onReject?: (application: Application) => void
  onSendCredentials?: (application: Application) => void
  onGradeTest?: (application: Application) => void
  isGradeTestInProgress?: boolean
}) {
  const [testQuestions, setTestQuestions] = useState<AppQuestionItem[] | null>(null)
  const [loadingTestQuestions, setLoadingTestQuestions] = useState(false)
  const [testQuestionsError, setTestQuestionsError] = useState<string | null>(null)

  const hasTestAnswers = application
    ? Array.isArray((application.form_data as any)?.application_test_answers) &&
      ((application.form_data as any).application_test_answers as any[]).length > 0
    : false

  useEffect(() => {
    if (!application || !hasTestAnswers || !application.cohort_id) {
      setTestQuestions(null)
      setTestQuestionsError(null)
      return
    }
    setLoadingTestQuestions(true)
    setTestQuestionsError(null)
    apiGateway
      .get('/director/application-questions/', {
        params: { cohort_id: application.cohort_id },
      })
      .then((res: unknown) => {
        const data = res as { questions?: AppQuestionItem[] }
        setTestQuestions((data.questions || []) as AppQuestionItem[])
      })
      .catch((err: unknown) => {
        const msg = (err as { message?: string })?.message || 'Failed to load application test questions.'
        setTestQuestionsError(msg)
        setTestQuestions(null)
      })
      .finally(() => setLoadingTestQuestions(false))
  }, [application, hasTestAnswers])

  if (!application) return null

  const formEntries = application.form_data
    ? Object.entries(application.form_data).filter(
        ([k, v]) =>
          v != null &&
          String(v).trim() !== '' &&
          ![
            'review_notes',
            'interview_notes',
            'support_documents',
            'application_test_answers',
            'application_test_token',
            'application_test_invited_at',
            'application_test_completed_at',
            'application_test_results',
          ].includes(k)
      )
    : []

  const reviewNotes = application.form_data?.review_notes as string | undefined
  const interviewNotes = application.form_data?.interview_notes as string | undefined
  const supportDocuments = application.form_data?.support_documents as string | string[] | undefined

  const rawTestAnswers = application.form_data?.application_test_answers as
    | { question_id: string; answer: string }[]
    | undefined

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md max-h-[90vh] flex flex-col border-och-steel/20 bg-och-midnight">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-white">
            {application.applicant_type === 'student' ? 'Student' : 'Sponsor'} Application Details
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 text-sm overflow-y-auto flex-1 min-h-0 pr-2">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-och-steel">Name</span>
              <p className="text-white font-medium">{application.name || '-'}</p>
            </div>
            <div>
              <span className="text-och-steel">Email</span>
              <p className="text-white font-medium">{application.email || '-'}</p>
            </div>
            <div>
              <span className="text-och-steel">Cohort</span>
              <p className="text-white font-medium truncate">{application.cohort_name}</p>
            </div>
            <div>
              <span className="text-och-steel">Application status</span>
              <p>
                {(() => {
                  const statusLabel = getApplicationStatusLabel(application.status, application)
                  const statusClass = getStatusBadgeClass(statusLabel)
                  return (
                    <Badge variant={getStatusVariant(application.status)} className={statusClass}>
                      {statusLabel}
                    </Badge>
                  )
                })()}
              </p>
            </div>
            <div>
              <span className="text-och-steel">Applied</span>
              <p className="text-white">
                {new Date(application.created_at).toLocaleString()}
              </p>
            </div>
          </div>

          {application.applicant_type === 'student' && (
            <div className="space-y-4 border-t border-och-steel/20 pt-4">
              <h4 className="text-sm font-medium text-white">Mentor feedback</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="rounded-lg bg-och-midnight/50 border border-och-steel/20 p-3">
                  <span className="text-xs text-och-steel block mb-1">Application review</span>
                  <p className="text-white font-medium">
                    Score: {(application as Application).review_score != null ? (application as Application).review_score : '—'}
                  </p>
                  {(application as Application).reviewer_mentor_name && (
                    <p className="text-xs text-och-steel mt-1">By {(application as Application).reviewer_mentor_name}</p>
                  )}
                  {reviewNotes && (
                    <p className="text-sm text-white mt-2 pt-2 border-t border-och-steel/20 whitespace-pre-wrap">{reviewNotes}</p>
                  )}
                </div>
                <div className="rounded-lg bg-och-midnight/50 border border-och-steel/20 p-3">
                  <span className="text-xs text-och-steel block mb-1">Interview</span>
                  <p className="text-white font-medium">
                    Score: {(application as Application).interview_score != null ? (application as Application).interview_score : '—'}
                  </p>
                  {(application as Application).interview_mentor_name && (
                    <p className="text-xs text-och-steel mt-1">By {(application as Application).interview_mentor_name}</p>
                  )}
                  {interviewNotes && (
                    <p className="text-sm text-white mt-2 pt-2 border-t border-och-steel/20 whitespace-pre-wrap">{interviewNotes}</p>
                  )}
                  {supportDocuments && (
                    <p className="text-sm text-white mt-2 pt-2 border-t border-och-steel/20 whitespace-pre-wrap">
                      Docs: {Array.isArray(supportDocuments) ? supportDocuments.join('\n') : supportDocuments}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {application.applicant_type === 'student' && hasTestAnswers && (
            <div className="space-y-3 border-t border-och-steel/20 pt-4">
              <h4 className="text-sm font-medium text-white">Application test</h4>
              <p className="text-och-steel text-xs">
                Invited:{' '}
                {application.form_data?.application_test_invited_at
                  ? new Date(application.form_data.application_test_invited_at as string).toLocaleString()
                  : '—'}
                {' · '}
                Completed:{' '}
                {application.form_data?.application_test_completed_at
                  ? new Date(application.form_data.application_test_completed_at as string).toLocaleString()
                  : '—'}
              </p>

              {typeof (application.form_data as any)?.application_test_results?.overall_score === 'number' && (
                <div className="rounded-lg border border-och-mint/30 bg-och-mint/5 p-3 space-y-2">
                  <p className="text-sm font-medium text-white">
                    Score: <span className="text-och-mint font-semibold">
                      {Math.round((application.form_data as any).application_test_results.overall_score)}%
                    </span>
                  </p>
                  {(() => {
                    const results = (application.form_data as any)?.application_test_results
                    const summary = results?.grade_summary
                    if (summary) {
                      return <p className="text-xs text-och-steel leading-relaxed">{summary}</p>
                    }
                    const perQuestion = results?.per_question as { type?: string; score?: number }[] | undefined
                    if (Array.isArray(perQuestion) && perQuestion.length > 0) {
                      const mcqTotal = perQuestion.filter((pq) => pq.type === 'mcq').length
                      const mcqCorrect = perQuestion.filter((pq) => pq.type === 'mcq' && pq.score != null && pq.score > 0).length
                      const other = perQuestion.filter((pq) => pq.type === 'scenario' || pq.type === 'behavioral').length
                      let fallback = `Multiple choice: ${mcqCorrect}/${mcqTotal} correct.`
                      if (other > 0) fallback += ' Scenario and behavioral: see per-question AI feedback below.'
                      return <p className="text-xs text-och-steel leading-relaxed">{fallback}</p>
                    }
                    return null
                  })()}
                </div>
              )}

              {onGradeTest &&
                typeof (application.form_data as any)?.application_test_results?.overall_score !== 'number' && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1 text-och-gold border-och-gold/40 hover:text-och-gold/90"
                    disabled={isGradeTestInProgress}
                    onClick={() => onGradeTest(application)}
                  >
                    <Award className="w-3.5 h-3.5" /> {isGradeTestInProgress ? 'Grading…' : 'Grade with AI'}
                  </Button>
                )}

              {loadingTestQuestions && (
                <p className="text-och-steel text-sm">Loading questions…</p>
              )}

              {!loadingTestQuestions && testQuestionsError && (
                <p className="text-och-orange text-xs">{testQuestionsError}</p>
              )}

              {!loadingTestQuestions && !testQuestionsError && testQuestions && (
                <div className="space-y-3 rounded-lg bg-och-midnight/50 border border-och-steel/20 p-3 max-h-64 overflow-y-auto">
                  {(() => {
                    const answerMap = new Map(
                      rawTestAnswers!.map((a) => [a.question_id, a.answer] as [string, string])
                    )
                    const resultsPerQuestion = (application.form_data as any)?.application_test_results?.per_question as Array<{ question_id?: string; type?: string; score?: number; max_score?: number; ai_feedback?: string }> | undefined
                    const resultByQid = new Map(
                      (resultsPerQuestion ?? []).map((pq) => [pq.question_id, pq])
                    )
                    return testQuestions.map((q, idx) => {
                      const answer = (answerMap.get(q.id) || '').trim()
                      const isMcq = q.type === 'mcq'
                      const isScenarioOrBehavioral = q.type === 'scenario' || q.type === 'behavioral'
                      const result = resultByQid.get(q.id)
                      const isCorrect =
                        isMcq &&
                        q.correct_answer &&
                        answer &&
                        answer.toLowerCase().trim() === q.correct_answer.toLowerCase().trim()
                      return (
                        <div
                          key={q.id}
                          className="rounded-md border border-och-steel/30 bg-och-midnight/70 p-3"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-xs text-och-steel mb-1">
                                Question {idx + 1} ·{' '}
                                {q.type === 'mcq'
                                  ? 'Multiple choice'
                                  : q.type === 'scenario'
                                  ? 'Scenario'
                                  : 'Behavioral'}
                              </p>
                              <p className="text-sm text-white mb-2 whitespace-pre-wrap">
                                {q.question_text}
                              </p>
                            </div>
                            {isMcq && (
                              <span
                                className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${
                                  isCorrect
                                    ? 'bg-och-mint/10 text-och-mint border border-och-mint/40'
                                    : 'bg-och-orange/10 text-och-orange border border-och-orange/40'
                                }`}
                              >
                                {answer ? (isCorrect ? 'Correct' : 'Incorrect') : 'No answer'}
                              </span>
                            )}
                            {isScenarioOrBehavioral && result?.score != null && (
                              <span className="text-xs px-2 py-0.5 rounded-full shrink-0 bg-och-mint/10 text-och-mint border border-och-mint/40">
                                Score: {typeof result.max_score === 'number' ? `${Number(result.score).toFixed(1)} / ${result.max_score}` : result.score}
                              </span>
                            )}
                          </div>

                          <div className="mt-2 space-y-1 text-xs">
                            <div>
                              <span className="text-och-steel block">Student answer</span>
                              <p className="text-white whitespace-pre-wrap">
                                {answer || '—'}
                              </p>
                            </div>
                            {isMcq && q.correct_answer && (
                              <div>
                                <span className="text-och-steel block">Correct answer</span>
                                <p className="text-och-mint whitespace-pre-wrap">
                                  {q.correct_answer}
                                </p>
                              </div>
                            )}
                            {isScenarioOrBehavioral && result?.ai_feedback && (
                              <div className="rounded border border-och-steel/20 bg-och-midnight/50 p-2 mt-1">
                                <span className="text-och-steel block">AI feedback</span>
                                <p className="text-white/90 leading-relaxed">{result.ai_feedback}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })
                  })()}
                </div>
              )}
            </div>
          )}

          {formEntries.length > 0 && (
            <div>
              <span className="text-och-steel block mb-2">Form responses</span>
              <div className="space-y-2 rounded-lg bg-och-midnight/50 border border-och-steel/20 p-4">
                {formEntries.map(([key, value]) => (
                  <div key={key}>
                    <span className="text-och-steel text-xs block">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </span>
                    <p className="text-white">{String(value)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {application.notes && (
            <div>
              <span className="text-och-steel block mb-1">Notes</span>
              <p className="text-white rounded-lg bg-och-midnight/50 border border-och-steel/20 p-3">{application.notes}</p>
            </div>
          )}

          <Link
            href={`/dashboard/director/cohorts/${application.cohort_id}`}
            className="inline-flex items-center gap-1 text-och-mint hover:underline text-sm"
          >
            View cohort <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-och-steel/20 pt-3 text-sm">
          <div className="flex flex-wrap gap-2">
            {/* Enroll: students only when eligible, sponsors always */}
            {onEnroll && (
              <Button
                variant="defender"
                size="sm"
                onClick={() => onEnroll(application)}
                disabled={
                  application.applicant_type === 'student' &&
                  application.enrollment_status !== 'eligible'
                }
                className="gap-1"
              >
                <UserCheck className="w-3.5 h-3.5" />
                {application.applicant_type === 'student' ? 'Enroll student' : 'Enroll sponsor'}
              </Button>
            )}
            {onReject && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onReject(application)}
                className="gap-1 text-och-orange border-och-orange/40"
              >
                Reject
              </Button>
            )}
            {/* System-sent acceptance + credentials email (only when enrolled) */}
            {onSendCredentials && application.email && application.enrollment_status === 'enrolled' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSendCredentials(application)}
                className="gap-1 text-och-mint border-och-mint/40"
              >
                <UserPlus className="w-3.5 h-3.5" />
                Send acceptance email
              </Button>
            )}
          </div>
          {application.enrollment_status === 'enrolled' && application.email && (
            <span className="text-xs text-och-steel">
              Credentials can be set up via the acceptance email (includes password link).
            </span>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

function AssignToMentorModal({
  open,
  onOpenChange,
  mentors,
  selectedCount,
  cohortName,
  onAssign,
  assigning,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  mentors: MentorAssignment[]
  selectedCount: number
  cohortName: string
  onAssign: (mentorId: number) => Promise<void>
  assigning: boolean
}) {
  const [selectedMentorId, setSelectedMentorId] = useState<number | ''>('')
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md border-och-steel/20 bg-och-midnight">
        <DialogHeader>
          <DialogTitle className="text-white">Assign to mentor for review</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 text-sm">
          <p className="text-och-steel">
            Assign <span className="text-white font-medium">{selectedCount}</span> student(s) to a mentor. Select a mentor assigned to <span className="text-och-mint">{cohortName}</span>:
          </p>
          {mentors.length === 0 ? (
            <p className="text-och-orange">No mentors assigned to this cohort. Assign mentors in the cohort page first.</p>
          ) : (
            <select
              value={selectedMentorId}
              onChange={(e) => setSelectedMentorId(e.target.value ? Number(e.target.value) : '')}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white"
            >
              <option value="">Select mentor</option>
              {mentors.map((m) => {
                const mentorId = typeof m.mentor === 'object' ? m.mentor?.id : m.mentor
                const name = m.mentor_name || (typeof m.mentor === 'object' ? (m.mentor?.first_name || m.mentor?.last_name ? `${m.mentor.first_name || ''} ${m.mentor.last_name || ''}`.trim() : m.mentor?.email) : m.mentor_email)
                return (
                  <option key={m.id} value={mentorId}>{name || m.mentor_email || String(mentorId)}</option>
                )
              })}
            </select>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button
              variant="defender"
              disabled={!selectedMentorId || mentors.length === 0 || assigning}
              onClick={() => selectedMentorId && onAssign(selectedMentorId)}
            >
              {assigning ? 'Assigning...' : 'Assign'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

interface AppQuestionItem {
  id: string
  type: 'mcq' | 'scenario' | 'behavioral'
  question_text: string
  options: string[]
  correct_answer: string
  scoring_weight: number
}

const DEFAULT_QUESTION: Omit<AppQuestionItem, 'id'> = {
  type: 'mcq',
  question_text: '',
  options: ['', '', ''],
  correct_answer: '',
  scoring_weight: 1,
}

function ApplicationQuestionsTab({ cohorts }: { cohorts: Cohort[] }) {
  const [showSetModal, setShowSetModal] = useState(false)
  const [selectedCohortId, setSelectedCohortId] = useState<string | null>(null)
  const [selectedCohortName, setSelectedCohortName] = useState<string>('')
  const [hasQuestions, setHasQuestions] = useState<Record<string, boolean>>({})
  const [showEditorModal, setShowEditorModal] = useState(false)
  const [editorMode, setEditorMode] = useState<'manual' | 'ai'>('manual')
  const [cohortTracks, setCohortTracks] = useState<string[]>([])
  const [aiGenerating, setAiGenerating] = useState(false)
  const [timeLimitMinutes, setTimeLimitMinutes] = useState(60)
  const [testDate, setTestDate] = useState('')
  const [questions, setQuestions] = useState<AppQuestionItem[]>([])
  const [saving, setSaving] = useState(false)
  const [showAiAddModal, setShowAiAddModal] = useState(false)
  const [aiAddType, setAiAddType] = useState<'logical' | 'critical' | 'track' | 'behavioral'>('logical')

  // On mount / when cohorts are loaded, fetch summary from backend so ticks persist after refresh
  useEffect(() => {
    if (!cohorts.length) return
    ;(async () => {
      try {
        const res = await apiGateway.get('/director/application-questions/') as any
        const data = res as { cohorts?: { cohort_id: string; question_count?: number }[] }
        const next: Record<string, boolean> = {}
        ;(data.cohorts || []).forEach((item) => {
          next[item.cohort_id] = (item.question_count ?? 0) > 0
        })
        setHasQuestions(next)
      } catch (err) {
      }
    })()
  }, [cohorts.length])

  const handleSet = (cohortId: string) => {
    const cohort = cohorts.find((c) => c.id === cohortId)
    setSelectedCohortId(cohortId)
    setSelectedCohortName(cohort?.name ?? '')
    setShowSetModal(true)
  }

  const openEditor = (mode: 'manual' | 'ai') => {
    setEditorMode(mode)
    setShowSetModal(false)
    if (mode === 'manual') {
      setQuestions([{ ...DEFAULT_QUESTION, id: crypto.randomUUID() }])
      setTimeLimitMinutes(60)
      setTestDate('')
      setShowEditorModal(true)
    } else {
      setAiGenerating(true)
      setShowEditorModal(true)
      setQuestions([])
      setTimeLimitMinutes(60)
      setTestDate('')
      // Fetch cohort tracks for better prompts
      apiGateway
        .get(`/cohorts/${selectedCohortId}/`)
        .then((cohort: unknown) => {
          const c = cohort as { curriculum_tracks?: string[]; name?: string }
          const tracks = c?.curriculum_tracks ?? []
          if (Array.isArray(tracks)) {
            setCohortTracks(tracks as string[])
          } else {
            setCohortTracks([])
          }
          return c
        })
        .catch(() => ({ name: selectedCohortName, curriculum_tracks: [] }))
        .then(async (c: any) => {
          try {
            const ai = await fastapiApi.generateApplicationQuestions({
              cohort_id: selectedCohortId!,
              cohort_name: c?.name,
              tracks: c?.curriculum_tracks ?? [],
              categories: ['logical', 'critical', 'track', 'behavioral'],
              count: 4,
            })
            const mapped: AppQuestionItem[] = ai.questions.map((q) => ({
              id: crypto.randomUUID(),
              type: q.type as AppQuestionItem['type'],
              question_text: q.question_text,
              options: q.options || [],
              correct_answer: q.correct_answer || '',
              scoring_weight: q.scoring_weight ?? 1,
            }))
            setQuestions(mapped)
          } catch (err) {
            toast.error('AI question generation failed. Check AI service configuration.')
            setQuestions([{ ...DEFAULT_QUESTION, id: crypto.randomUUID() }])
          } finally {
            setAiGenerating(false)
          }
        })
    }
  }

  const addQuestion = () => {
    if (editorMode === 'manual') {
      setQuestions((q) => [...q, { ...DEFAULT_QUESTION, id: crypto.randomUUID() }])
    } else {
      setAiAddType('logical')
      setShowAiAddModal(true)
    }
  }

  const addAiGeneratedQuestion = () => {
    if (!selectedCohortId) {
      setShowAiAddModal(false)
      return
    }
    ;(async () => {
      try {
        const categories =
          aiAddType === 'behavioral'
            ? ['behavioral']
            : aiAddType === 'critical'
            ? ['critical']
            : aiAddType === 'track'
            ? ['track']
            : ['logical']
        const ai = await fastapiApi.generateApplicationQuestions({
          cohort_id: selectedCohortId,
          cohort_name: selectedCohortName,
          tracks: cohortTracks,
          categories,
          count: 1,
        })
        const mapped: AppQuestionItem[] = ai.questions.map((q) => ({
          id: crypto.randomUUID(),
          type: q.type as AppQuestionItem['type'],
          question_text: q.question_text,
          options: q.options || [],
          correct_answer: q.correct_answer || '',
          scoring_weight: q.scoring_weight ?? 1,
        }))
        setQuestions((prev) => [...prev, ...mapped])
      } catch (err) {
        toast.error('AI could not generate a new question.')
      } finally {
        setShowAiAddModal(false)
      }
    })()
    setShowAiAddModal(false)
  }

  const updateQuestion = (id: string, field: keyof AppQuestionItem, value: string | number | string[]) => {
    setQuestions((q) => q.map((x) => (x.id === id ? { ...x, [field]: value } : x)))
  }

  const removeQuestion = (id: string) => {
    setQuestions((q) => q.filter((x) => x.id !== id))
  }

  const handleSaveQuestions = async () => {
    if (!selectedCohortId) return
    setSaving(true)
    try {
      await apiGateway.post('/director/application-questions/', {
        cohort_id: selectedCohortId,
        time_limit_minutes: timeLimitMinutes,
        test_date: testDate || null,
        questions: questions.map(({ type, question_text, options, correct_answer, scoring_weight }) => ({ type, question_text, options, correct_answer, scoring_weight })),
      })
      setHasQuestions((p) => ({ ...p, [selectedCohortId]: true }))
      setShowEditorModal(false)
      toast.success('Application questions saved.')
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? (e as Error)?.message ?? 'Save failed'
      toast.error(msg)
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = async (cohortId: string) => {
    const cohort = cohorts.find((c) => c.id === cohortId)
    setSelectedCohortId(cohortId)
    setSelectedCohortName(cohort?.name ?? '')
    try {
      const res = await apiGateway.get('/director/application-questions/', {
        params: { cohort_id: cohortId },
      }) as any
      const data = res as {
        time_limit_minutes?: number
        opens_at?: string | null
        questions?: Array<{
          id: string
          type: 'mcq' | 'scenario' | 'behavioral'
          question_text: string
          options?: string[]
          correct_answer?: string
          scoring_weight?: number
        }>
      }
      const loadedQuestions: AppQuestionItem[] = (data.questions || []).map((q) => ({
        id: q.id,
        type: q.type,
        question_text: q.question_text,
        options: q.options || [],
        correct_answer: q.correct_answer || '',
        scoring_weight: q.scoring_weight ?? 1,
      }))
      if (loadedQuestions.length > 0) {
        setQuestions(loadedQuestions)
        setHasQuestions((prev) => ({ ...prev, [cohortId]: true }))
      } else {
        setQuestions([{ ...DEFAULT_QUESTION, id: crypto.randomUUID() }])
      }
      setEditorMode('manual')
      setTimeLimitMinutes(data.time_limit_minutes ?? 60)
      // Convert ISO datetime to datetime-local input value
      const opensAt = data.opens_at
      setTestDate(opensAt ? opensAt.slice(0, 16).replace(' ', 'T') : '')
      setShowEditorModal(true)
    } catch (err) {
      // Fallback: open manual editor with empty question
      setQuestions([{ ...DEFAULT_QUESTION, id: crypto.randomUUID() }])
      setEditorMode('manual')
      setTimeLimitMinutes(60)
      setTestDate('')
      setShowEditorModal(true)
    }
  }

  return (
    <Card className="border-och-steel/20">
      <div className="p-4">
        <h3 className="text-lg font-semibold text-white mb-1">Application Questions by Cohort</h3>
        <p className="text-sm text-och-steel mb-4">
          Set or edit application test questions per cohort. Once set, applicants can be sent the application test.
        </p>
        {cohorts.length === 0 ? (
          <div className="py-8 text-center text-och-steel">No cohorts found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-och-steel/20">
                  <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Cohort</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Questions set</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-och-steel">Action</th>
                </tr>
              </thead>
              <tbody>
                {cohorts.map((c) => (
                  <tr key={c.id} className="border-b border-och-steel/10 hover:bg-och-midnight/30">
                    <td className="py-3 px-4 text-white font-medium">{c.name}</td>
                    <td className="py-3 px-4">
                      {hasQuestions[c.id] ? (
                        <span className="text-och-mint inline-flex items-center gap-1">✓ Set</span>
                      ) : (
                        <span className="text-och-steel">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {hasQuestions[c.id] ? (
                        <Button variant="outline" size="sm" onClick={() => handleEdit(c.id)}>Edit</Button>
                      ) : (
                        <Button variant="defender" size="sm" onClick={() => handleSet(c.id)}>Set</Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Dialog open={showSetModal} onOpenChange={setShowSetModal}>
        <DialogContent className="max-w-sm border-och-steel/20 bg-och-midnight">
          <DialogHeader>
            <DialogTitle className="text-white">Set application questions</DialogTitle>
          </DialogHeader>
          <p className="text-och-steel text-sm mb-4">
            How would you like to set the questions?
          </p>
          <div className="flex gap-3">
            <Button
              type="button"
              variant="defender"
              size="sm"
              className="flex-1"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                openEditor('manual')
              }}
            >
              Set manually
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                openEditor('ai')
              }}
            >
              AI setting
            </Button>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button
              type="button"
              variant="outline"
              onClick={(e) => {
                e.preventDefault()
                setShowSetModal(false)
              }}
            >
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={showEditorModal} onOpenChange={setShowEditorModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col border-och-steel/20 bg-och-midnight">
          <DialogHeader>
            <DialogTitle className="text-white">
              {editorMode === 'ai' ? 'AI-generated questions' : 'Set questions manually'} — {selectedCohortName}
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {aiGenerating ? (
              <div className="py-8 text-center text-och-steel">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-och-mint mx-auto mb-3" />
                <p>AI is generating questions for this cohort…</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-och-steel mb-1">Time limit (minutes)</label>
                    <input
                      type="number"
                      min={5}
                      max={180}
                      value={timeLimitMinutes}
                      onChange={(e) => setTimeLimitMinutes(Number(e.target.value) || 60)}
                      className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-och-steel mb-1">Application test date & time</label>
                    <input
                      type="datetime-local"
                      value={testDate}
                      onChange={(e) => setTestDate(e.target.value)}
                      className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm"
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-white">Questions</label>
                    <Button variant="outline" size="sm" onClick={addQuestion}>Add question</Button>
                  </div>
                  <div className="space-y-4">
                    {questions.map((q, idx) => (
                      <div key={q.id} className="rounded-lg border border-och-steel/20 p-4 bg-och-midnight/50">
                        <div className="flex justify-between items-start gap-2 mb-2">
                          <span className="text-xs text-och-steel">Question {idx + 1}</span>
                          <Button variant="ghost" size="sm" className="text-och-orange hover:text-och-orange" onClick={() => removeQuestion(q.id)}>Remove</Button>
                        </div>
                        <select
                          value={q.type}
                          onChange={(e) => updateQuestion(q.id, 'type', e.target.value as AppQuestionItem['type'])}
                          className="w-full mb-2 px-3 py-2 bg-och-midnight border border-och-steel/30 rounded text-white text-sm"
                        >
                          <option value="mcq">MCQ</option>
                          <option value="scenario">Scenario</option>
                          <option value="behavioral">Behavioral</option>
                        </select>
                        <textarea
                          placeholder="Question text"
                          value={q.question_text}
                          onChange={(e) => updateQuestion(q.id, 'question_text', e.target.value)}
                          className="w-full mb-2 px-3 py-2 bg-och-midnight border border-och-steel/30 rounded text-white text-sm min-h-[60px]"
                          rows={2}
                        />
                        {q.type === 'mcq' && (
                          <div className="space-y-1 mb-2">
                            {q.options.map((opt, i) => (
                              <input
                                key={i}
                                type="text"
                                placeholder={`Option ${i + 1}`}
                                value={opt}
                                onChange={(e) => {
                                  const next = [...q.options]
                                  next[i] = e.target.value
                                  updateQuestion(q.id, 'options', next)
                                }}
                                className="w-full px-3 py-1.5 bg-och-midnight border border-och-steel/30 rounded text-white text-sm"
                              />
                            ))}
                            <input
                              type="text"
                              placeholder="Correct answer (must match an option)"
                              value={q.correct_answer}
                              onChange={(e) => updateQuestion(q.id, 'correct_answer', e.target.value)}
                              className="w-full px-3 py-1.5 bg-och-midnight border border-och-steel/30 rounded text-white text-sm"
                            />
                          </div>
                        )}
                        <input
                          type="number"
                          step={0.1}
                          min={0}
                          placeholder="Scoring weight"
                          value={q.scoring_weight || ''}
                          onChange={(e) => updateQuestion(q.id, 'scoring_weight', Number(e.target.value) || 1)}
                          className="w-24 px-2 py-1 bg-och-midnight border border-och-steel/30 rounded text-white text-sm"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
          {!aiGenerating && (
            <div className="flex justify-end gap-2 mt-4 pt-4 border-t border-och-steel/20">
              <Button variant="outline" onClick={() => setShowEditorModal(false)}>Cancel</Button>
              <Button variant="defender" disabled={saving || questions.length === 0} onClick={handleSaveQuestions}>
                {saving ? 'Saving…' : 'Save'}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* AI add-question type selector (only used in AI mode) */}
      <Dialog open={showAiAddModal} onOpenChange={setShowAiAddModal}>
        <DialogContent className="max-w-sm border-och-steel/20 bg-och-midnight">
          <DialogHeader>
            <DialogTitle className="text-white">Add AI-generated question</DialogTitle>
          </DialogHeader>
          <p className="text-och-steel text-sm mb-3">
            What type of question would you like to add?
          </p>
          <div className="flex flex-col gap-2 text-sm">
            <button
              type="button"
              onClick={() => setAiAddType('logical')}
              className={`text-left px-3 py-2 rounded border ${aiAddType === 'logical' ? 'border-och-mint text-white' : 'border-och-steel/40 text-och-steel'}`}
            >
              Logical & analytical
            </button>
            <button
              type="button"
              onClick={() => setAiAddType('critical')}
              className={`text-left px-3 py-2 rounded border ${aiAddType === 'critical' ? 'border-och-mint text-white' : 'border-och-steel/40 text-och-steel'}`}
            >
              Critical thinking / scenario
            </button>
            <button
              type="button"
              onClick={() => setAiAddType('track')}
              className={`text-left px-3 py-2 rounded border ${aiAddType === 'track' ? 'border-och-mint text-white' : 'border-och-steel/40 text-och-steel'}`}
              disabled={cohortTracks.length === 0}
            >
              Cohort track-based {cohortTracks.length === 0 && '(tracks not available)'}
            </button>
            <button
              type="button"
              onClick={() => setAiAddType('behavioral')}
              className={`text-left px-3 py-2 rounded border ${aiAddType === 'behavioral' ? 'border-och-mint text-white' : 'border-och-steel/40 text-och-steel'}`}
            >
              Behavioral
            </button>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowAiAddModal(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="defender"
              onClick={addAiGeneratedQuestion}
            >
              Generate question
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  )
}

function InterviewQuestionsTab({ cohorts }: { cohorts: Cohort[] }) {
  const [hasQuestions, setHasQuestions] = useState<Record<string, boolean>>({})

  return (
    <Card className="border-och-steel/20">
      <div className="p-4">
        <h3 className="text-lg font-semibold text-white mb-1">Interview Questions by Cohort</h3>
        <p className="text-sm text-och-steel mb-4">
          Set or edit interview questions per cohort. Mentors assigned to the cohort will see these when conducting interviews (after application test pass).
        </p>
        {cohorts.length === 0 ? (
          <div className="py-8 text-center text-och-steel">No cohorts found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-och-steel/20">
                  <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Cohort</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Questions set</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-och-steel">Action</th>
                </tr>
              </thead>
              <tbody>
                {cohorts.map((c) => (
                  <tr key={c.id} className="border-b border-och-steel/10 hover:bg-och-midnight/30">
                    <td className="py-3 px-4 text-white font-medium">{c.name}</td>
                    <td className="py-3 px-4">
                      {hasQuestions[c.id] ? <span className="text-och-mint">✓ Set</span> : <span className="text-och-steel">—</span>}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {hasQuestions[c.id] ? (
                        <Button variant="outline" size="sm">Edit</Button>
                      ) : (
                        <Button variant="defender" size="sm">Set</Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Card>
  )
}

function GradesTab({
  cohorts,
  applications,
  cohortFilter,
  setCohortFilter,
  loading,
}: {
  cohorts: Cohort[]
  applications: Application[]
  cohortFilter: string
  setCohortFilter: (v: string) => void
  loading: boolean
}) {
  const studentApps = useMemo(() => applications.filter((a) => a.applicant_type === 'student'), [applications])
  const passedReview = useMemo(() => studentApps.filter((a) => (a as Application).review_status === 'passed'), [studentApps])
  const failedReview = useMemo(() => studentApps.filter((a) => (a as Application).review_status === 'failed'), [studentApps])
  const eligible = useMemo(() => studentApps.filter((a) => (a as Application).enrollment_status === 'eligible'), [studentApps])

  return (
    <div className="space-y-6">
      <Card className="border-och-steel/20 p-4">
        <h3 className="text-lg font-semibold text-white mb-2">Passing grades (thresholds)</h3>
        <p className="text-sm text-och-steel mb-4">
          Set minimum passing scores per cohort for application test and interview. Use the cohort filter below to view pass/fail by cohort.
        </p>
        <div className="flex flex-wrap items-center gap-4">
          <label className="text-och-steel text-sm">Cohort</label>
          <select
            value={cohortFilter}
            onChange={(e) => setCohortFilter(e.target.value)}
            className="px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm"
          >
            <option value="">All cohorts</option>
            {cohorts.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <Button variant="outline" size="sm">Set application threshold</Button>
          <Button variant="outline" size="sm">Set interview threshold</Button>
        </div>
      </Card>

      <Card className="border-och-steel/20 overflow-hidden">
        <div className="p-4 border-b border-och-steel/20">
          <h3 className="text-lg font-semibold text-white">Pass / Fail by cohort</h3>
          <p className="text-sm text-och-steel">Filter by cohort above to see applicants who passed or failed application review or interview.</p>
        </div>
        {loading ? (
          <div className="p-8 text-center text-och-steel">Loading applications...</div>
        ) : !cohortFilter ? (
          <div className="p-8 text-center text-och-steel">Select a cohort to see passed/failed applicants.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4">
            <div className="rounded-lg bg-och-midnight/50 border border-och-steel/20 p-4">
              <p className="text-xs text-och-steel mb-1">Passed application review</p>
              <p className="text-2xl font-bold text-och-mint">{passedReview.length}</p>
            </div>
            <div className="rounded-lg bg-och-midnight/50 border border-och-steel/20 p-4">
              <p className="text-xs text-och-steel mb-1">Failed application review</p>
              <p className="text-2xl font-bold text-och-orange">{failedReview.length}</p>
            </div>
            <div className="rounded-lg bg-och-midnight/50 border border-och-steel/20 p-4">
              <p className="text-xs text-och-steel mb-1">Eligible to enroll</p>
              <p className="text-2xl font-bold text-och-defender">{eligible.length}</p>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}

type ApplicationsTab = 'applicants' | 'application-questions' | 'interview-questions' | 'grades'

function ApplicationsContent() {
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState<ApplicationsTab>('applicants')
  const [applications, setApplications] = useState<Application[]>([])
  const [cohorts, setCohorts] = useState<Cohort[]>([])
  const [loading, setLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [cohortFilter, setCohortFilter] = useState<string>('')
  const [applicantTypeFilter, setApplicantTypeFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [reviewStatusFilter, setReviewStatusFilter] = useState<string>('')
  const [enrollmentStatusFilter, setEnrollmentStatusFilter] = useState<string>('')
  const [mentorFilter, setMentorFilter] = useState<string>('')
  const [selectedApp, setSelectedApp] = useState<Application | null>(null)
  const [selectedIdsSet, setSelectedIdsSet] = useState<Set<string>>(new Set())
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [mentors, setMentors] = useState<MentorAssignment[]>([])
  const [assigning, setAssigning] = useState(false)
  const [showCutoffModal, setShowCutoffModal] = useState<'review' | 'interview' | null>(null)
  const [cutoffGrade, setCutoffGrade] = useState('')
  const [settingCutoff, setSettingCutoff] = useState(false)
  const [showEnrollModal, setShowEnrollModal] = useState(false)
  const [enrolling, setEnrolling] = useState(false)
  const [enrollingSingleId, setEnrollingSingleId] = useState<string | null>(null)
  const [actionMenuAppId, setActionMenuAppId] = useState<string | null>(null)
  const [sendingTestIds, setSendingTestIds] = useState<Set<string>>(new Set())
  const [gradingTestIds, setGradingTestIds] = useState<Set<string>>(new Set())
  useEffect(() => {
    const cohortId = searchParams.get('cohort_id') || ''
    setCohortFilter(cohortId)
  }, [searchParams])

  useEffect(() => {
    fetchCohorts()
  }, [])

  useEffect(() => {
    if (activeTab === 'applicants' || activeTab === 'grades') {
      fetchApplications()
    }
  }, [activeTab, cohortFilter, applicantTypeFilter, statusFilter, reviewStatusFilter, enrollmentStatusFilter, mentorFilter])

  const studentApps = useMemo(() => applications.filter((a) => a.applicant_type === 'student'), [applications])
  const mentorOptions = useMemo(() => {
    if (mentors.length > 0) return mentors
    const seen = new Map<number, MentorAssignment>()
    studentApps.forEach((a) => {
      const id = (a as Application).reviewer_mentor_id
      if (id != null && !seen.has(id)) {
        const name = (a as Application).reviewer_mentor_name || `Mentor ${id}`
        seen.set(id, { id: String(id), mentor: id, mentor_name: name } as MentorAssignment)
      }
    })
    return Array.from(seen.values())
  }, [mentors, studentApps])

  useEffect(() => {
    if (cohortFilter) fetchMentors(cohortFilter)
    else setMentors([])
  }, [cohortFilter])
  const kpis = useMemo(() => ({
    total: studentApps.length,
    pending: studentApps.filter((a) => (a as Application).review_status === 'pending' || !(a as Application).review_status).length,
    reviewed: studentApps.filter((a) => (a as Application).review_status === 'reviewed').length,
    passed: studentApps.filter((a) => (a as Application).review_status === 'passed').length,
    failed: studentApps.filter((a) => (a as Application).review_status === 'failed').length,
    eligible: studentApps.filter((a) => (a as Application).enrollment_status === 'eligible').length,
  }), [studentApps])
  const unassignedStudentApps = useMemo(() => studentApps.filter((a) => !(a as any).reviewer_mentor_id), [studentApps])
  const selectedIds = useMemo(() => Array.from(selectedIdsSet), [selectedIdsSet])

  const toggleSelected = (appId: string, isStudent: boolean) => {
    if (!isStudent) return
    setSelectedIdsSet((prev) => {
      const next = new Set(prev)
      if (next.has(appId)) next.delete(appId)
      else next.add(appId)
      return next
    })
  }

  const toggleSelectAllStudents = () => {
    if (selectedIdsSet.size >= studentApps.length) {
      setSelectedIdsSet(new Set())
    } else {
      setSelectedIdsSet(new Set(studentApps.map((a) => a.id)))
    }
  }

  const fetchMentors = async (cohortId: string) => {
    try {
      const list = await programsClient.getCohortMentors(cohortId)
      setMentors(Array.isArray(list) ? list : [])
    } catch {
      setMentors([])
    }
  }

  const fetchCohorts = async () => {
    try {
      const res = await apiGateway.get<{ data?: Cohort[]; results?: Cohort[] }>('/cohorts/')
      const data = res as any
      const list = data?.data ?? data?.results ?? data ?? []
      setCohorts(Array.isArray(list) ? list : [])
    } catch {
      setCohorts([])
    }
  }

  const fetchApplications = async (): Promise<Application[]> => {
    setLoading(true)
    setFetchError(null)
    try {
      const params: Record<string, string> = {}
      if (cohortFilter) params.cohort_id = cohortFilter
      if (applicantTypeFilter) params.applicant_type = applicantTypeFilter
      if (statusFilter) params.status = statusFilter
      if (reviewStatusFilter) params.review_status = reviewStatusFilter
      if (enrollmentStatusFilter) params.enrollment_status = enrollmentStatusFilter
      if (mentorFilter) params.reviewer_mentor_id = mentorFilter
      const res = await apiGateway.get<{ applications: Application[] }>(
        '/director/public-applications/',
        { params }
      )
      const data = res as any
      const list = data?.applications ?? []
      setApplications(list)
      return list
    } catch (err: unknown) {
      setApplications([])
      const status = (err as { status?: number })?.status
      const msg = (err as { message?: string })?.message
      if (status === 403) {
        setFetchError('You do not have permission to view applications. Directors and admins only.')
      } else if (status === 404) {
        setFetchError('Applications endpoint not found. Please ensure the backend is up to date.')
      } else {
        setFetchError(msg ? `Failed to load: ${msg}` : 'Failed to load applications. Please try again.')
      }
      return []
    } finally {
      setLoading(false)
    }
  }

  const getStatusVariant = (s: string) => {
    if (s === 'approved' || s === 'converted') return 'defender'
    if (s === 'rejected') return 'orange'
    return 'steel'
  }
  const getApplicationStatusLabel = (s: string, app?: Application) => {
    const map: Record<string, string> = {
      approved: 'Approved',
      rejected: 'Rejected',
      converted: 'Converted',
    }
    if (s !== 'pending') return map[s] || s

    // For pending applications, derive a richer status from application test state
    const fd: any = (app as any)?.form_data || {}
    const invitedAt = fd.application_test_invited_at
    const completedAt = fd.application_test_completed_at
    const results = fd.application_test_results
    const hasScore = results && typeof results.overall_score === 'number'

    if (invitedAt && !completedAt) {
      return 'Application email sent'
    }

    if (completedAt && !hasScore) {
      return 'Application test submitted, waiting grading'
    }

    if (completedAt && hasScore) {
      return 'Application test graded'
    }

    return 'Submitted'
  }

  const getStatusBadgeClass = (label: string) => {
    if (label === 'Application test submitted, waiting grading') {
      return 'bg-och-gold/10 text-och-gold border border-och-gold/40 whitespace-nowrap'
    }
    return 'whitespace-nowrap'
  }

  const handleOpenAssignModal = () => {
    const cohortId = cohortFilter || (selectedIds.length ? (applications.find((a) => a.id === selectedIds[0])?.cohort_id) : null)
    if (cohortId) fetchMentors(cohortId)
    setShowAssignModal(true)
  }

  const handleAssign = async (mentorId: number) => {
    setAssigning(true)
    try {
      await apiGateway.post('/director/public-applications/assign-to-mentor/', {
        application_ids: selectedIds,
        mentor_id: mentorId,
      })
      setSelectedAnchorIdx(null)
      setSelectCount('')
      setShowAssignModal(false)
      fetchApplications()
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to assign')
    } finally {
      setAssigning(false)
    }
  }

  const cohortName = cohortFilter ? (cohorts.find((c) => c.id === cohortFilter)?.name || 'cohort') : (applications[0]?.cohort_name || 'cohort')

  const eligibleToEnroll = useMemo(
    () => studentApps.filter((a) => (a as Application).enrollment_status === 'eligible'),
    [studentApps]
  )

  const handleSetCutoff = async (phase: 'review' | 'interview') => {
    const cohortId = cohortFilter || applications[0]?.cohort_id
    if (!cohortId) return
    const val = parseFloat(cutoffGrade)
    if (isNaN(val) || val < 0 || val > 100) {
      alert('Grade must be 0-100')
      return
    }
    setSettingCutoff(true)
    try {
      const endpoint = phase === 'review' ? '/director/public-applications/set-review-cutoff/' : '/director/public-applications/set-interview-cutoff/'
      const res = await apiGateway.post<{ eligible_count?: number; passed_count?: number; failed_count?: number; graded_count?: number }>(endpoint, { cohort_id: cohortId, cutoff_grade: val })
      setShowCutoffModal(null)
      setCutoffGrade('')
      fetchApplications()
      const data = res as { eligible_count?: number; passed_count?: number; failed_count?: number; graded_count?: number }
      if (phase === 'review') {
        const passed = data?.passed_count ?? 0
        const failed = data?.failed_count ?? 0
        alert(`Review cutoff set. ${passed} passed, ${failed} failed.`)
      } else {
        const eligible = data?.eligible_count ?? 0
        const graded = data?.graded_count ?? 0
        if (eligible > 0) {
          alert(`${eligible} application(s) are now eligible for enrollment.`)
        } else if (graded === 0) {
          alert('Cutoff set. No applications had graded interviews yet — mentors must grade interviews first (mentor dashboard → Application Review).')
        } else {
          alert(`Cutoff set. ${graded} application(s) did not meet the cutoff and were marked as failed.`)
        }
      }
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed')
    } finally {
      setSettingCutoff(false)
    }
  }

  const handleEnroll = async () => {
    const ids = eligibleToEnroll.map((a) => a.id)
    if (!ids.length) return
    setEnrolling(true)
    try {
      await apiGateway.post('/director/public-applications/enroll/', { application_ids: ids })
      setShowEnrollModal(false)
      fetchApplications()
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to enroll')
    } finally {
      setEnrolling(false)
    }
  }

  const handleEnrollSingle = async (app: Application) => {
    setEnrollingSingleId(app.id)
    try {
      await apiGateway.post('/director/public-applications/enroll/', { application_ids: [app.id] })
      fetchApplications()
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to enroll application')
    } finally {
      setEnrollingSingleId(null)
    }
  }

  const handleRejectSingle = async (app: Application) => {
    try {
      await apiGateway.post('/director/public-applications/reject/', { application_id: app.id })
      fetchApplications()
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to reject application')
    }
  }

  const handleDeleteSingle = async (app: Application) => {
    try {
      await apiGateway.post('/director/public-applications/delete/', { application_ids: [app.id] })
      if (selectedApp?.id === app.id) setSelectedApp(null)
      setSelectedIdsSet((prev) => {
        const next = new Set(prev)
        next.delete(app.id)
        return next
      })
      fetchApplications()
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to delete application')
    }
  }

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return
    if (!confirm(`Permanently remove ${selectedIds.length} selected application(s)? This cannot be undone.`)) return
    try {
      await apiGateway.post('/director/public-applications/delete/', { application_ids: [...selectedIds] })
      setSelectedIdsSet(new Set())
      if (selectedApp && selectedIds.includes(selectedApp.id)) setSelectedApp(null)
      fetchApplications()
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to delete some applications')
    }
  }

  const handleSendCredentials = async (app: Application) => {
    if (!app.email) return
    try {
      await apiGateway.post('/director/public-applications/send-credentials/', {
        application_id: app.id,
      })
      alert('Acceptance email with credentials link has been sent.')
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to send credentials')
    }
  }

  const handleSendApplicationTest = async (ids: string[]) => {
    if (!ids.length) return
    setSendingTestIds((prev) => new Set([...prev, ...ids]))
    try {
      await apiGateway.post('/director/public-applications/send-test/', {
        application_ids: ids,
      })
      setSelectedIdsSet((prev) => {
        const next = new Set(prev)
        ids.forEach((id) => next.delete(id))
        return next
      })
      fetchApplications()
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to send application test')
    } finally {
      setSendingTestIds((prev) => {
        const next = new Set(prev)
        ids.forEach((id) => next.delete(id))
        return next
      })
    }
  }

  const handleGradeWithAI = async (ids: string[]) => {
    if (!ids.length) return
    setGradingTestIds((prev) => new Set([...prev, ...ids]))
    try {
      const res = await apiGateway.post<{ success?: boolean; graded_count?: number }>(
        '/director/public-applications/grade-test/',
        { application_ids: ids }
      )
      const gradedCount = (res as any)?.graded_count ?? 0
      const list = await fetchApplications()
      if (ids.length === 1 && selectedApp?.id === ids[0]) {
        const updated = list.find((a) => a.id === ids[0])
        if (updated) setSelectedApp(updated)
      }
      setSelectedIdsSet((prev) => {
        const next = new Set(prev)
        ids.forEach((id) => next.delete(id))
        return next
      })
      if (gradedCount === 0) {
        alert('No applications were graded. Each application must have submitted test answers and a cohort with questions configured.')
      }
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to grade application test')
    } finally {
      setGradingTestIds((prev) => {
        const next = new Set(prev)
        ids.forEach((id) => next.delete(id))
        return next
      })
    }
  }

  const selectedIdsWithNoGrade = useMemo(() => {
    return selectedIds.filter((id) => {
      const app = applications.find((a) => a.id === id)
      if (!app || app.applicant_type !== 'student') return false
      const fd = (app as any).form_data || {}
      const hasAnswers = Array.isArray(fd.application_test_answers) && fd.application_test_answers.length > 0
      const hasGrade = typeof fd.application_test_results?.overall_score === 'number'
      return hasAnswers && !hasGrade
    })
  }, [selectedIds, applications])

  return (
    <RouteGuard requiredRoles={['program_director', 'admin']}>
      <DirectorLayout>
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-white mb-2">Applications</h1>
            <p className="text-och-steel">
              Student and sponsor applications from the homepage. Manage application questions, interview questions, and grades by cohort.
            </p>
          </div>

          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as ApplicationsTab)} className="mb-6">
            <TabsList className="bg-och-midnight/80 border border-och-steel/20">
              <TabsTrigger value="applicants" className="gap-2 data-[state=active]:bg-och-defender/20 data-[state=active]:text-och-mint">
                <Users className="w-4 h-4" /> Applicants
              </TabsTrigger>
              <TabsTrigger value="application-questions" className="gap-2 data-[state=active]:bg-och-defender/20 data-[state=active]:text-och-mint">
                <FileQuestion className="w-4 h-4" /> Application Questions
              </TabsTrigger>
              <TabsTrigger value="interview-questions" className="gap-2 data-[state=active]:bg-och-defender/20 data-[state=active]:text-och-mint">
                <MessageSquare className="w-4 h-4" /> Interview Questions
              </TabsTrigger>
              <TabsTrigger value="grades" className="gap-2 data-[state=active]:bg-och-defender/20 data-[state=active]:text-och-mint">
                <Gauge className="w-4 h-4" /> Grades
              </TabsTrigger>
            </TabsList>

            <TabsContent value="applicants" className="mt-6">
          {/* KPI Cards */}
          {!loading && studentApps.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
              <Card className="p-4 border-och-steel/20">
                <p className="text-xs text-och-steel mb-1">Total applications</p>
                <p className="text-2xl font-bold text-white">{kpis.total}</p>
              </Card>
              <Card className="p-4 border-och-steel/20">
                <p className="text-xs text-och-steel mb-1">Awaiting mentor review</p>
                <p className="text-sm text-och-steel/80 mb-0.5">Not yet graded</p>
                <p className="text-2xl font-bold text-och-orange">{kpis.pending}</p>
              </Card>
              <Card className="p-4 border-och-steel/20">
                <p className="text-xs text-och-steel mb-1">Mentor graded</p>
                <p className="text-sm text-och-steel/80 mb-0.5">Awaiting your review cutoff</p>
                <p className="text-2xl font-bold text-och-steel">{kpis.reviewed}</p>
              </Card>
              <Card className="p-4 border-och-steel/20">
                <p className="text-xs text-och-steel mb-1">Passed application review</p>
                <p className="text-sm text-och-steel/80 mb-0.5">Above cutoff, in or after interview</p>
                <p className="text-2xl font-bold text-och-defender">{kpis.passed}</p>
              </Card>
              <Card className="p-4 border-och-steel/20">
                <p className="text-xs text-och-steel mb-1">Failed application review</p>
                <p className="text-sm text-och-steel/80 mb-0.5">Below review cutoff</p>
                <p className="text-2xl font-bold text-och-orange">{kpis.failed}</p>
              </Card>
              <Card className="p-4 border-och-steel/20">
                <p className="text-xs text-och-steel mb-1">Ready to enroll</p>
                <p className="text-sm text-och-steel/80 mb-0.5">Passed interview, above cutoff</p>
                <p className="text-2xl font-bold text-och-mint">{kpis.eligible}</p>
              </Card>
            </div>
          )}

          {/* Filters */}
          <Card className="mb-6 border-och-steel/20">
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Filter className="w-4 h-4 text-och-steel" />
                <span className="text-sm font-medium text-white">Filters</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
                <div>
                  <label className="block text-xs text-och-steel mb-1">Cohort</label>
                  <select
                    value={cohortFilter}
                    onChange={(e) => setCohortFilter(e.target.value)}
                    className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm"
                  >
                    <option value="">All cohorts</option>
                    {cohorts.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-och-steel mb-1">Type</label>
                  <select
                    value={applicantTypeFilter}
                    onChange={(e) => setApplicantTypeFilter(e.target.value)}
                    className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm"
                  >
                    <option value="">All (Students & Sponsors)</option>
                    <option value="student">Students</option>
                    <option value="sponsor">Sponsors</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-och-steel mb-1">Application status</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm"
                  >
                    <option value="">All</option>
                    <option value="pending">Submitted (pending)</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                    <option value="converted">Converted</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-och-steel mb-1">Review status</label>
                  <select
                    value={reviewStatusFilter}
                    onChange={(e) => setReviewStatusFilter(e.target.value)}
                    className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm"
                  >
                    <option value="">All</option>
                    <option value="pending">Awaiting mentor review</option>
                    <option value="reviewed">Mentor graded, awaiting cutoff</option>
                    <option value="passed">Passed application review</option>
                    <option value="failed">Failed application review</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-och-steel mb-1">Enrollment</label>
                  <select
                    value={enrollmentStatusFilter}
                    onChange={(e) => setEnrollmentStatusFilter(e.target.value)}
                    className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm"
                  >
                    <option value="">All</option>
                    <option value="eligible">Ready to enroll</option>
                    <option value="enrolled">Enrolled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-och-steel mb-1">Mentor</label>
                  <select
                    value={mentorFilter}
                    onChange={(e) => setMentorFilter(e.target.value)}
                    className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm"
                  >
                    <option value="">All mentors</option>
                    {mentorOptions.map((m) => {
                      const mentorId = typeof m.mentor === 'object' ? (m.mentor as any)?.id : m.mentor
                      const name = m.mentor_name || m.mentor_email || String(mentorId)
                      return <option key={m.id} value={mentorId}>{name}</option>
                    })}
                  </select>
                </div>
                <div className="flex items-end gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setCohortFilter('')
                      setApplicantTypeFilter('')
                      setStatusFilter('')
                      setReviewStatusFilter('')
                      setEnrollmentStatusFilter('')
                      setMentorFilter('')
                    }}
                  >
                    Clear
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {/* Table */}
          <Card className="border-och-steel/20 overflow-hidden">
            {loading ? (
              <div className="p-12 text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-och-defender mx-auto mb-4" />
                <p className="text-och-steel">Loading applications...</p>
              </div>
            ) : applications.length === 0 ? (
              <div className="p-12 text-center">
                {fetchError ? (
                  <p className="text-och-orange mb-2">{fetchError}</p>
                ) : (
                  <p className="text-och-steel">No applications found. Applications appear here when students or sponsors apply from the homepage.</p>
                )}
                <Link href="/" className="text-och-mint hover:underline mt-2 inline-block">View homepage</Link>
              </div>
            ) : (
              <>
              {studentApps.length > 0 && (
                <div className="p-4 border-b border-och-steel/20 bg-och-midnight/30 flex flex-wrap items-center gap-3">
                  <span className="text-och-steel text-sm">{selectedIds.length} selected</span>
                  <Button
                    variant="defender"
                    size="sm"
                    className="gap-1"
                    disabled={selectedIds.length === 0}
                    onClick={handleOpenAssignModal}
                  >
                    <UserPlus className="w-3.5 h-3.5" /> Assign to mentor
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1"
                    disabled={selectedIds.length === 0 || selectedIds.some((id) => sendingTestIds.has(id))}
                    onClick={() => handleSendApplicationTest(selectedIds)}
                  >
                    <Send className="w-3.5 h-3.5 shrink-0" />
                    {selectedIds.some((id) => sendingTestIds.has(id)) ? 'Sending…' : 'Send application test (email)'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1 text-och-gold hover:text-och-gold/90 border-och-gold/40"
                    disabled={selectedIdsWithNoGrade.length === 0 || selectedIdsWithNoGrade.some((id) => gradingTestIds.has(id))}
                    onClick={() => handleGradeWithAI(selectedIdsWithNoGrade)}
                  >
                    <Award className="w-3.5 h-3.5 shrink-0" />
                    {selectedIdsWithNoGrade.some((id) => gradingTestIds.has(id)) ? 'Grading…' : 'Grade with AI'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1 text-och-orange hover:text-och-orange/90"
                    disabled={selectedIds.length === 0}
                    onClick={handleBulkDelete}
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Delete
                  </Button>
                </div>
              )}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-och-steel/20">
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel w-10">
                        <button
                          type="button"
                          onClick={toggleSelectAllStudents}
                          className="inline-flex h-4 w-4 items-center justify-center rounded border border-och-steel/40 bg-och-midnight text-sm font-medium text-och-mint"
                          title={selectedIdsSet.size >= studentApps.length ? 'Deselect all' : 'Select all students'}
                          aria-label={selectedIdsSet.size >= studentApps.length ? 'Deselect all' : 'Select all students'}
                        >
                          {studentApps.length > 0 && selectedIdsSet.size >= studentApps.length ? '✓' : null}
                        </button>
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel w-12">#</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Date</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Cohort</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Type</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Name</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Email</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Grade</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Review by</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-och-steel">Status</th>
                      <th className="text-right py-3 px-4 text-xs font-medium text-och-steel">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {applications.map((app, idx) => {
                      const isStudent = app.applicant_type === 'student'
                      const isSelected = isStudent && selectedIdsSet.has(app.id)
                      const fd: any = (app as any).form_data || {}
                      const testResults = fd.application_test_results
                      const overallScore =
                        testResults && typeof testResults.overall_score === 'number'
                          ? (testResults.overall_score as number)
                          : null
                      const statusLabel = getApplicationStatusLabel(app.status, app as Application)
                      const statusClass = getStatusBadgeClass(statusLabel)
                      return (
                      <tr
                        key={app.id}
                        className="border-b border-och-steel/10 hover:bg-och-midnight/30"
                      >
                        <td className="py-3 px-4 align-middle">
                          {isStudent ? (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                toggleSelected(app.id, true)
                              }}
                              className="inline-flex h-4 w-4 items-center justify-center rounded border border-och-steel/40 bg-och-midnight text-sm font-medium hover:border-och-mint/60"
                              aria-label={isSelected ? 'Deselect row' : 'Select row'}
                              aria-checked={isSelected}
                            >
                              {isSelected ? (
                                <span className="text-och-mint" aria-hidden>✓</span>
                              ) : null}
                            </button>
                          ) : null}
                        </td>
                        <td className="py-3 px-4 text-sm text-och-steel font-medium">{idx + 1}</td>
                        <td className="py-3 px-4 text-sm text-och-steel">
                          {new Date(app.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4 text-sm text-white max-w-[180px] truncate">
                          {app.cohort_name}
                        </td>
                        <td className="py-3 px-4">
                          {app.applicant_type === 'student' ? (
                            <Badge variant="defender" className="gap-1">
                              <GraduationCap className="w-3 h-3" /> Student
                            </Badge>
                          ) : (
                            <Badge variant="gold" className="gap-1">
                              <Users className="w-3 h-3" /> Sponsor
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-4 text-sm text-white">{app.name || '-'}</td>
                        <td className="py-3 px-4 text-sm text-och-steel">{app.email || '-'}</td>
                        <td className="py-3 px-4 text-sm text-white">
                          {overallScore != null ? `${Math.round(overallScore)}%` : '—'}
                        </td>
                        <td className="py-3 px-4 text-sm text-och-steel">
                          {(app as Application).reviewer_mentor_name || '-'}
                        </td>
                        <td className="py-3 px-4">
                          <Badge
                            variant={getStatusVariant(app.status)}
                            title={app.status}
                            className={statusClass}
                          >
                            {statusLabel}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-och-mint hover:text-och-mint/80 p-1.5"
                              onClick={() => setSelectedApp(app)}
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </Button>
                            <Link
                              href={`/dashboard/director/cohorts/${app.cohort_id}`}
                              className="text-och-steel hover:text-och-mint text-sm inline-flex items-center gap-1"
                            >
                              <ExternalLink className="w-3 h-3" />
                            </Link>
                            {isStudent && (
                              <div className="relative">
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setActionMenuAppId((prev) => (prev === app.id ? null : app.id))
                                  }}
                                  className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-och-steel/40 text-och-steel hover:text-och-mint hover:border-och-mint/60 bg-och-midnight/70"
                                  aria-expanded={actionMenuAppId === app.id}
                                  aria-haspopup="true"
                                >
                                  <MoreHorizontal className="w-3.5 h-3.5" />
                                </button>
                                {actionMenuAppId === app.id && (
                                  <div
                                    className="absolute right-0 mt-1 w-44 rounded-md border border-och-steel/40 bg-och-midnight shadow-xl z-50"
                                    onClick={(e) => e.stopPropagation()}
                                    role="menu"
                                  >
                                    <button
                                      type="button"
                                      role="menuitem"
                                      disabled={sendingTestIds.has(app.id)}
                                      className="w-full flex items-center gap-2 px-3 py-2 text-xs text-och-steel hover:bg-och-midnight/60 disabled:opacity-60"
                                      onClick={() => {
                                        handleSendApplicationTest([app.id])
                                      }}
                                    >
                                      <Send className="w-3.5 h-3.5 text-och-mint shrink-0" />
                                      <span>{sendingTestIds.has(app.id) ? 'Sending…' : 'Send application test'}</span>
                                    </button>
                                    <button
                                      type="button"
                                      role="menuitem"
                                      className="w-full flex items-center gap-2 px-3 py-2 text-xs text-och-steel hover:bg-och-midnight/60"
                                      onClick={() => {
                                        setActionMenuAppId(null)
                                        setSelectedApp(app)
                                      }}
                                    >
                                      <Eye className="w-3.5 h-3.5 shrink-0" />
                                      <span>View details</span>
                                    </button>
                                    <button
                                      type="button"
                                      role="menuitem"
                                      className="w-full flex items-center gap-2 px-3 py-2 text-xs text-och-orange hover:bg-och-midnight/60"
                                      onClick={() => {
                                        setActionMenuAppId(null)
                                        handleDeleteSingle(app)
                                      }}
                                    >
                                      <Trash2 className="w-3.5 h-3.5 shrink-0" />
                                      <span>Delete</span>
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )})}
                  </tbody>
                </table>
              </div>

              <ApplicationDetailsModal
                application={selectedApp}
                open={!!selectedApp}
                onOpenChange={(open) => !open && setSelectedApp(null)}
                getStatusVariant={getStatusVariant}
                getApplicationStatusLabel={getApplicationStatusLabel}
                getStatusBadgeClass={getStatusBadgeClass}
                onEnroll={(app) => !enrollingSingleId && handleEnrollSingle(app)}
                onReject={handleRejectSingle}
                onSendCredentials={handleSendCredentials}
                onGradeTest={(app) => handleGradeWithAI([app.id])}
                isGradeTestInProgress={selectedApp ? gradingTestIds.has(selectedApp.id) : false}
              />
              <AssignToMentorModal
                open={showAssignModal}
                onOpenChange={setShowAssignModal}
                mentors={mentors}
                selectedCount={selectedIds.length}
                cohortName={cohortName}
                onAssign={handleAssign}
                assigning={assigning}
              />
              {showCutoffModal && (
                <Dialog open={!!showCutoffModal} onOpenChange={(o) => !o && setShowCutoffModal(null)}>
                  <DialogContent className="max-w-sm border-och-steel/20 bg-och-midnight">
                    <DialogHeader>
                      <DialogTitle className="text-white">
                        Set {showCutoffModal} cutoff grade
                      </DialogTitle>
                    </DialogHeader>
                    <p className="text-och-steel text-sm mb-2">Applications with score ≥ cutoff pass.</p>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      placeholder="0-100"
                      value={cutoffGrade}
                      onChange={(e) => setCutoffGrade(e.target.value)}
                      className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded text-white"
                    />
                    <div className="flex justify-end gap-2 mt-4">
                      <Button variant="outline" onClick={() => setShowCutoffModal(null)}>Cancel</Button>
                      <Button variant="defender" disabled={settingCutoff} onClick={() => handleSetCutoff(showCutoffModal)}>
                        {settingCutoff ? 'Setting...' : 'Set cutoff'}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              )}
              {showEnrollModal && (
                <Dialog open={showEnrollModal} onOpenChange={setShowEnrollModal}>
                  <DialogContent className="max-w-sm border-och-steel/20 bg-och-midnight">
                    <DialogHeader>
                      <DialogTitle className="text-white">Enroll eligible applicants</DialogTitle>
                    </DialogHeader>
                    <p className="text-och-steel text-sm">
                      Enroll {eligibleToEnroll.length} applicant(s) who passed the interview? User accounts will be created if needed.
                    </p>
                    <div className="flex justify-end gap-2 mt-4">
                      <Button variant="outline" onClick={() => setShowEnrollModal(false)}>Cancel</Button>
                      <Button variant="defender" disabled={enrolling} onClick={handleEnroll}>
                        {enrolling ? 'Enrolling...' : 'Enroll'}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              )}
              </>
            )}
          </Card>
            </TabsContent>

            <TabsContent value="application-questions" className="mt-6">
              <ApplicationQuestionsTab cohorts={cohorts} />
            </TabsContent>

            <TabsContent value="interview-questions" className="mt-6">
              <InterviewQuestionsTab cohorts={cohorts} />
            </TabsContent>

            <TabsContent value="grades" className="mt-6">
              <GradesTab
                cohorts={cohorts}
                applications={applications}
                cohortFilter={cohortFilter}
                setCohortFilter={setCohortFilter}
                loading={loading}
              />
            </TabsContent>
          </Tabs>
        </div>
      </DirectorLayout>
    </RouteGuard>
  )
}

export default function ApplicationsPage() {
  return (
    <Suspense fallback={
      <RouteGuard requiredRoles={['program_director', 'admin']}>
        <DirectorLayout>
          <div className="max-w-7xl mx-auto p-12 text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-och-defender mx-auto mb-4" />
            <p className="text-och-steel">Loading applications...</p>
          </div>
        </DirectorLayout>
      </RouteGuard>
    }>
      <ApplicationsContent />
    </Suspense>
  )
}
