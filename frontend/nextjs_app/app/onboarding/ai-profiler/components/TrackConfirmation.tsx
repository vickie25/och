'use client'

import { motion } from 'framer-motion'
import { useState } from 'react'
import { CheckCircle2, XCircle, ArrowRight, Shield, Sword, ClipboardList, FlaskConical, Crown, Crosshair } from 'lucide-react'

interface Track {
  key: string
  name: string
  description: string
  icon?: string
}

interface TrackRecommendationScore {
  track_key: string
  track_name: string
  score: number
}

interface TrackConfirmationProps {
  recommendedTrack: Track
  allTracks: Track[]
  // Optional raw recommendation scores from the profiler so we can
  // show clear percentages for the primary and alternative tracks.
  recommendations?: TrackRecommendationScore[]
  onConfirm: (trackKey: string) => void
  onDecline: () => void
}

const TRACK_INFO: Record<string, { icon: JSX.Element; color: string; description: string }> = {
  defender: {
    icon: <Shield className="h-6 w-6" />,
    color: 'from-blue-500 to-blue-700',
    description: 'Protect systems, detect threats, and respond to incidents'
  },
  offensive: {
    icon: <Sword className="h-6 w-6" />,
    color: 'from-red-500 to-red-700',
    description: 'Ethical hacking, penetration testing, and security research'
  },
  grc: {
    icon: <ClipboardList className="h-6 w-6" />,
    color: 'from-purple-500 to-purple-700',
    description: 'Governance, risk management, and compliance'
  },
  innovation: {
    icon: <FlaskConical className="h-6 w-6" />,
    color: 'from-green-500 to-green-700',
    description: 'Build security solutions, innovate, and create new technologies'
  },
  leadership: {
    icon: <Crown className="h-6 w-6" />,
    color: 'from-yellow-500 to-yellow-700',
    description: 'Lead security teams, strategize, and drive organizational change'
  }
}

export default function TrackConfirmation({
  recommendedTrack,
  allTracks,
  recommendations,
  onConfirm,
  onDecline
}: TrackConfirmationProps) {
  const [selectedTrack, setSelectedTrack] = useState<string>(recommendedTrack.key)

  // Normalize strengths to percentages that sum to ~100 based on the
  // scores provided by the profiler engine.
  const totalScore = recommendations && recommendations.length > 0
    ? recommendations.reduce((sum, rec) => sum + (rec.score || 0), 0)
    : 0

  const strengthByTrack = recommendations && recommendations.length > 0 && totalScore > 0
    ? recommendations.map(rec => ({
        ...rec,
        strengthPct: Math.round(((rec.score || 0) / totalScore) * 100)
      }))
    : null

  const getTrackStrengthPct = (trackKey: string): number | null => {
    if (!strengthByTrack) return null
    const found = strengthByTrack.find(rec => rec.track_key === trackKey)
    return found ? found.strengthPct : null
  }

  const trackInfo = TRACK_INFO[recommendedTrack.key] || {
    icon: <Crosshair className="h-6 w-6" />,
    color: 'from-gray-500 to-gray-700',
    description: recommendedTrack.description
  }

  const handleConfirm = () => {
    onConfirm(selectedTrack)
  }

  const handleDecline = () => {
    // Call parent's onDecline to restart profiling from beginning
    onDecline()
  }

  const handleSelectOtherTrack = (trackKey: string) => {
    setSelectedTrack(trackKey)
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-3 py-3 bg-gradient-to-br from-och-midnight via-och-space to-och-crimson">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-4xl w-full"
      >
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl px-4 py-3 md:px-6 md:py-3 border border-white/20 flex flex-col gap-2">
          {/* Header */}
          <div className="text-center mb-1">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
              className="text-2xl mb-1"
            >
              {trackInfo.icon}
            </motion.div>
            <h1 className="text-lg md:text-xl font-bold text-white">
              Track Recommendation
            </h1>
          </div>

          {/* Recommended Track Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className={`bg-gradient-to-r ${trackInfo.color} rounded-xl px-4 py-3 md:px-5 md:py-3 border border-white/30 shadow`}
          >
            <div className="text-center">
              <h2 className="text-lg md:text-xl font-bold text-white mb-1">
                {recommendedTrack.name} Track
              </h2>
              {(() => {
                const primaryPct = getTrackStrengthPct(recommendedTrack.key)
                if (typeof primaryPct === 'number') {
                  return (
                    <p className="text-white/90 text-[11px] md:text-sm mb-1">
                      {trackInfo.description}
                    </p>
                  )
                }
                return (
                  <p className="text-white/90 text-[11px] md:text-sm mb-2">
                    {trackInfo.description}
                  </p>
                )
              })()}
              {typeof getTrackStrengthPct(recommendedTrack.key) === 'number' && (
                <p className="text-white font-semibold text-xs md:text-sm mb-2">
                  Match strength: {getTrackStrengthPct(recommendedTrack.key)}%
                </p>
              )}
              <div className="inline-block bg-white/20 px-3 py-1 rounded-full border border-white/30">
                <span className="text-white font-semibold text-[11px] md:text-sm">
                  🎯 Best Match for Your Profile
                </span>
              </div>
            </div>
          </motion.div>

          {/* Supporting text beneath best match (key note) */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mb-2"
          >
            <p className="text-center text-gray-100 text-[11px] md:text-xs font-semibold mb-1">
              Based on your profiling assessment, the track above aligns best with your skills and interests.
            </p>
            <div className="w-full flex justify-center">
              <div className="inline-flex w-full max-w-3xl items-start gap-2 rounded-md bg-red-500/15 px-3 py-2 border border-red-500/40">
              <span className="text-[10px] md:text-[11px] font-bold uppercase tracking-wide text-red-300">
                NB
              </span>
                <div className="text-[10px] md:text-[11px] text-red-100 space-y-0.5">
                  <p>
                    If it doesn&apos;t feel like the perfect fit, you can confidently select any of the other tracks below and proceed with the one that matches where you&apos;d like to grow.
                  </p>
                  <p>
                    Och will help you build from your strengths so you can grow your match towards 100% over time.
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Other Tracks Overview (compact, same page) */}
          {allTracks.length > 1 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45 }}
              className="mb-1.5 flex-shrink-0"
            >
              <h3 className="text-center text-xs md:text-sm font-semibold text-[#E2E8F0] mb-2.5">
                How you scored on other tracks
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-2">
                {allTracks.map((track) => {
                  const info = TRACK_INFO[track.key] || {
                    icon: '🎯',
                    color: 'from-gray-500 to-gray-700',
                    description: track.description
                  }
                  const isSelected = selectedTrack === track.key
                  const isRecommended = track.key === recommendedTrack.key
                  const strengthPct = getTrackStrengthPct(track.key)

                  return (
                    <button
                      key={track.key}
                      type="button"
                      onClick={() => handleSelectOtherTrack(track.key)}
                      className={`flex flex-col items-start rounded-lg border px-2 py-2 text-left transition-all ${
                        isSelected
                          ? 'border-och-orange bg-och-orange/20'
                          : 'border-white/15 bg-white/5 hover:border-white/35'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className="text-lg">{info.icon}</span>
                        <span className="text-xs md:text-sm font-semibold text-white">
                          {track.name}
                        </span>
                        {isRecommended && (
                          <span className="ml-1 rounded-full bg-och-orange/30 px-1.5 py-0.5 text-[9px] font-semibold text-och-orange">
                            Recommended
                          </span>
                        )}
                      </div>
                      {typeof strengthPct === 'number' && (
                        <p className="text-[11px] font-semibold text-och-orange mb-0.5">
                          {strengthPct}% match
                        </p>
                      )}
                      <p className="text-[10px] text-gray-300 line-clamp-2">
                        {info.description}
                      </p>
                      {isSelected && (
                        <div className="mt-0.5 flex items-center text-[10px] text-och-orange">
                          <CheckCircle2 className="mr-1 h-3 w-3" />
                          Selected
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </motion.div>
          )}

          {/* Action Button */}
          <div className="flex flex-col sm:flex-row gap-2 justify-center mt-1.5">
            <motion.button
              onClick={handleConfirm}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.55 }}
              className="flex-1 sm:flex-none px-6 py-2.5 bg-gradient-to-r from-och-orange to-och-crimson hover:from-och-orange/80 hover:to-och-crimson/80 text-white rounded-lg font-semibold text-sm md:text-[15px] transition-all transform hover:scale-105 flex items-center justify-center gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              Confirm & proceed with selected track
            </motion.button>
          </div>

          {/* Info Text */}
          {/* (Bottom helper text removed per layout request – main guidance now shown above score grid) */}
        </div>
      </motion.div>
    </div>
  )
}
