'use client'

import { motion } from 'framer-motion'
import { Shield, Sword, FlaskConical, Crown, ClipboardList, Brain, Scale, Crosshair } from 'lucide-react'

interface AIProfilerWelcomeProps {
  onStart: () => void
}

export default function AIProfilerWelcome({ onStart }: AIProfilerWelcomeProps) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="w-full max-w-4xl mx-auto text-center space-y-4"
      >
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-4"
        >
          <div className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[rgba(248,250,252,0.14)] bg-[rgba(15,23,42,0.85)] mb-3">
            <Crosshair className="h-5 w-5 text-[#F59E0B]" />
          </div>
          <h1 className="font-['Space_Grotesk'] text-[clamp(26px,3vw,32px)] font-bold tracking-[-0.06em] text-[#E2E8F0] mb-2">
            AI Career Profiler
          </h1>
          <p className="text-[13px] md:text-[14px] text-[#94A3B8] max-w-[520px] mx-auto">
            A short, mission-grade assessment that maps your strengths, learning style, and goals to the right OCH track.
          </p>
        </motion.div>

        {/* OCH Tracks Preview (compressed) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mb-4"
        >
          <h2 className="text-[13px] md:text-[14px] font-semibold text-[#E2E8F0] mb-2 uppercase tracking-[0.18em] text-[#FBBF24]">
            OCH career tracks
          </h2>
          <div className="flex flex-wrap justify-center gap-2">
            {[
              { 
                key: 'defender', 
                name: 'Defender', 
                icon: <Shield className="h-3.5 w-3.5 text-[#60A5FA]" />,
              },
              { 
                key: 'offensive', 
                name: 'Offensive', 
                icon: <Sword className="h-3.5 w-3.5 text-[#F97373]" />,
              },
              { 
                key: 'innovation', 
                name: 'Innovation', 
                icon: <FlaskConical className="h-3.5 w-3.5 text-[#22C55E]" />,
              },
              { 
                key: 'leadership', 
                name: 'Leadership', 
                icon: <Crown className="h-3.5 w-3.5 text-[#FBBF24]" />,
              },
              { 
                key: 'grc', 
                name: 'GRC', 
                icon: <ClipboardList className="h-3.5 w-3.5 text-[#A855F7]" />,
              }
            ].map((track, index) => (
              <motion.div
                key={track.key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.6 + index * 0.08 }}
                className="inline-flex items-center gap-1 rounded-full border border-[rgba(148,163,184,0.4)] bg-[rgba(15,23,42,0.9)] px-3 py-1 text-[11px] md:text-[12px] text-[#E2E8F0]"
              >
                {track.icon}
                <span>{track.name}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* How it works (compact row) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mb-4"
        >
          <h2 className="text-[13px] md:text-[14px] font-semibold text-[#E2E8F0] mb-2">
            How it works
          </h2>
          <div className="flex flex-col md:flex-row items-center justify-center gap-3 text-[11px] md:text-[13px] text-[#94A3B8]">
            <div className="inline-flex items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-[rgba(15,23,42,0.9)] border border-[rgba(148,163,184,0.5)] flex items-center justify-center">
                <Brain className="h-3.5 w-3.5 text-[#FBBF24]" />
              </div>
              <span>Answer a short, guided assessment.</span>
            </div>
            <span className="hidden md:inline text-[#475569]">•</span>
            <div className="inline-flex items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-[rgba(15,23,42,0.9)] border border-[rgba(148,163,184,0.5)] flex items-center justify-center">
                <Scale className="h-3.5 w-3.5 text-[#38BDF8]" />
              </div>
              <span>AI weighs your strengths, goals, and learning style.</span>
            </div>
            <span className="hidden md:inline text-[#475569]">•</span>
            <div className="inline-flex items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-[rgba(15,23,42,0.9)] border border-[rgba(148,163,184,0.5)] flex items-center justify-center">
                <Crosshair className="h-3.5 w-3.5 text-[#F59E0B]" />
              </div>
              <span>We lock in the OCH track that fits you best.</span>
            </div>
          </div>
        </motion.div>

        {/* Start Button */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 1.0 }}
        >
          <button
            onClick={onStart}
            className="bg-gradient-to-r from-och-orange to-och-crimson hover:from-och-orange/80 hover:to-och-crimson/80 text-white text-lg md:text-xl font-bold px-8 md:px-10 py-3 md:py-3.5 rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
          >
            Start AI Assessment
          </button>
          <p className="text-gray-400 text-xs md:text-sm mt-3">
            Takes about 10-15 minutes • No wrong answers
          </p>
        </motion.div>
      </motion.div>
    </div>
  )
}

































