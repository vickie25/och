'use client'

import { motion } from 'framer-motion'
import { ListChecks, Clock, Brain, Target } from 'lucide-react'

interface AIProfilerInstructionsProps {
  onContinue: () => void
  totalQuestions: number
}

export default function AIProfilerInstructions({ onContinue, totalQuestions }: AIProfilerInstructionsProps) {
  return (
    <div className="min-h-screen flex flex-col px-4 py-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="max-w-3xl mx-auto w-full flex-1 overflow-hidden flex flex-col gap-4"
      >
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-center space-y-3"
        >
          <div className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[rgba(248,250,252,0.12)] bg-[rgba(15,23,42,0.9)]">
            <ListChecks className="h-5 w-5 text-[#F59E0B]" />
          </div>
          <h1 className="font-['Space_Grotesk'] text-[clamp(22px,3vw,28px)] font-bold tracking-[-0.06em] text-[#E2E8F0]">
            How this assessment works
          </h1>
          <p className="text-[13px] md:text-[14px] text-[#94A3B8] max-w-[520px] mx-auto">
            Answer honestly and instinctively. There are no &ldquo;right&rdquo; answers – we&apos;re mapping you to the work you&apos;ll actually thrive in.
          </p>
        </motion.div>

        {/* Instructions + overview (compressed into one block) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="bg-white/5 rounded-xl p-4 md:p-5 flex flex-col gap-4"
        >
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-3 text-left">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 inline-flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(245,158,11,0.18)] text-[11px] font-semibold text-[#F59E0B]">
                  1
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-[#E2E8F0]">Be honest.</p>
                  <p className="text-[12px] text-[#94A3B8]">
                    Answer based on what you actually enjoy and how you naturally work – not what you think sounds impressive.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-0.5 inline-flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(245,158,11,0.18)] text-[11px] font-semibold text-[#F59E0B]">
                  2
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-[#E2E8F0]">Picture real scenarios.</p>
                  <p className="text-[12px] text-[#94A3B8]">
                    Many questions mirror real work situations. Choose the option that feels most like how you&apos;d respond.
                  </p>
                </div>
              </div>
            </div>
            <div className="space-y-3 text-left">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 inline-flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(245,158,11,0.18)] text-[11px] font-semibold text-[#F59E0B]">
                  3
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-[#E2E8F0]">Check your energy.</p>
                  <p className="text-[12px] text-[#94A3B8]">
                    Pay attention to what gives you energy – building, defending, leading, designing, or advising.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-0.5 inline-flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(245,158,11,0.18)] text-[11px] font-semibold text-[#F59E0B]">
                  4
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-[#E2E8F0]">No time pressure.</p>
                  <p className="text-[12px] text-[#94A3B8]">
                    Take your time. The more thoughtful your responses, the sharper your track match.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 border-t border-[rgba(148,163,184,0.35)] pt-3 mt-1 text-[12px] text-[#CBD5F5]">
            <div className="flex items-center justify-center gap-2">
              <Brain className="h-4 w-4 text-[#FBBF24]" />
              <span>{totalQuestions} questions • scenario-based</span>
            </div>
            <div className="flex items-center justify-center gap-2">
              <Clock className="h-4 w-4 text-[#38BDF8]" />
              <span>10–15 minutes • auto-saves as you go</span>
            </div>
          </div>
        </motion.div>

        {/* Bottom CTA: single Start Assessment button */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.9 }}
          className="text-center pb-4"
        >
          <button
            onClick={onContinue}
            className="inline-flex items-center gap-2 rounded-[999px] bg-gradient-to-r from-och-orange to-och-crimson px-8 py-3 text-[13px] font-semibold text-white shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
          >
            <Target className="h-4 w-4" />
            Start assessment
          </button>
          <p className="text-[#94A3B8] text-[11px] mt-2">
            Takes about 10–15 minutes • No wrong answers
          </p>
        </motion.div>
      </motion.div>
    </div>
  )
}





































