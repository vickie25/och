'use client'

import { motion } from 'framer-motion'
import { Brain, Zap, Theater, LayoutTemplate } from 'lucide-react'
import { useState, useEffect } from 'react'

interface ProfilingQuestion {
  id: string
  question: string
  category: string
  options: Array<{
    value: string
    text: string
  }>
}

interface Progress {
  session_id: string
  current_question: number
  total_questions: number
  progress_percentage: number
  estimated_time_remaining: number
}

interface AIProfilerAssessmentProps {
  question: ProfilingQuestion
  questionNumber: number
  totalQuestions: number
  progress: Progress
  onAnswer: (questionId: string, answer: string) => void
  previousAnswer?: string
}

export default function AIProfilerAssessment({
  question,
  questionNumber,
  totalQuestions,
  progress,
  onAnswer,
  previousAnswer
}: AIProfilerAssessmentProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<string>(previousAnswer || '')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Reset selection when question changes so no option is pre-highlighted on the next question
  useEffect(() => {
    setSelectedAnswer(previousAnswer || '')
  }, [question.id, previousAnswer])

  // Auto-save answer selection to localStorage immediately
  useEffect(() => {
    if (selectedAnswer && selectedAnswer !== previousAnswer) {
      // Save to localStorage for immediate persistence
      const saveKey = `profiling_answer_${question.id}`
      localStorage.setItem(saveKey, selectedAnswer)
      console.log('[AIProfilerAssessment] Answer saved locally:', { questionId: question.id, answer: selectedAnswer })
    }
  }, [selectedAnswer, question.id, previousAnswer])

  const handleSubmit = async () => {
    if (!selectedAnswer || isSubmitting) return

    let answerToSubmit = selectedAnswer

    // NOTE: Backend expects A, B, C, D, E as option values - this is correct!
    // Ensure uppercase for consistency
    if (selectedAnswer.length === 1 && /^[A-E]$/i.test(selectedAnswer)) {
      answerToSubmit = selectedAnswer.toUpperCase()
      console.log('[AIProfilerAssessment] Answer is A-E (valid):', answerToSubmit)
    }

    setIsSubmitting(true)
    try {
      console.log('[AIProfilerAssessment] Submitting answer:', {
        questionId: question.id,
        answer: answerToSubmit,
        answerLength: answerToSubmit.length
      })
      await onAnswer(question.id, answerToSubmit)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getCategoryInfo = (category: string) => {
    const categories: Record<
      string,
      { icon: JSX.Element; name: string; color: string }
    > = {
      technical_aptitude: { icon: <Brain className="h-3.5 w-3.5 text-[#38BDF8]" />, name: 'Technical Aptitude', color: 'text-[#38BDF8]' },
      problem_solving: { icon: <Zap className="h-3.5 w-3.5 text-[#22C55E]" />, name: 'Problem Solving', color: 'text-[#22C55E]' },
      scenario_preference: { icon: <Theater className="h-3.5 w-3.5 text-[#A855F7]" />, name: 'Scenario Analysis', color: 'text-[#A855F7]' },
      work_style: { icon: <LayoutTemplate className="h-3.5 w-3.5 text-[#FBBF24]" />, name: 'Work Style', color: 'text-[#FBBF24]' },
    }
    return (
      categories[category] || {
        icon: <Brain className="h-3.5 w-3.5 text-[#64748B]" />,
        name: category,
        color: 'text-[#64748B]',
      }
    )
  }

  const categoryInfo = getCategoryInfo(question.category)
  const progressPercentage = Math.round(progress.progress_percentage)

  // Listen for answer selection events (for tracking)
  useEffect(() => {
    const handleAnswerSelected = (event: CustomEvent) => {
      console.log('[AIProfilerAssessment] Answer selection event received:', event.detail)
      // This event is already handled in onChange, but can be used for additional tracking
    }

    window.addEventListener('profiling-answer-selected', handleAnswerSelected as EventListener)
    return () => {
      window.removeEventListener('profiling-answer-selected', handleAnswerSelected as EventListener)
    }
  }, [])

  return (
    <div className="h-screen flex flex-col px-3 py-2 overflow-hidden">
      {/* Progress at top – compact, always visible */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex-shrink-0 bg-gradient-to-b from-och-midnight/98 to-och-midnight/95 backdrop-blur-sm rounded-b-lg pb-2 pt-1 px-2"
      >
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-wrap items-center justify-between gap-1 mb-1">
            <div className="text-white text-xs font-semibold">
              Question {questionNumber} of {totalQuestions}
            </div>
            <div className="text-gray-400 text-xs">
              {Math.floor(progress.estimated_time_remaining / 60)}:{(progress.estimated_time_remaining % 60).toString().padStart(2, '0')} left
            </div>
          </div>
          <div className="w-full bg-white/20 rounded-full h-1.5 mb-1">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progressPercentage}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className="bg-gradient-to-r from-och-orange to-och-crimson h-1.5 rounded-full"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-xs">{progressPercentage}%</span>
            <button
              onClick={handleSubmit}
              disabled={!selectedAnswer || isSubmitting}
              className={`text-xs font-bold px-4 py-1.5 rounded-full transition-all ${
                selectedAnswer && !isSubmitting
                  ? 'bg-gradient-to-r from-och-orange to-och-crimson text-white hover:opacity-90'
                  : 'bg-gray-600 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isSubmitting ? '...' : questionNumber === totalQuestions ? 'Complete' : 'Next'}
            </button>
          </div>
        </div>
      </motion.div>

      {/* Question + choices – fits on screen; scrolls only on very small viewports */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="max-w-4xl mx-auto w-full flex-1 min-h-0 flex flex-col py-2 overflow-y-auto"
      >
        <p className="text-[10px] text-[#64748B] text-center flex-shrink-0 mb-1">
          Progress is saved automatically.
        </p>

        {/* Question card – compact */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="bg-white/10 backdrop-blur-sm rounded-lg p-3 flex-shrink-0"
        >
          <div className="flex items-center mb-2 gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[rgba(15,23,42,0.9)] border border-[rgba(148,163,184,0.4)]">
              {categoryInfo.icon}
            </span>
            <span className={`text-[11px] font-semibold ${categoryInfo.color}`}>
              {categoryInfo.name}
            </span>
          </div>
          <h2 className="text-base md:text-lg font-bold text-white leading-snug mb-3">
            {question.question}
          </h2>

          {/* Options – compact list so all fit on screen */}
          <div className="space-y-2">
            {question.options.map((option, index) => {
              let optionValue = option.value || option.text || `option_${index}`
              const optionText = option.text || option.value || optionValue
              if (optionValue.length === 1 && /^[A-E]$/i.test(optionValue)) {
                optionValue = optionValue.toUpperCase()
              }
              return (
                <motion.label
                  key={optionValue}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2, delay: index * 0.03 }}
                  className={`flex items-center gap-2 p-3 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                    selectedAnswer === optionValue
                      ? 'border-och-orange bg-och-orange/20 text-white'
                      : 'border-white/20 bg-white/5 text-gray-300 hover:border-white/40 hover:bg-white/10'
                  }`}
                >
                  <input
                    type="radio"
                    name={`question-${question.id}`}
                    value={optionValue}
                    checked={selectedAnswer === optionValue}
                    onChange={(e) => {
                      const selectedValue = e.target.value
                      const normalizedValue = selectedValue.length === 1 && /^[A-E]$/i.test(selectedValue)
                        ? selectedValue.toUpperCase()
                        : selectedValue
                      setSelectedAnswer(normalizedValue)
                      if (typeof window !== 'undefined') {
                        window.dispatchEvent(new CustomEvent('profiling-answer-selected', {
                          detail: {
                            questionId: question.id,
                            answer: normalizedValue,
                            questionNumber: questionNumber,
                            timestamp: new Date().toISOString()
                          }
                        }))
                      }
                    }}
                    className="accent-och-orange flex-shrink-0"
                  />
                  <span className="text-sm leading-tight">{optionText}</span>
                </motion.label>
              )
            })}
          </div>
        </motion.div>

        {/* Bottom submit – compact */}
        <div className="flex-shrink-0 text-center pt-2">
          <button
            onClick={handleSubmit}
            disabled={!selectedAnswer || isSubmitting}
            className={`text-sm font-bold px-8 py-2.5 rounded-full transition-all ${
              selectedAnswer && !isSubmitting
                ? 'bg-gradient-to-r from-och-orange to-och-crimson text-white hover:opacity-90'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                Processing...
              </span>
            ) : questionNumber === totalQuestions ? (
              'Complete Assessment'
            ) : (
              'Next Question'
            )}
          </button>
        </div>
      </motion.div>
    </div>
  )
}





































