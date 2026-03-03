'use client'

import { motion } from 'framer-motion'

interface AIProfilerInstructionsProps {
  onContinue: () => void
  totalQuestions: number
}

export default function AIProfilerInstructions({ onContinue, totalQuestions }: AIProfilerInstructionsProps) {
  return (
    <div className="min-h-screen flex flex-col px-4 py-4">
      {/* Sticky top: button visible so users know they can proceed without scrolling */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="sticky top-0 z-10 flex-shrink-0 flex justify-center py-3 pb-4 bg-gradient-to-b from-och-midnight/95 via-och-midnight/90 to-transparent backdrop-blur-sm"
      >
        <button
          onClick={onContinue}
          className="bg-gradient-to-r from-och-orange to-och-crimson hover:from-och-orange/80 hover:to-och-crimson/80 text-white text-lg font-bold px-10 py-3 rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
        >
          Start Assessment
        </button>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="max-w-3xl mx-auto w-full flex-1 overflow-y-auto"
      >
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-center mb-8"
        >
          <div className="text-5xl mb-4">📋</div>
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Assessment Instructions
          </h1>
          <p className="text-xl text-gray-300">
            Follow these guidelines for the most accurate results
          </p>
        </motion.div>

        {/* Instructions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="bg-white/10 backdrop-blur-sm rounded-xl p-8 mb-8"
        >
          <div className="space-y-6">
            <div className="flex items-start space-x-4">
              <div className="bg-och-orange rounded-full w-8 h-8 flex items-center justify-center text-black font-bold text-sm flex-shrink-0 mt-1">
                1
              </div>
              <div>
                <h3 className="text-white font-semibold mb-2">Be Authentic</h3>
                <p className="text-gray-300">
                  Answer based on your genuine preferences and natural tendencies. There's no "right" answer - we're finding your best fit.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="bg-och-orange rounded-full w-8 h-8 flex items-center justify-center text-black font-bold text-sm flex-shrink-0 mt-1">
                2
              </div>
              <div>
                <h3 className="text-white font-semibold mb-2">Think About Scenarios</h3>
                <p className="text-gray-300">
                  Many questions present realistic work situations. Consider how you'd actually behave in these scenarios.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="bg-och-orange rounded-full w-8 h-8 flex items-center justify-center text-black font-bold text-sm flex-shrink-0 mt-1">
                3
              </div>
              <div>
                <h3 className="text-white font-semibold mb-2">Consider Your Energy</h3>
                <p className="text-gray-300">
                  Think about what energizes you most - building things, leading teams, exploring ideas, or helping others grow.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="bg-och-orange rounded-full w-8 h-8 flex items-center justify-center text-black font-bold text-sm flex-shrink-0 mt-1">
                4
              </div>
              <div>
                <h3 className="text-white font-semibold mb-2">Take Your Time</h3>
                <p className="text-gray-300">
                  Read each question carefully. There's no time limit, but thoughtful responses give better results.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Assessment Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="bg-white/5 rounded-xl p-6 mb-8"
        >
          <h3 className="text-white font-semibold mb-4 text-center">Assessment Overview</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="text-center">
              <div className="text-3xl mb-2">❓</div>
              <div className="text-2xl font-bold text-white">{totalQuestions}</div>
              <div className="text-gray-300">Questions</div>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">⏱️</div>
              <div className="text-2xl font-bold text-white">10-15</div>
              <div className="text-gray-300">Minutes</div>
            </div>
          </div>
        </motion.div>

        {/* Categories */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mb-8"
        >
          <h3 className="text-white font-semibold mb-4 text-center">What We'll Assess</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { name: 'Technical Aptitude', icon: '🧠', desc: 'Logic & patterns' },
              { name: 'Problem Solving', icon: '💡', desc: 'Decision making' },
              { name: 'Work Style', icon: '⚡', desc: 'Energy & preferences' },
              { name: 'Scenario Analysis', icon: '🎭', desc: 'Real situations' }
            ].map((category, index) => (
              <motion.div
                key={category.name}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: 1.0 + index * 0.1 }}
                className="bg-white/10 rounded-lg p-4 text-center hover:bg-white/20 transition-colors"
              >
                <div className="text-2xl mb-2">{category.icon}</div>
                <div className="text-white font-semibold text-sm mb-1">{category.name}</div>
                <div className="text-gray-400 text-xs">{category.desc}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* In-page continue (same action as sticky button) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 1.2 }}
          className="text-center pb-8"
        >
          <button
            onClick={onContinue}
            className="bg-gradient-to-r from-och-orange to-och-crimson hover:from-och-orange/80 hover:to-och-crimson/80 text-white text-xl font-bold px-12 py-4 rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
          >
            Start Assessment
          </button>
          <p className="text-gray-400 text-sm mt-4">
            Takes about 10–15 minutes • No wrong answers
          </p>
        </motion.div>
      </motion.div>
    </div>
  )
}





































