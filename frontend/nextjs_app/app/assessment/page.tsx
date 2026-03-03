'use client'

import { useState, useEffect, useCallback, useRef, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { apiGateway } from '@/services/apiGateway'
import { CheckCircle2, Clock, AlertCircle, Loader2, ChevronRight } from 'lucide-react'

type Question = {
  id: string
  type: string
  question_text: string
  options: string[] | { value: string; label: string }[]
  correct_answer?: string
  scoring_weight?: number
}

type Section = {
  section_name: string
  time_minutes: number
  questions: Question[]
}

type AssessmentData = {
  completed: boolean
  completed_at?: string
  message?: string
  token?: string
  cohort_name?: string
  time_limit_minutes?: number
  sections?: Section[]
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function AssessmentContent() {
  const searchParams = useSearchParams()
  const token = searchParams.get('token') || searchParams.get('t') || ''

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<AssessmentData | null>(null)

  const [sectionIndex, setSectionIndex] = useState(0)
  const [questionIndex, setQuestionIndex] = useState(0)
  const [sectionStarted, setSectionStarted] = useState(false)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [countdownSeconds, setCountdownSeconds] = useState(0)
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const answersRef = useRef<Record<string, string>>({})
  answersRef.current = answers

  const currentSection = data?.sections?.[sectionIndex]
  const currentQuestion = currentSection?.questions?.[questionIndex]
  const allQuestions = data?.sections?.flatMap((s) => s.questions) ?? []
  const totalSeconds = (currentSection?.time_minutes ?? 0) * 60

  const fetchAssessment = useCallback(async () => {
    if (!token) {
      setError('Invalid or missing assessment link.')
      setLoading(false)
      return
    }
    try {
      const res = await apiGateway.get<AssessmentData>('/public/assessment/', {
        params: { token },
        skipAuth: true,
      })
      setData(res)
      setError(null)
    } catch (err: unknown) {
      const msg = (err as { message?: string })?.message || 'Failed to load assessment.'
      setError(msg)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    fetchAssessment()
  }, [fetchAssessment])

  const submitAnswers = useCallback(async () => {
    if (!data?.token || submitted) return
    if (countdownRef.current) {
      clearInterval(countdownRef.current)
      countdownRef.current = null
    }
    const currentAnswers = answersRef.current
    const payload = Object.entries(currentAnswers).map(([question_id, answer]) => ({ question_id, answer }))
    try {
      setSubmitting(true)
      await apiGateway.post(
        '/public/assessment/submit/',
        { token: data.token, answers: payload },
        { skipAuth: true }
      )
      setSubmitted(true)
    } catch (err: unknown) {
      setError((err as { message?: string })?.message || 'Failed to submit assessment.')
    } finally {
      setSubmitting(false)
    }
  }, [data?.token, submitted])

  useEffect(() => {
    if (!sectionStarted || submitting || submitted) return
    if (countdownSeconds <= 0) {
      submitAnswers()
      return
    }
    countdownRef.current = setInterval(() => {
      setCountdownSeconds((s) => {
        if (s <= 1) {
          if (countdownRef.current) clearInterval(countdownRef.current)
          submitAnswers()
          return 0
        }
        return s - 1
      })
    }, 1000)
    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current)
    }
  }, [sectionStarted, submitting, submitted])

  const handleStartSection = () => {
    setSectionStarted(true)
    setCountdownSeconds(totalSeconds)
  }

  const setAnswer = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }))
  }

  const goNext = () => {
    if (!currentSection) return
    if (questionIndex < currentSection.questions.length - 1) {
      setQuestionIndex((i) => i + 1)
    } else if (sectionIndex < (data?.sections?.length ?? 1) - 1) {
      setSectionIndex((i) => i + 1)
      setQuestionIndex(0)
      setSectionStarted(false)
    } else {
      submitAnswers()
    }
  }

  const isLastQuestion =
    currentSection &&
    questionIndex === currentSection.questions.length - 1 &&
    sectionIndex === (data?.sections?.length ?? 1) - 1
  const canGoNext = currentQuestion && (answers[currentQuestion.id] ?? '').trim().length > 0

  if (loading) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
        <Card className="p-8 max-w-md w-full text-center">
          <Loader2 className="w-12 h-12 text-och-mint animate-spin mx-auto mb-4" />
          <p className="text-och-steel">Loading assessment...</p>
        </Card>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
        <Card className="p-8 max-w-md w-full text-center border-och-steel/30">
          <AlertCircle className="w-12 h-12 text-och-orange mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-white mb-2">Invalid or expired link</h1>
          <p className="text-och-steel mb-6">{error}</p>
          <p className="text-sm text-och-steel">Use the link from your application test email. If the problem continues, contact your program coordinator.</p>
        </Card>
      </div>
    )
  }

  if (data?.completed || submitted) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
        <Card className="p-8 max-w-md w-full text-center border-och-mint/20">
          <CheckCircle2 className="w-14 h-14 text-och-mint mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-white mb-2">
            {submitted ? 'Assessment submitted' : 'Already completed'}
          </h1>
          <p className="text-och-steel">
            {submitted
              ? 'Your assessment has been submitted successfully. You can close this page.'
              : data?.message || 'You have already completed this assessment. This link will not accept further submissions.'}
          </p>
        </Card>
      </div>
    )
  }

  if (!currentSection || !data?.sections?.length) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
        <Card className="p-8 max-w-md w-full text-center">
          <p className="text-och-steel">No assessment is available for this link.</p>
        </Card>
      </div>
    )
  }

  if (!sectionStarted) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
        <Card className="p-8 max-w-lg w-full border-och-steel/30">
          <h1 className="text-xl font-semibold text-white mb-2">{data.cohort_name} – Application test</h1>
          <h2 className="text-lg text-och-mint mb-4">{currentSection.section_name}</h2>
          <p className="text-och-steel mb-2">
            This section has <strong>{currentSection.questions.length}</strong> question{currentSection.questions.length !== 1 ? 's' : ''}.
          </p>
          <p className="text-och-steel mb-6 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Time allowed: <strong>{currentSection.time_minutes} minutes</strong>. When you click Start, a countdown will begin. When time runs out, your answers will be submitted automatically.
          </p>
          <Button onClick={handleStartSection} className="w-full gap-2" variant="defender">
            Start section
            <ChevronRight className="w-4 h-4" />
          </Button>
        </Card>
      </div>
    )
  }

  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
        <Card className="p-8 max-w-md w-full text-center">
          <Loader2 className="w-10 h-10 text-och-mint animate-spin mx-auto mb-4" />
          <p className="text-och-steel">Submitting...</p>
        </Card>
      </div>
    )
  }

  const options = Array.isArray(currentQuestion.options)
    ? currentQuestion.options.map((o) => (typeof o === 'object' && o !== null && 'value' in o ? (o as { value: string; label: string }) : { value: String(o), label: String(o) }))
    : []

  return (
    <div className="min-h-screen bg-och-midnight p-4 pb-24">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <span className="text-och-steel text-sm">
            Question {questionIndex + 1} of {currentSection.questions.length}
            {data.sections.length > 1 ? ` (Section ${sectionIndex + 1})` : ''}
          </span>
          <div className="flex items-center gap-2 text-och-mint font-mono font-medium">
            <Clock className="w-4 h-4" />
            {formatTime(countdownSeconds)}
          </div>
        </div>

        <Card className="p-6 sm:p-8 border-och-steel/30 mb-6">
          <h2 className="text-lg font-medium text-white mb-6">{currentQuestion.question_text}</h2>

          {currentQuestion.type === 'mcq' && options.length > 0 ? (
            <ul className="space-y-3">
              {options.map((opt) => (
                <li key={opt.value}>
                  <label className="flex items-start gap-3 p-3 rounded-lg border border-och-steel/30 hover:border-och-mint/40 cursor-pointer has-[:checked]:border-och-mint has-[:checked]:bg-och-mint/10">
                    <input
                      type="radio"
                      name={currentQuestion.id}
                      value={opt.value}
                      checked={answers[currentQuestion.id] === opt.value}
                      onChange={() => setAnswer(currentQuestion.id, opt.value)}
                      className="mt-1 text-och-mint border-och-steel focus:ring-och-mint"
                    />
                    <span className="text-och-steel">{opt.label}</span>
                  </label>
                </li>
              ))}
            </ul>
          ) : (
            <textarea
              value={answers[currentQuestion.id] ?? ''}
              onChange={(e) => setAnswer(currentQuestion.id, e.target.value)}
              placeholder="Type your answer here..."
              rows={5}
              className="w-full px-4 py-3 bg-och-midnight border border-och-steel/30 rounded-lg text-white placeholder:text-och-steel/60 focus:border-och-mint focus:ring-1 focus:ring-och-mint"
            />
          )}
        </Card>

        {error && (
          <p className="text-och-orange text-sm mb-4">{error}</p>
        )}

        <div className="flex justify-end">
          <Button
            onClick={goNext}
            disabled={!canGoNext || submitting}
            className="gap-2"
            variant="defender"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Submitting...
              </>
            ) : isLastQuestion ? (
              'Submit assessment'
            ) : (
              <>
                Next
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function AssessmentPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-4">
        <Card className="p-8 max-w-md w-full text-center">
          <Loader2 className="w-12 h-12 text-och-mint animate-spin mx-auto mb-4" />
          <p className="text-och-steel">Loading assessment...</p>
        </Card>
      </div>
    }>
      <AssessmentContent />
    </Suspense>
  )
}
