'use client'

import { memo, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Shield,
  ArrowRight,
  Users,
  Target,
  Zap,
  BookOpen,
  Trophy,
  TrendingUp,
  CheckCircle,
  GraduationCap,
  MessageSquare,
  BarChart3,
  Menu,
  X,
  Terminal,
  BadgeCheck,
  Quote,
  Laptop,
  BarChart3 as BarChartIcon,
  Repeat,
  Lock,
  Paperclip
} from 'lucide-react'
import { apiGateway } from '@/services/apiGateway'
import { GoogleSignInButton } from './login/[role]/components/GoogleSignInButton'

type Track = {
  id: string
  name: string
  description?: string
}

interface HeroCohort {
  id: string
  name: string
  start_date: string
  end_date: string
  mode: string
}

// Simple scroll-reveal wrapper
const Reveal = memo(function Reveal({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    setIsVisible(true)
  }, [])

  return (
    <div
      className={`transition-all duration-700 ease-[cubic-bezier(0.22,0.61,0.36,1)] ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  )
})

Reveal.displayName = 'Reveal'

// Terminal typing line
const TerminalTyping = memo(function TerminalTyping() {
  const lines = useMemo(
    () => [
      '$ cyboch init --profile',
      '⟩ Scanning aptitude matrix...',
      '⟩ Mapping strengths: [analytical, methodical, detail-oriented]',
      '✓ Profile complete. Recommended track: Defender',
      '',
      '$ cyboch mission start "Operation Dark Harvest"',
      '⟩ Loading mission briefing...',
      '⟩ 3 subtasks · 2 decision branches · 1 evidence upload',
      '✓ Mission active. Good luck, operator.'
    ],
    []
  )

  const [currentLine, setCurrentLine] = useState(0)
  const [displayed, setDisplayed] = useState('')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    
    const full = lines[currentLine]
    let index = 0

    const interval = setInterval(() => {
      index += 1
      setDisplayed(full.slice(0, index))
      if (index >= full.length) {
        clearInterval(interval)
        const timeout = setTimeout(() => {
          setCurrentLine((prev) => (prev + 1) % lines.length)
        }, 1200)
        return () => clearTimeout(timeout)
      }
    }, 45)

    return () => clearInterval(interval)
  }, [currentLine, lines, mounted])

  if (!mounted) {
    return (
      <div className="font-mono text-[12px] leading-relaxed text-[#E2E8F0]">
        <div className="text-[#F59E0B]">$ cyboch init --profile</div>
      </div>
    )
  }

  return (
    <div className="font-mono text-[12px] leading-relaxed text-[#E2E8F0]">
      {lines.slice(0, currentLine).map((line, idx) => (
        <div
          key={idx}
          className={line.startsWith('$') ? 'text-[#F59E0B]' : line.includes('✓') ? 'text-emerald-400' : 'text-sky-400'}
        >
          {line}
        </div>
      ))}
      <div className="flex">
        <span className={displayed.startsWith('$') ? 'text-[#F59E0B]' : 'text-sky-400'}>{displayed}</span>
        <span className="inline-block w-[8px] bg-[#F59E0B] ml-[2px] animate-pulse" />
      </div>
    </div>
  )
})

TerminalTyping.displayName = 'TerminalTyping'

// Animated counter
const StatCounter = memo(function StatCounter({ label, to, suffix = '', prefix = '' }: { label: string; to: number; suffix?: string; prefix?: string }) {
  const [value, setValue] = useState(0)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    
    let frame: number
    const start = performance.now()
    const duration = 900

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(to * eased))
      if (progress < 1) {
        frame = requestAnimationFrame(tick)
      }
    }

    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [to, mounted])

  return (
    <div className="flex flex-col items-start min-w-[90px]">
      <span className="font-heading text-[30px] font-bold text-[#F59E0B] leading-none">
        {prefix}
        {mounted ? value : 0}
        {suffix}
      </span>
      <span className="mt-1 text-[12px] font-medium text-[#E2E8F0]">{label}</span>
    </div>
  )
})

StatCounter.displayName = 'StatCounter'

// Sticky navigation
const NavigationHeader = memo(function NavigationHeader({
  onScrollTo
}: {
  onScrollTo: (id: string) => void
}) {
  const router = useRouter()
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    
    const handler = () => {
      setScrolled(window.scrollY > 10)
    }
    handler()
    window.addEventListener('scroll', handler)
    return () => window.removeEventListener('scroll', handler)
  }, [mounted])

  const handleNavClick = (id: string) => {
    setOpen(false)
    onScrollTo(id)
  }

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-colors duration-300 border-b h-[70px] ${
        scrolled
          ? 'bg-[rgba(6,9,15,0.85)] backdrop-blur-[20px] border-[rgba(255,255,255,0.06)]'
          : 'bg-transparent border-transparent'
      }`}
    >
      <nav className="max-w-[1140px] mx-auto px-6">
        <div className="flex h-[70px] items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-xl bg-[rgba(245,158,11,0.08)] border border-[rgba(245,158,11,0.4)] flex items-center justify-center shadow-[0_0_18px_rgba(245,158,11,0.55)]">
              <Shield className="h-5 w-5 text-[#F59E0B]" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-[17px] font-[700] tracking-[0.18em] text-[#94A3B8] uppercase">
                CybOCH <span className="text-[#F59E0B]">Engine</span>
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-8 text-[13px]">
            <button
              type="button"
              onClick={() => handleNavClick('features')}
              className="text-[#64748B] font-medium hover:text-[#F59E0B] transition-colors duration-200"
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('tracks')}
              className="text-[#64748B] font-medium hover:text-[#F59E0B] transition-colors duration-200"
            >
              Tracks
            </button>
            <button
              type="button"
              onClick={() => router.push('/cohorts')}
              className="text-[#64748B] font-medium hover:text-[#F59E0B] transition-colors duration-200"
            >
              Cohorts
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('pricing')}
              className="text-[#64748B] font-medium hover:text-[#F59E0B] transition-colors duration-200"
            >
              Pricing
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('faq')}
              className="text-[#64748B] font-medium hover:text-[#F59E0B] transition-colors duration-200"
            >
              FAQ
            </button>
          </div>

          <div className="hidden md:flex items-center gap-3">
            <button
              type="button"
              onClick={() => router.push('/login')}
              className="text-[13px] font-medium text-[#64748B] hover:text-[#F59E0B] transition-colors duration-200"
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => router.push('/register')}
              className="relative inline-flex items-center gap-2 rounded-full px-[30px] py-[14px] text-[13px] font-bold text-[#0A0E1A] bg-gradient-to-r from-[#F59E0B] to-[#D97706] shadow-[0_0_24px_rgba(245,158,11,0.55)] hover:shadow-[0_0_30px_rgba(245,158,11,0.7)] hover:-translate-y-0.5 transition-all duration-200"
            >
              <span>Start Free</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          <button
            type="button"
            className="md:hidden inline-flex items-center justify-center rounded-lg border border-[rgba(255,255,255,0.1)] bg-[rgba(10,14,26,0.6)] p-1.5 text-[#E2E8F0]"
            onClick={() => setOpen((o) => !o)}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {open && (
          <div className="md:hidden absolute top-full left-0 right-0 mt-2 mx-4 rounded-2xl bg-[rgba(10,14,26,0.98)] backdrop-blur-xl border border-[rgba(255,255,255,0.1)] shadow-[0_20px_60px_rgba(0,0,0,0.9)] py-4 px-4 space-y-3">
            <button
              type="button"
              onClick={() => handleNavClick('features')}
              className="block w-full text-left text-[#E2E8F0] hover:text-[#F59E0B] text-[13px] font-medium"
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('tracks')}
              className="block w-full text-left text-[#E2E8F0] hover:text-[#F59E0B] text-[13px] font-medium"
            >
              Tracks
            </button>
            <button
              type="button"
              onClick={() => {
                setOpen(false)
                router.push('/cohorts')
              }}
              className="block w-full text-left text-[#E2E8F0] hover:text-[#F59E0B] text-[13px] font-medium"
            >
              Cohorts
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('pricing')}
              className="block w-full text-left text-[#E2E8F0] hover:text-[#F59E0B] text-[13px] font-medium"
            >
              Pricing
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('faq')}
              className="block w-full text-left text-[#E2E8F0] hover:text-[#F59E0B] text-[13px] font-medium"
            >
              FAQ
            </button>
            <div className="pt-2 flex gap-2">
              <button
                type="button"
                onClick={() => router.push('/login')}
                className="flex-1 rounded-full border border-[rgba(255,255,255,0.15)] px-3 py-2 text-xs text-[#E2E8F0] hover:border-[#F59E0B] hover:text-[#F59E0B] transition-colors"
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => router.push('/register')}
                className="flex-1 rounded-full bg-[#F59E0B] px-3 py-2 text-xs font-bold text-[#0A0E1A] shadow-[0_0_20px_rgba(245,158,11,0.6)]"
              >
                Start Free
              </button>
            </div>
          </div>
        )}
      </nav>
    </header>
  )
})

NavigationHeader.displayName = 'NavigationHeader'

// Glass card wrappers
const GlassCard = memo(function GlassCard({
  children,
  className = ''
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={`relative rounded-[18px] border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.03)] backdrop-blur-xl shadow-[0_18px_60px_rgba(0,0,0,0.85)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_22px_70px_rgba(0,0,0,0.95)] ${className}`}
    >
      {children}
    </div>
  )
})

GlassCard.displayName = 'GlassCard'

const FAQItem = memo(function FAQItem({
  question,
  answer,
  isOpen,
  onToggle
}: {
  question: string
  answer: string
  isOpen: boolean
  onToggle: () => void
}) {
  return (
    <div className="border border-white/5 rounded-xl bg-slate-900/40">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 sm:px-5 py-4 text-left"
      >
        <span className="text-sm sm:text-base font-medium text-slate-100">{question}</span>
        <span
          className={`ml-4 inline-flex h-6 w-6 items-center justify-center rounded-full border border-amber-400/40 text-amber-300 text-xs transition-transform ${
            isOpen ? 'rotate-90' : ''
          }`}
        >
          {isOpen ? '▼' : '›'}
        </span>
      </button>
      <div
        className={`px-4 sm:px-5 pb-4 text-xs sm:text-sm text-slate-400 transition-all duration-300 ${
          isOpen ? 'max-h-96 opacity-100 pt-2' : 'max-h-0 opacity-0 overflow-hidden'
        }`}
      >
        {answer}
      </div>
    </div>
  )
})

FAQItem.displayName = 'FAQItem'

const AuthModal = memo(function AuthModal({
  open,
  mode,
  onClose,
  onSwitchMode
}: {
  open: boolean
  mode: 'login' | 'register'
  onClose: () => void
  onSwitchMode: (mode: 'login' | 'register') => void
}) {
  if (!open) return null
  const router = useRouter()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (mode === 'register') {
      router.push('/register')
    } else {
      router.push('/login')
    }
    onClose()
  }

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 backdrop-blur-xl">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(245,158,11,0.12),_transparent_60%),radial-gradient(circle_at_bottom,_rgba(15,23,42,0.85),_transparent_55%)]" />
      <div className="relative mx-4 w-full max-w-md">
        <GlassCard className="overflow-hidden border-white/10 bg-slate-950/80">
          <div className="flex items-center justify-between border-b border-white/5 px-5 py-3">
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-lg bg-amber-500/15 border border-amber-400/40 flex items-center justify-center">
                <Shield className="h-4 w-4 text-amber-400" />
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-semibold tracking-[0.16em] text-slate-400 uppercase">
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                </span>
                <span className="text-[11px] text-slate-500">CybOCH Engine Access</span>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-white/10 bg-slate-900/80 p-1.5 text-slate-400 hover:text-amber-300 hover:border-amber-400/50 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="px-5 pt-5 pb-4 space-y-4">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-100">
                {mode === 'login' ? 'Welcome back, Operator.' : 'Begin your operator journey.'}
              </p>
              <p className="text-xs text-slate-500">
                Authenticate to enter your mission console. We&apos;ll keep this fast and secure.
              </p>
            </div>
            <form className="space-y-3" onSubmit={handleSubmit}>
              {mode === 'register' && (
                <div className="space-y-1.5">
                  <label className="block text-[11px] font-medium text-slate-400">Full Name</label>
                  <input
                    type="text"
                    className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-amber-400/70 focus:ring-1 focus:ring-amber-400/60"
                    placeholder="Ada Cyberkali"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>
              )}
              <div className="space-y-1.5">
                <label className="block text-[11px] font-medium text-slate-400">Email</label>
                <input
                  type="email"
                  className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-amber-400/70 focus:ring-1 focus:ring-amber-400/60"
                  placeholder="you@operator.net"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="block text-[11px] font-medium text-slate-400">Password</label>
                <input
                  type="password"
                  className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-amber-400/70 focus:ring-1 focus:ring-amber-400/60"
                  placeholder={mode === 'login' ? '••••••••' : 'Min. 8 characters, one symbol'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <button
                type="submit"
                className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-amber-400 via-amber-300 to-amber-500 px-3 py-2.5 text-xs font-semibold text-slate-950 shadow-[0_0_24px_rgba(245,158,11,0.7)] hover:shadow-[0_0_28px_rgba(245,158,11,0.85)] transition-shadow"
              >
                {mode === 'login' ? 'Enter Mission Console' : 'Create Mission Profile'}
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </form>
            <div className="pt-2">
              <GoogleSignInButton role="student" mode={mode} />
            </div>
            <div className="flex items-center justify-between pt-1">
              <p className="text-[10px] text-slate-500 max-w-[70%]">
                By continuing you agree to mission-grade security and data handling policies.
              </p>
              <button
                type="button"
                onClick={() => onSwitchMode(mode === 'login' ? 'register' : 'login')}
                className="text-[11px] font-medium text-amber-300 hover:text-amber-200"
              >
                {mode === 'login' ? 'New operator?' : 'Already onboarded?'}
              </button>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  )
})

AuthModal.displayName = 'AuthModal'

const Footer = memo(function Footer() {
  return (
    <footer className="border-t border-white/5 mt-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-4 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-slate-500">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-amber-400" />
          <span>CybOCH Engine · OCH Platform</span>
        </div>
        <div className="flex items-center gap-4">
          <span>© {new Date().getFullYear()} All rights reserved.</span>
          <Link href="/about" className="hover:text-amber-300">
            About
          </Link>
          <Link href="/pricing" className="hover:text-amber-300">
            Pricing
          </Link>
        </div>
      </div>
    </footer>
  )
})

Footer.displayName = 'Footer'

export default function HomePage() {
  const router = useRouter()
  const [tracks, setTracks] = useState<Track[]>([])
  const [authOpen, setAuthOpen] = useState(false)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('register')
  const [showStickyCta, setShowStickyCta] = useState(false)
  const [faqOpenIndex, setFaqOpenIndex] = useState<number | null>(0)
  const [pricingPeriod, setPricingPeriod] = useState<'monthly' | 'yearly'>('monthly')
  const [heroCohorts, setHeroCohorts] = useState<HeroCohort[]>([])
  const [heroCohortIndex, setHeroCohortIndex] = useState(0)
  const [pricingPlans, setPricingPlans] = useState<any[]>([])

  // Fetch tracks from API where available, fall back to defaults
  useEffect(() => {
    let mounted = true
    const loadTracks = async () => {
      try {
        const res = await fetch('/api/profiling/tracks')
        if (!res.ok) throw new Error('failed')
        const data = await res.json()
        if (mounted && Array.isArray(data?.tracks)) {
          setTracks(
            data.tracks.slice(0, 5).map((t: any, idx: number) => ({
              id: String(t.id ?? idx),
              name: String(t.name ?? 'Track'),
              description: String(t.description ?? '')
            }))
          )
        }
      } catch {
        if (mounted) {
          setTracks([
            { id: 'defender', name: 'Defender', description: 'Blue-team resilience, SOC workflows, incident response.' },
            { id: 'offensive', name: 'Offensive', description: 'Red-team operations, exploit chains, adversary simulation.' },
            { id: 'grc', name: 'GRC', description: 'Governance, risk, and compliance for high-trust environments.' },
            { id: 'innovation', name: 'Innovation', description: 'Security R&D, automation, new detection patterns.' },
            { id: 'leadership', name: 'Leadership', description: 'Strategic cyber leadership and program design.' }
          ])
        }
      }
    }
    loadTracks()
    return () => {
      mounted = false
    }
  }, [])

  // Fetch published cohorts for hero slider
  useEffect(() => {
    let mounted = true
    const loadCohorts = async () => {
      try {
        const res = await apiGateway.get('/public/cohorts/', { skipAuth: true })
        const data = res as any
        if (!mounted) return
        const list: HeroCohort[] = (data || []).map((c: any) => ({
          id: String(c.id),
          name: String(c.name),
          start_date: String(c.start_date),
          end_date: String(c.end_date),
          mode: String(c.mode || ''),
        }))
        setHeroCohorts(list)
        setHeroCohortIndex(0)
      } catch {
        if (mounted) {
          setHeroCohorts([])
        }
      }
    }
    loadCohorts()
    return () => {
      mounted = false
    }
  }, [])

  // Fetch pricing plans
  useEffect(() => {
    let mounted = true
    const loadPricing = async () => {
      try {
        const res = await apiGateway.get('/subscription/plans/public', { skipAuth: true })
        if (mounted && Array.isArray(res)) {
          setPricingPlans(res)
        }
      } catch (error) {
        console.error('Failed to load pricing plans:', error)
        if (mounted) {
          setPricingPlans([])
        }
      }
    }
    loadPricing()
    return () => {
      mounted = false
    }
  }, [])

  // Auto-rotate hero cohorts if more than one
  useEffect(() => {
    if (heroCohorts.length <= 1) return
    const id = window.setInterval(() => {
      setHeroCohortIndex((prev) => (prev + 1) % heroCohorts.length)
    }, 7000)
    return () => window.clearInterval(id)
  }, [heroCohorts.length])

  // Sticky CTA visibility
  useEffect(() => {
    const handler = () => {
      const y = window.scrollY
      const maxScroll = document.body.scrollHeight - window.innerHeight
      setShowStickyCta(y > 520 && y < maxScroll - 320)
    }
    handler()
    window.addEventListener('scroll', handler)
    return () => window.removeEventListener('scroll', handler)
  }, [])

  // Simple scroll reveal using Intersection Observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-in')
          }
        })
      },
      { threshold: 0.15 }
    )
    const nodes = document.querySelectorAll('[data-animate]')
    nodes.forEach((n) => observer.observe(n))
    return () => observer.disconnect()
  }, [])

  const handleStartTrial = useMemo(
    () => () => {
      router.push('/register')
    },
    [router]
  )

  const scrollToId = (id: string) => {
    if (typeof window === 'undefined') return
    const el = document.getElementById(id)
    if (!el) return
    const rect = el.getBoundingClientRect()
    const offset = rect.top + window.scrollY - 80
    window.scrollTo({ top: offset, behavior: 'smooth' })
  }

  const handleOpenAuth = (mode: 'login' | 'register') => {
    setAuthMode(mode)
    setAuthOpen(true)
  }

  const journeyStages = [
    'Profiler',
    'Foundations',
    'Beginner',
    'Intermediate',
    'Advanced',
    'Mastery',
    'Marketplace'
  ]

  const faqItems = [
    {
      q: 'What happens after the trial?',
      a: 'After your 14-day free trial, you can choose to subscribe to Starter (monthly plan) or Premium (annual plan) to continue accessing all features. If you don\'t subscribe, your account will revert to limited free access with read-only curriculum and basic features.'
    },
    {
      q: 'Can I switch tracks?',
      a: 'Yes! You can switch between tracks (Defender, Offensive, GRC, Innovation, Leadership) at any time. Your progress in each track is saved, so you can explore multiple paths and return to any track whenever you want.'
    },
    {
      q: 'Do I need to install anything?',
      a: 'No installation required. CybOCH Engine runs entirely in your browser. For hands-on labs and missions, we provide cloud-based environments that you access through your browser. Some advanced missions may require specific tools, which we\'ll guide you through.'
    },
    {
      q: 'How does mentor matching work?',
      a: 'Premium subscribers get matched with experienced mentors based on your track, skill level, and goals. Mentors review your mission submissions, provide feedback, score your work, and guide your progression. Mentorship includes group sessions, 1-on-1 support, and mission reviews.'
    },
    {
      q: 'Missions vs Recipes — what’s the difference?',
      a: 'Missions are real-world cyber operations with scenarios, subtasks, decision branches, and mentor scoring — they build your portfolio and prove capability. Recipes are step-by-step skill guides (tools, commands, code snippets) that help you complete missions. Think: Missions = the test, Recipes = the study materials.'
    },
    {
      q: 'Do I get a certificate?',
      a: 'Yes! Upon completing missions and reaching milestones, you earn certificates and badges. More importantly, you build a professional portfolio that auto-generates from your completed missions, showcasing your skills with proof of work that employers can verify.'
    }
  ]

  const starterPlan = pricingPlans.find(p => p.tier === 'starter')
  const premiumPlan = pricingPlans.find(p => p.tier === 'premium')
  const starterPrice = starterPlan?.price_monthly || 5
  const premiumYearlyPrice = 54
  const premiumMonthlyEquivalent = premiumPlan?.price_monthly || 4.5

  return (
    <div className="min-h-screen bg-[#06090F] text-[#E2E8F0] font-sans" suppressHydrationWarning>
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(10,14,26,1),_transparent_55%),radial-gradient(circle_at_top_left,_rgba(245,158,11,0.12),_transparent_55%),radial-gradient(circle_at_bottom_right,_rgba(56,189,248,0.12),_transparent_55%)]" />
      <div className="pointer-events-none fixed inset-0 -z-10 opacity-[0.03]" style={{backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '50px 50px'}} />

      <NavigationHeader onScrollTo={scrollToId} />

      <main className="pt-[70px]">
        {/* HERO */}
        <section className="relative max-w-[1140px] mx-auto px-4 sm:px-6 py-8 sm:py-12 md:py-16">
          <div className="grid gap-8 lg:gap-10 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] items-center">
            <Reveal>
              <div className="space-y-4 sm:space-y-6 md:space-y-7">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
                  <div className="flex gap-1.5 text-[11px] font-semibold text-white">
                    <span className="h-6 w-6 rounded-full bg-[#1D4ED8] flex items-center justify-center">F</span>
                    <span className="h-6 w-6 rounded-full bg-[#DB2777] flex items-center justify-center">P</span>
                    <span className="h-6 w-6 rounded-full bg-[#10B981] flex items-center justify-center">B</span>
                    <span className="h-6 w-6 rounded-full bg-[#F59E0B] flex items-center justify-center">K</span>
                  </div>
                  <div className="inline-flex items-center gap-2 rounded-full border border-[rgba(245,158,11,0.12)] bg-[rgba(245,158,11,0.06)] px-3 py-1.5 text-[10px] sm:text-[11px] text-[#F59E0B] shadow-[0_0_20px_rgba(245,158,11,0.5)]">
                    <BadgeCheck className="h-3.5 w-3.5 text-[#F59E0B]" />
                    <span className="uppercase tracking-[0.12em] sm:tracking-[0.18em] text-[#F59E0B] font-semibold">
                      127+ operators trained
                    </span>
                  </div>
                </div>
                <div className="space-y-2 sm:space-y-3">
                  <h1
                    className="font-heading text-[clamp(32px,8vw,68px)] font-bold tracking-[-1.5px] sm:tracking-[-2px] leading-[1.1] sm:leading-[1.05]"
                  >
                    <span className="block text-[#E2E8F0]">Your cyber career.</span>
                    <span className="block bg-gradient-to-r from-[#F59E0B] via-[#FBBF24] to-[#F59E0B] bg-clip-text text-transparent">
                      Mission by mission.
                    </span>
                  </h1>
                  <p className="max-w-[460px] text-[14px] sm:text-[16px] leading-[1.7] sm:leading-[1.8] text-[#94A3B8]">
                    Discover your cyber identity. Complete real-world missions. Build a professional portfolio. Grow
                    from beginner to marketplace-ready — guided by mentors every step.
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 items-stretch sm:items-center">
                  <button
                    type="button"
                    onClick={handleStartTrial}
                    className="inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[#F59E0B] to-[#D97706] px-5 sm:px-[30px] py-3 sm:py-[14px] text-[13px] sm:text-[14px] font-bold text-[#0A0E1A] shadow-[0_0_28px_rgba(245,158,11,0.7)] hover:shadow-[0_0_36px_rgba(245,158,11,0.85)] hover:-translate-y-0.5 transition-all duration-200"
                  >
                    <Zap className="h-4 w-4" />
                    <span className="hidden sm:inline">Discover Your Cyber Identity</span>
                    <span className="sm:hidden">Start Free Trial</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => scrollToId('demo')}
                    className="inline-flex items-center justify-center gap-2 rounded-full border border-[rgba(255,255,255,0.15)] bg-[rgba(6,9,15,0.6)] px-5 sm:px-[30px] py-3 sm:py-[14px] text-[13px] sm:text-[14px] font-medium text-[#E2E8F0] hover:border-[rgba(245,158,11,0.6)] hover:text-[#F59E0B] transition-colors duration-200"
                  >
                    <Terminal className="h-4 w-4" />
                    <span>See How It Works</span>
                  </button>
                </div>

                <p className="text-[11px] text-[#64748B] flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center gap-1">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                    <span>14 days free</span>
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                    <span>No credit card</span>
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Cancel anytime</span>
                  </span>
                </p>

                <div className="mt-4 grid grid-cols-2 sm:flex sm:flex-wrap lg:inline-flex items-center gap-4 sm:gap-6 lg:gap-8 rounded-[20px] border border-[rgba(255,255,255,0.06)] bg-[rgba(6,9,15,0.9)] px-4 sm:px-6 lg:px-[32px] py-4 sm:py-5 lg:py-[20px]">
                  <StatCounter label="Free Trial" to={14} suffix=" days" />
                  <div className="hidden sm:block h-10 w-px bg-[rgba(148,163,184,0.35)]" />
                  <StatCounter label="Full Access" to={5} suffix="/mo" prefix="$" />
                  <div className="hidden sm:block h-10 w-px bg-[rgba(148,163,184,0.35)]" />
                  <StatCounter label="Tracks" to={5} />
                  <div className="hidden sm:block h-10 w-px bg-[rgba(148,163,184,0.35)]" />
                  <StatCounter label="Missions" to={40} suffix="+" />
                </div>
              </div>
            </Reveal>

            <Reveal delay={120}>
              <GlassCard className="relative overflow-hidden border-[rgba(245,158,11,0.15)] bg-[rgba(6,9,15,0.8)]">
                <div className="pointer-events-none absolute -top-20 -right-24 h-52 w-52 rounded-full bg-[radial-gradient(circle,_rgba(245,158,11,0.18),_transparent_60%)]" />
                <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.05)] px-4 py-2">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
                    <span className="h-2.5 w-2.5 rounded-full bg-[#F59E0B]/80" />
                    <span className="h-2.5 w-2.5 rounded-full bg-rose-400/80" />
                  </div>
                  <p className="font-mono text-[10px] text-[#64748B]">/opt/cyboch/engine</p>
                </div>
                <div className="px-4 py-3 border-b border-[rgba(255,255,255,0.05)] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Terminal className="h-4 w-4 text-[#F59E0B]" />
                    <span className="font-mono text-[11px] text-[#94A3B8]">mission-console</span>
                  </div>
                  <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium text-emerald-300 border border-emerald-400/30">
                    LIVE
                  </span>
                </div>
                <div className="px-4 py-3 bg-[#0D1117]">
                  <TerminalTyping />
                </div>

                {/* Cohort slider (only when there are published cohorts) */}
                {heroCohorts.length > 0 && (
                  <div className="border-t border-[rgba(255,255,255,0.05)] bg-slate-950/70 px-4 py-3 flex items-center justify-between gap-3">
                    {(() => {
                      const c = heroCohorts[Math.min(heroCohortIndex, heroCohorts.length - 1)]
                      return (
                        <>
                          <div className="min-w-0">
                            <p className="text-[10px] uppercase tracking-[0.18em] text-[#FBBF24] font-semibold mb-1">
                              Now enrolling
                            </p>
                            <p className="text-sm font-semibold text-white truncate" title={c.name}>
                              {c.name}
                            </p>
                            <p className="text-[11px] text-[#94A3B8]">
                              {c.start_date} – {c.end_date} • {c.mode}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => router.push('/cohorts')}
                            className="shrink-0 inline-flex items-center justify-center rounded-full bg-[#F59E0B] px-3 py-1.5 text-[11px] font-semibold text-[#0A0E1A] shadow-[0_0_16px_rgba(245,158,11,0.6)] hover:shadow-[0_0_22px_rgba(245,158,11,0.8)] transition-shadow"
                          >
                            Apply now
                            <ArrowRight className="ml-1 h-3 w-3" />
                          </button>
                        </>
                      )
                    })()}
                  </div>
                )}

                <div className="border-t border-[rgba(255,255,255,0.05)] px-4 py-2 flex items-center justify-between text-[10px] text-[#64748B]">
                  <span>Profiler · Tracks · Missions · Marketplace</span>
                  <span className="inline-flex items-center gap-1 text-[#F59E0B]">
                    <Shield className="h-3 w-3" />
                    High-Trust Mode
                  </span>
                </div>
              </GlassCard>
            </Reveal>
          </div>
        </section>

        {/* TRUSTED BY */}
        <section className="max-w-[1140px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-16">
          <Reveal>
            <div className="text-center space-y-2">
              <p className="text-[10px] uppercase tracking-[0.22em] text-[#64748B] font-semibold">
                Mentors from
              </p>
              <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-[12px] text-[#E5E7EB]">
                <span className="opacity-70">Serianu</span>
                <span className="opacity-70">Safaricom</span>
                <span className="opacity-70">Deloitte</span>
                <span className="opacity-70">KPMG</span>
                <span className="opacity-70">Africa CERT</span>
              </div>
            </div>
          </Reveal>
        </section>

        {/* WHO IS THIS FOR */}
        <section id="who" className="max-w-[1140px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-16">
          <Reveal>
            <div className="flex flex-col gap-6">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.24em] text-[#FBBF24]">Who is this for</p>
                <h2 className="mt-1 font-heading text-[40px] font-bold tracking-[-1.2px] text-[#E2E8F0]">
                  Built for those ready to <span className="text-[#F59E0B]">do the work</span>
                </h2>
                <p className="text-[14px] text-[#94A3B8]">
                  No matter where you start — if you&apos;re serious, there&apos;s a path here.
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-4">
                <GlassCard className="border-[rgba(255,255,255,0.07)] bg-[rgba(6,9,15,0.7)] hover:border-[rgba(245,158,11,0.4)]">
                  <div className="p-5 space-y-2.5">
                    <div className="flex items-center justify-between gap-3">
                      <div className="h-9 w-9 rounded-xl bg-[rgba(15,23,42,0.9)] flex items-center justify-center text-[#F59E0B]">
                        <GraduationCap className="h-5 w-5" />
                      </div>
                      <span className="rounded-full border border-[rgba(255,255,255,0.1)] bg-[rgba(10,14,26,0.7)] px-2 py-0.5 text-[9px] uppercase tracking-[0.18em] text-[#64748B]">
                        Operator profile
                      </span>
                    </div>
                    <h3 className="text-[15px] font-bold text-[#E2E8F0]">Fresh Graduates</h3>
                    <p className="text-[13px] text-[#94A3B8]">
                      Turn theory into proof. Build what employers actually want to see.
                    </p>
                  </div>
                </GlassCard>

                <GlassCard className="border-[rgba(255,255,255,0.07)] bg-[rgba(6,9,15,0.7)] hover:border-[rgba(245,158,11,0.4)]">
                  <div className="p-5 space-y-2.5">
                    <div className="flex items-center justify-between gap-3">
                      <div className="h-9 w-9 rounded-xl bg-[rgba(15,23,42,0.9)] flex items-center justify-center text-[#38BDF8]">
                        <Repeat className="h-5 w-5" />
                      </div>
                      <span className="rounded-full border border-[rgba(255,255,255,0.1)] bg-[rgba(10,14,26,0.7)] px-2 py-0.5 text-[9px] uppercase tracking-[0.18em] text-[#64748B]">
                        Operator profile
                      </span>
                    </div>
                    <h3 className="text-[15px] font-bold text-[#E2E8F0]">Career Switchers</h3>
                    <p className="text-[13px] text-[#94A3B8]">
                      Structure your transition with clear milestones and mentor support.
                    </p>
                  </div>
                </GlassCard>

                <GlassCard className="border-[rgba(255,255,255,0.07)] bg-[rgba(6,9,15,0.7)] hover:border-[rgba(245,158,11,0.4)]">
                  <div className="p-5 space-y-2.5">
                    <div className="flex items-center justify-between gap-3">
                      <div className="h-9 w-9 rounded-xl bg-[rgba(15,23,42,0.9)] flex items-center justify-center text-[#22C55E]">
                        <Laptop className="h-5 w-5" />
                      </div>
                      <span className="rounded-full border border-[rgba(255,255,255,0.1)] bg-[rgba(10,14,26,0.7)] px-2 py-0.5 text-[9px] uppercase tracking-[0.18em] text-[#64748B]">
                        Operator profile
                      </span>
                    </div>
                    <h3 className="text-[15px] font-bold text-[#E2E8F0]">Self-Taught Hackers</h3>
                    <p className="text-[13px] text-[#94A3B8]">
                      Turn scattered skills into a credible, portfolio-backed profile.
                    </p>
                  </div>
                </GlassCard>

                <GlassCard className="border-[rgba(255,255,255,0.07)] bg-[rgba(6,9,15,0.7)] hover:border-[rgba(245,158,11,0.4)]">
                  <div className="p-5 space-y-2.5">
                    <div className="flex items-center justify-between gap-3">
                      <div className="h-9 w-9 rounded-xl bg-[rgba(15,23,42,0.9)] flex items-center justify-center text-[#F97316]">
                        <BarChartIcon className="h-5 w-5" />
                      </div>
                      <span className="rounded-full border border-[rgba(255,255,255,0.1)] bg-[rgba(10,14,26,0.7)] px-2 py-0.5 text-[9px] uppercase tracking-[0.18em] text-[#64748B]">
                        Operator profile
                      </span>
                    </div>
                    <h3 className="text-[15px] font-bold text-[#E2E8F0]">Rising Professionals</h3>
                    <p className="text-[13px] text-[#94A3B8]">
                      Level up with advanced missions and leadership track access.
                    </p>
                  </div>
                </GlassCard>
              </div>
            </div>
          </Reveal>
        </section>

        {/* JOURNEY TIMELINE */}
        <section className="relative py-8 sm:py-12 md:py-16 bg-gradient-to-b from-[#06090F] to-[#0A0E1A]">
          <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{backgroundImage: 'linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px'}} />
          <div className="max-w-[1140px] mx-auto px-4 sm:px-6">
            <Reveal>
              <div className="text-center mb-8 sm:mb-12 md:mb-[70px]">
                <p className="font-heading text-[12px] uppercase tracking-[2px] text-[#F59E0B] font-bold mb-4">
                  The Journey
                </p>
                <h2 className="font-heading text-[clamp(32px,4vw,48px)] font-bold tracking-[-1.5px] leading-[1.1] text-[#E2E8F0] mb-[18px]">
                  From discovery to deployment
                </h2>
                <p className="font-sans text-[16px] text-[#94A3B8] leading-[1.7] max-w-[500px] mx-auto">
                  Seven stages. Personalized to your strengths.
                </p>
              </div>
            </Reveal>
            <Reveal delay={100}>
              <div className="relative overflow-x-auto pb-4">
                <div className="absolute top-[27px] left-0 right-0 h-[2px] bg-gradient-to-r from-[rgba(245,158,11,0.3)] via-[rgba(245,158,11,0.15)] to-[rgba(245,158,11,0.1)] z-0 hidden md:block" />
                <div className="flex md:items-start md:justify-between gap-3 md:gap-4 min-w-max md:min-w-0">
                  {journeyStages.map((stage, idx) => (
                    <div
                      key={stage}
                      className="relative z-10 flex flex-col items-center min-w-[90px] md:min-w-[120px] transition-transform duration-300 hover:-translate-y-1.5 group"
                      style={{animationDelay: `${idx * 0.1}s`}}
                    >
                      <div className="w-[44px] h-[44px] md:w-[54px] md:h-[54px] rounded-full bg-[rgba(245,158,11,0.08)] border-2 border-[rgba(245,158,11,0.25)] flex items-center justify-center font-heading text-[14px] md:text-[16px] font-bold text-[#F59E0B] transition-all duration-300 group-hover:bg-[rgba(245,158,11,0.15)] group-hover:border-[#F59E0B] group-hover:shadow-[0_0_20px_rgba(245,158,11,0.3)] group-hover:scale-105">
                        {String(idx + 1).padStart(2, '0')}
                      </div>
                      <p className="mt-3 md:mt-4 font-sans text-[11px] md:text-[13px] font-semibold text-[#94A3B8] text-center transition-colors duration-200 group-hover:text-[#E2E8F0]">
                        {stage}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </Reveal>
          </div>
        </section>

        {/* PLATFORM FEATURES */}
        <section id="features" className="max-w-[1140px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-16">
          <Reveal>
            <div className="flex flex-col gap-6">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.24em] text-[#FBBF24]">Platform Features</p>
                <h2 className="mt-1 font-heading text-[40px] font-bold tracking-[-1.2px] text-[#E2E8F0]">
                  Everything to become <span className="text-[#F59E0B]">mission-ready</span>
                </h2>
                <p className="text-[14px] text-[#94A3B8]">
                  Not a course library. A complete talent engine.
                </p>
              </div>
              <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
                {[
                  {
                    label: 'Start Here',
                    title: 'Cyber Talent Profiler',
                    icon: Target,
                    desc: 'AI-powered assessment mapping strengths, aptitude, and work style to a personalized learning blueprint.'
                  },
                  {
                    label: 'Core Engine',
                    title: 'Mission-Driven Learning',
                    icon: Zap,
                    desc: 'Real-world cyber simulations with branching decisions, subtasks, evidence submission, and mentor-scored rubrics.'
                  },
                  {
                    label: 'Skill Building',
                    title: 'Recipe Micro-Skills',
                    icon: BookOpen,
                    desc: 'Step-by-step guides, code snippets, and tool walkthroughs that help you complete missions.'
                  },
                  {
                    label: 'Human-Powered',
                    title: 'Mentor-Guided Growth',
                    icon: Users,
                    desc: 'Experienced professionals review your work, score missions, and guide your progression through every stage.'
                  },
                  {
                    label: 'Proof of Work',
                    title: 'Professional Portfolio',
                    icon: Trophy,
                    desc: 'Auto-generated from missions and reflections. Skill radar, gap detection, PDF export, and public profile.'
                  },
                  {
                    label: 'Earn & Grow',
                    title: 'OCH Marketplace',
                    icon: TrendingUp,
                    desc: 'Mission-proven talent meets real work. Microtasks, projects, and team-based engagements from day one.'
                  }
                ].map((f) => (
                  <GlassCard key={f.title} className="border-[rgba(15,23,42,1)] bg-[rgba(6,9,15,0.95)]">
                    <div className="p-5 space-y-3">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#64748B]">
                        {f.label}
                      </p>
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-xl bg-[#020617] flex items-center justify-center text-[#F59E0B]">
                          <f.icon className="h-4 w-4" />
                        </div>
                        <h3 className="text-[16px] font-semibold text-[#E2E8F0]">{f.title}</h3>
                      </div>
                      <p className="text-[13px] leading-[1.7] text-[#94A3B8]">{f.desc}</p>
                    </div>
                  </GlassCard>
                ))}
              </div>
            </div>
          </Reveal>
        </section>

        {/* FIVE TRACKS */}
        <section id="tracks" className="max-w-[1140px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-16">
          <Reveal>
            <div className="flex flex-col gap-6">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.24em] text-[#FBBF24]">Five Tracks</p>
                <h2 className="mt-1 font-heading text-[36px] font-bold tracking-[-1.1px] text-[#E2E8F0]">
                  Choose your <span className="text-[#F59E0B]">operator path</span>
                </h2>
                <p className="text-[14px] text-[#94A3B8]">
                  The Profiler recommends your fit. Each progresses Beginner → Mastery.
                </p>
              </div>
              <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
                {[
                  {
                    id: 'defender',
                    name: 'Defender',
                    subtitle: 'SOC, detection, IR, threat management.'
                  },
                  {
                    id: 'offensive',
                    name: 'Offensive',
                    subtitle: 'Ethical hacking, red-team, exploitation.'
                  },
                  {
                    id: 'grc',
                    name: 'GRC',
                    subtitle: 'Governance, risk, compliance, audit.'
                  },
                  {
                    id: 'innovation',
                    name: 'Innovation',
                    subtitle: 'Cloud, automation, scripting, AI/ML.'
                  },
                  {
                    id: 'leadership',
                    name: 'Leadership',
                    subtitle: 'Crisis comms, influence, VIP identity.'
                  }
                ].map((t) => (
                  <GlassCard
                    key={t.id}
                    className="border-[rgba(15,23,42,1)] bg-[rgba(6,9,15,0.95)] hover:border-[rgba(245,158,11,0.6)]"
                  >
                    <button
                      type="button"
                      className="flex h-full w-full flex-col items-start p-4 text-left"
                      onClick={() => router.push('/onboarding/ai-profiler')}
                    >
                      <h3 className="text-[15px] font-semibold text-[#E2E8F0]">{t.name}</h3>
                      <p className="mt-1 text-[12px] text-[#94A3B8]">{t.subtitle}</p>
                    </button>
                  </GlassCard>
                ))}
              </div>
              <div>
                <button
                  type="button"
                  onClick={() => router.push('/onboarding/ai-profiler')}
                  className="mt-2 inline-flex items-center justify-center rounded-[999px] border border-[#F59E0B] px-5 py-2.5 text-[13px] font-semibold text-[#F59E0B] hover:bg-[rgba(245,158,11,0.08)] transition-colors"
                >
                  Find Your Path →
                </button>
              </div>
            </div>
          </Reveal>
        </section>

        {/* MISSIONS SECTION - NOT COURSES */}
        <section id="demo" className="max-w-[1140px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-16">
          <Reveal>
            <div className="space-y-6">
              <div className="space-y-2">
                <h2 className="font-['Space_Grotesk'] text-[clamp(32px,4vw,44px)] font-bold tracking-[-1.5px] text-[#E2E8F0]">
                  Not courses. <span className="text-[#F59E0B]">Operations.</span>
                </h2>
                <p className="text-[14px] text-[#94A3B8]">
                  Every mission simulates real cyber work. Click through to see.
                </p>
              </div>
              <GlassCard className="border-[rgba(15,23,42,1)] bg-[#020617] rounded-[20px] overflow-hidden">
                <MissionDemo />
              </GlassCard>
            </div>
          </Reveal>
        </section>

        {/* YOUR FIRST 14 DAYS */}
        <section className="max-w-[1140px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-16">
          <Reveal>
            <div className="space-y-8">
              <div className="space-y-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#FBBF24]">
                  Your first 14 days
                </p>
                <h2 className="font-['Space_Grotesk'] text-[clamp(30px,4vw,40px)] font-bold tracking-[-1.2px] text-[#E2E8F0]">
                  What you’ll accomplish — <span className="text-[#F59E0B]">before you pay</span>
                </h2>
                <p className="text-[13px] text-[#94A3B8]">
                  Your free trial isn&apos;t a teaser. It&apos;s a real transformation window.
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-4">
                {[
                  {
                    badge: 'Day 1–2',
                    badgeColor: 'bg-[rgba(245,158,11,0.15)] text-[#F59E0B]',
                    title: 'Discover Your Identity',
                    items: [
                      'Complete Cyber Talent Profiler',
                      'Get Personalized Blueprint',
                      'Recommended track & difficulty',
                      'First portfolio entry'
                    ]
                  },
                  {
                    badge: 'Day 3–5',
                    badgeColor: 'bg-[rgba(59,130,246,0.18)] text-[#60A5FA]',
                    title: 'Learn the Methodology',
                    items: [
                      'Complete Foundations',
                      'Understand missions & recipes',
                      'Confirm your track path',
                      'Set initial goals'
                    ]
                  },
                  {
                    badge: 'Day 6–10',
                    badgeColor: 'bg-[rgba(168,85,247,0.2)] text-[#A855F7]',
                    title: 'Start Your Track',
                    items: [
                      'Begin learning modules',
                      'Complete first quizzes',
                      'Start first mini-mission',
                      'Get first mentor feedback'
                    ]
                  },
                  {
                    badge: 'Day 11–14',
                    badgeColor: 'bg-[rgba(16,185,129,0.2)] text-[#22C55E]',
                    title: 'Build Momentum',
                    items: [
                      'Explore Recipe library',
                      'Access Cross-Track programs',
                      'Portfolio taking shape',
                      'Ready to commit'
                    ]
                  }
                ].map((card) => (
                  <GlassCard
                    key={card.title}
                    className="border-[rgba(15,23,42,1)] bg-[rgba(6,9,15,0.95)] rounded-[20px]"
                  >
                    <div className="p-5 space-y-3">
                      <span
                        className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold ${card.badgeColor}`}
                      >
                        {card.badge}
                      </span>
                      <h3 className="text-[16px] font-semibold text-[#E2E8F0]">{card.title}</h3>
                      <ul className="space-y-1.5 text-[13px] text-[#CBD5F5]">
                        {card.items.map((item) => (
                          <li key={item} className="flex items-start gap-2">
                            <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#F59E0B]" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </GlassCard>
                ))}
              </div>
            </div>
          </Reveal>
        </section>

        {/* WHY WE BUILT THIS */}
        <section className="max-w-[1140px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-16">
          <Reveal>
            <div className="space-y-6">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#FBBF24]">
                Why we built this
              </p>
              <h2 className="font-['Space_Grotesk'] text-[clamp(32px,4vw,42px)] font-bold leading-[1.1] tracking-[-1.2px] text-[#E2E8F0]">
                The elevator has to{' '}
                <span className="text-[#F59E0B]">go back down</span>
              </h2>
              <div className="mt-2 border-l-[3px] border-[#F59E0B] pl-6">
                <p className="text-[15px] leading-[1.8] text-[#CBD5F5]">
                  Africa has 500,000+ unfilled cybersecurity positions. The talent exists — the structure to develop it
                  doesn&apos;t. We built CybOCH Engine because the world doesn&apos;t need another course. It needs a
                  system that takes a curious mind and turns them into a mission-ready professional — with mentors,
                  proof of work, and a path to real employment.
                </p>
              </div>
              <div className="flex items-center gap-3 pt-3">
                <div className="h-9 w-9 rounded-full bg-[#F59E0B] flex items-center justify-center text-sm font-bold text-[#020617]">
                  M
                </div>
                <div className="text-[11px] leading-snug">
                  <p className="font-semibold text-[#E2E8F0]">Martin K.</p>
                  <p className="text-[#94A3B8]">Founder, Ongoza Cyber Hub</p>
                </div>
              </div>
            </div>
          </Reveal>
        </section>

        {/* SINGLE TESTIMONIAL */}
        <section className="max-w-[1140px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-14">
          <Reveal>
            <div className="text-center space-y-4">
              <div className="flex justify-center text-[#FBBF24]">
                <Quote className="h-6 w-6" />
              </div>
              <p className="text-[18px] md:text-[20px] leading-[1.8] text-[#E5E7EB] max-w-[760px] mx-auto">
                The missions changed everything. I stopped collecting certificates and started building proof of what I
                can actually do.
              </p>
              <p className="text-[13px] font-semibold text-[#F9FAFB]">
                Fatima N. <span className="text-[#F59E0B]"> GRC · Cohort Alpha</span>
              </p>
            </div>
          </Reveal>
        </section>

        {/* PRICING */}
        <section id="pricing" className="max-w-[1140px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-16">
          <Reveal>
            <div className="space-y-8">
              <div className="space-y-3 text-center">
                <p className="text-[11px] uppercase tracking-[0.24em] text-[#64748B]">Pricing</p>
                <h2 className="font-['Space_Grotesk'] text-[clamp(30px,4vw,40px)] font-bold tracking-[-1.2px] text-[#E2E8F0]">
                  Less than coffee. <span className="text-[#F59E0B]">More than a degree.</span>
                </h2>
                <p className="text-[13px] text-[#94A3B8]">
                  Full access from day one. No feature gates. No hidden costs.
                </p>
              </div>

              <div className="flex justify-center mb-4">
                <div className="inline-flex items-center rounded-full border border-[rgba(148,163,184,0.4)] bg-[rgba(6,9,15,0.9)] p-1 text-[11px]">
                  <span
                    className={`cursor-pointer rounded-full px-3 py-1.5 ${
                      pricingPeriod === 'monthly'
                        ? 'bg-[rgba(15,23,42,1)] text-[#E2E8F0] font-semibold'
                        : 'text-[#94A3B8]'
                    }`}
                    onClick={() => setPricingPeriod('monthly')}
                  >
                    Monthly
                  </span>
                  <span
                    className={`cursor-pointer rounded-full px-3 py-1.5 ${
                      pricingPeriod === 'yearly'
                        ? 'bg-[#F59E0B] text-[#020617] font-semibold'
                        : 'text-[#94A3B8]'
                    }`}
                    onClick={() => setPricingPeriod('yearly')}
                  >
                    Annual — Save 17%
                  </span>
                </div>
              </div>

              <div className="grid gap-4 grid-cols-1 md:grid-cols-3 items-stretch">
                {/* Free Trial */}
                <GlassCard className="border-[rgba(15,23,42,1)] bg-[rgba(6,9,15,0.95)] rounded-[22px]">
                  <div className="p-6 space-y-4">
                    <div className="space-y-1">
                      <h3 className="text-[16px] font-semibold text-[#E2E8F0]">Free Trial</h3>
                      <p className="text-[12px] text-[#94A3B8]">Full access. No credit card needed.</p>
                    </div>
                    <div className="flex items-baseline gap-1 text-[#F9FAFB]">
                      <span className="text-[30px] font-bold">$0</span>
                      <span className="text-[13px] text-[#94A3B8]">/ 14 days</span>
                    </div>
                    <ul className="space-y-1.5 text-[13px] text-[#E2E8F0]">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>Cyber Talent Profiler</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>Foundations access</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>Begin your track</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>Missions &amp; recipes</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>Mentor access</span>
                      </li>
                    </ul>
                    <button
                      type="button"
                      onClick={handleStartTrial}
                      className="mt-3 inline-flex w-full items-center justify-center rounded-[999px] border border-[#F59E0B] px-4 py-2.5 text-[13px] font-semibold text-[#F59E0B] hover:bg-[rgba(245,158,11,0.08)] transition-colors"
                    >
                      Start Free
                    </button>
                  </div>
                </GlassCard>

                {/* Starter */}
                {starterPlan && (
                  <GlassCard className="border-[rgba(15,23,42,1)] bg-[rgba(6,9,15,0.95)] rounded-[22px]">
                    <div className="p-6 space-y-4">
                      <div className="space-y-1">
                        <h3 className="text-[16px] font-semibold text-[#E2E8F0]">Starter</h3>
                        <p className="text-[12px] text-[#94A3B8]">Monthly subscription</p>
                      </div>
                      <div className="flex items-baseline gap-1 text-[#F9FAFB]">
                        <span className="text-[30px] font-bold">${starterPrice}</span>
                        <span className="text-[13px] text-[#94A3B8]">/ month</span>
                      </div>
                      <ul className="space-y-1.5 text-[13px] text-[#E2E8F0]">
                        <li className="flex items-start gap-2">
                          <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                          <span>All trial features</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                          <span>AI-only missions</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                          <span>Limited portfolio</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                          <span>Basic TalentScope</span>
                        </li>
                      </ul>
                      <button
                        type="button"
                        onClick={handleStartTrial}
                        className="mt-3 inline-flex w-full items-center justify-center rounded-[999px] border border-[#F59E0B] px-4 py-2.5 text-[13px] font-semibold text-[#F59E0B] hover:bg-[rgba(245,158,11,0.08)] transition-colors"
                      >
                        Get Started
                      </button>
                    </div>
                  </GlassCard>
                )}

                {/* Premium */}
                {premiumPlan && (
                  <GlassCard className="relative border-[rgba(245,158,11,0.5)] bg-[rgba(15,23,42,1)] rounded-[24px]">
                    <div className="absolute -top-3 right-4 rounded-full bg-[#F59E0B] px-3 py-1 text-[10px] font-semibold text-[#020617] shadow-[0_10px_30px_rgba(245,158,11,0.6)]">
                      Best Value
                    </div>
                    <div className="p-6 space-y-4">
                      <div className="space-y-1">
                        <h3 className="text-[16px] font-semibold text-[#F9FAFB]">Premium</h3>
                        <p className="text-[12px] text-[#E5E7EB]">Annual subscription</p>
                      </div>
                      <div className="flex items-baseline gap-1 text-[#FBBF24]">
                        <span className="text-[30px] font-bold">${premiumYearlyPrice}</span>
                        <span className="text-[13px] text-[#E5E7EB]">/ year</span>
                      </div>
                      <p className="text-[11px] text-[#22C55E]">💰 Save 10% • Equivalent to ${premiumMonthlyEquivalent}/month</p>
                      <ul className="space-y-1.5 text-[13px] text-[#E5E7EB]">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>All tiers &amp; tracks</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>Unlimited missions &amp; recipes</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>Full mentor access</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>Portfolio &amp; public profile</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                        <span>VIP Leadership Academy</span>
                      </li>
                        <li className="flex items-start gap-2">
                          <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                          <span>Marketplace access</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <CheckCircle className="mt-[3px] h-3.5 w-3.5 text-[#22C55E]" />
                          <span>Priority mentor matching</span>
                        </li>
                      </ul>
                      <button
                        type="button"
                        onClick={handleStartTrial}
                        className="mt-3 inline-flex w-full items-center justify-center rounded-[999px] bg-[#F59E0B] px-4 py-2.5 text-[13px] font-semibold text-[#020617] shadow-[0_10px_40px_rgba(245,158,11,0.7)] hover:bg-[#F97316] transition-colors"
                      >
                        Get Full Access →
                      </button>
                    </div>
                  </GlassCard>
                )}
              </div>
            </div>
          </Reveal>
        </section>

        {/* FAQ */}
        <section id="faq" className="max-w-[800px] mx-auto px-4 sm:px-6 pb-8 sm:pb-12 md:pb-14">
          <Reveal>
            <div className="space-y-6">
              <h2 className="text-center font-['Space_Grotesk'] text-[clamp(28px,4vw,36px)] font-bold tracking-[-1.2px] text-[#E2E8F0]">
                Questions before you start
              </h2>
              <div className="space-y-2.5">
                {faqItems.map((item, idx) => (
                  <FAQItem
                    key={item.q}
                    question={item.q}
                    answer={item.a}
                    isOpen={faqOpenIndex === idx}
                    onToggle={() => setFaqOpenIndex(faqOpenIndex === idx ? null : idx)}
                  />
                ))}
              </div>
            </div>
          </Reveal>
        </section>

        {/* FINAL CTA */}
        <section className="max-w-[640px] mx-auto px-4 sm:px-6 pb-12 sm:pb-16 md:pb-20 text-center">
          <Reveal>
            <div className="space-y-5">
              <h2 className="font-['Space_Grotesk'] text-[clamp(30px,4vw,40px)] font-bold tracking-[-1.2px] text-[#E5E7EB]">
                Ready for your <span className="text-[#F59E0B]">first mission?</span>
              </h2>
              <p className="text-[14px] text-[#CBD5F5]">
                14 days free. No credit card. Take the Profiler and discover where you belong.
              </p>
              <button
                type="button"
                onClick={() => router.push('/onboarding/ai-profiler')}
                className="mt-2 inline-flex items-center justify-center rounded-[999px] bg-[#F59E0B] px-8 py-3 text-[14px] font-semibold text-[#020617] shadow-[0_10px_35px_rgba(245,158,11,0.7)] hover:bg-[#F97316] transition-colors"
              >
                Start Your Mission →
              </button>
            </div>
          </Reveal>
        </section>
      </main>

      {/* Sticky Bottom CTA */}
      {showStickyCta && !authOpen && (
        <div className="fixed inset-x-0 bottom-3 z-40 px-3 sm:px-0">
          <div className="mx-auto max-w-md sm:max-w-xl">
            <GlassCard className="border-amber-400/30 bg-slate-950/95">
              <div className="flex flex-col sm:flex-row items-center gap-3 px-4 py-3 sm:px-5 sm:py-3">
                <div className="flex-1 text-[11px] sm:text-xs text-slate-300">
                  <p className="font-medium text-slate-100">Ready for your first mission?</p>
                  <p className="text-slate-500">
                    14 days free · $5/mo after · cancel anytime.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleStartTrial}
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-amber-400 via-amber-300 to-amber-500 px-4 py-2 text-xs font-semibold text-slate-950 shadow-[0_0_22px_rgba(245,158,11,0.7)]"
                >
                  Start Free →
                </button>
              </div>
            </GlassCard>
          </div>
        </div>
      )}

      <Footer />

    </div>
  )
}

function MissionDemo() {
  const [tab, setTab] = useState<'briefing' | 'subtasks' | 'evidence' | 'mentor' | 'portfolio'>('briefing')

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 px-4 sm:px-5 pt-4">
        <div className="flex items-center gap-2 text-[13px] font-semibold text-[#E5E7EB]">
          <span className="h-2 w-2 rounded-full bg-[#22C55E]" />
          <span>MISSION: Operation Dark Harvest</span>
        </div>
        <span className="inline-flex items-center rounded-full bg-[#F59E0B] px-3 py-1 text-[11px] font-semibold text-[#020617]">
          Defender · Beginner
        </span>
      </div>

      <div className="px-4 sm:px-5 overflow-x-auto">
        <div className="flex gap-4 sm:gap-6 border-b border-[rgba(148,163,184,0.4)] text-[11px] sm:text-[12px] text-[#CBD5F5] min-w-max">
          {[
            { id: 'briefing', label: 'Briefing' },
            { id: 'subtasks', label: 'Subtasks' },
            { id: 'evidence', label: 'Evidence' },
            { id: 'mentor', label: 'Mentor Review' },
            { id: 'portfolio', label: 'Portfolio' }
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id as any)}
              className={`relative px-1 py-3 ${
                tab === t.id ? 'text-[#F59E0B]' : 'text-[#9CA3AF]'
              }`}
            >
              <span>{t.label}</span>
              {tab === t.id && (
                <span className="absolute inset-x-0 -bottom-px h-[2px] bg-[#F59E0B]" />
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 sm:px-5 pb-5 text-[11px] sm:text-[12px] text-[#E5E7EB] space-y-3">
        {tab === 'briefing' && (
          <div className="space-y-2">
            <p className="text-[10px] font-semibold tracking-[0.18em] text-[#F59E0B] uppercase">Scenario</p>
            <p className="text-[#E5E7EB]">
              A regional bank&apos;s SIEM has flagged unusual DNS queries to a domain registered 48 hours ago. Your SOC
              lead suspects data exfiltration. You are the first analyst on shift.
            </p>
            <div className="flex flex-wrap gap-2 pt-2 text-[11px]">
              <span className="rounded-full bg-[#0B1120] px-3 py-1 text-[#38BDF8]">DNS Analysis</span>
              <span className="rounded-full bg-[#0B1120] px-3 py-1 text-[#F97373]">Threat Intel</span>
              <span className="rounded-full bg-[#0B1120] px-3 py-1 text-[#A855F7]">SIEM Triage</span>
            </div>
            <div className="mt-3 rounded-[10px] bg-[#020617] border border-[rgba(148,163,184,0.5)] p-3 space-y-1.5">
              <p className="text-[10px] font-semibold tracking-[0.16em] text-[#9CA3AF] uppercase">Objectives</p>
              <p className="text-[12px] text-[#E5E7EB]">
                1. Analyze the flagged DNS logs 2. Determine if exfiltration is occurring 3. Document findings and
                recommend response
              </p>
            </div>
          </div>
        )}
        {tab === 'subtasks' && (
          <div className="space-y-2">
            <div className="flex items-center justify-between rounded-[10px] bg-[#020617] px-3 py-3 border border-[rgba(15,23,42,1)]">
              <div className="space-y-1 text-[12px]">
                <p className="font-semibold text-[#E5E7EB]">Subtask 1: Extract &amp; filter DNS logs</p>
                <p className="text-[11px] text-[#9CA3AF]">Recipe linked: &quot;SIEM Log Parsing with Splunk&quot;</p>
              </div>
              <span className="text-[#F59E0B] text-[18px] leading-none">↠</span>
            </div>
            <div className="flex items-center justify-between rounded-[10px] bg-[#020617] px-3 py-3 border border-[rgba(15,23,42,1)]">
              <div className="space-y-1 text-[12px]">
                <p className="font-semibold text-[#E5E7EB]">Subtask 2: Cross-reference with threat intel</p>
                <p className="text-[11px] text-[#9CA3AF]">
                  Decision branch: Is the domain in known IOC feeds?
                </p>
              </div>
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#111827] text-[11px] font-semibold text-[#E5E7EB]">
                3
              </span>
            </div>
            <div className="flex items-center justify-between rounded-[10px] bg-[#020617] px-3 py-3 border border-[rgba(31,41,55,1)] opacity-70">
              <div className="space-y-1 text-[12px]">
                <p className="font-semibold text-[#E5E7EB]">Subtask 3: Draft incident summary</p>
                <p className="text-[11px] text-[#9CA3AF]">Locked until subtask 2 complete</p>
              </div>
              <span className="text-[18px] text-[#4B5563]">
                <Lock className="h-4 w-4" />
              </span>
            </div>
          </div>
        )}
        {tab === 'evidence' && (
          <div className="space-y-2">
            <div className="rounded-[14px] border border-dashed border-[rgba(245,158,11,0.5)] bg-[#020617] px-6 py-8 text-center space-y-2">
              <div className="flex justify-center text-[#F59E0B]">
                <Paperclip className="h-6 w-6" />
              </div>
              <p className="text-[14px] font-semibold text-[#E5E7EB]">Upload Evidence</p>
              <p className="text-[12px] text-[#9CA3AF]">
                Scripts, reports, logs, screenshots — real artifacts proving capability
              </p>
            </div>
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between rounded-[12px] bg-[#020817] px-4 py-3 text-[12px]">
                <div className="flex items-center gap-3">
                  <span className="h-6 w-5 rounded bg-[#0F172A]" />
                  <span className="text-[#E5E7EB]">dns_analysis_report.pdf</span>
                </div>
                <span className="text-[11px] font-semibold text-[#22C55E]">Uploaded</span>
              </div>
              <div className="flex items-center justify-between rounded-[12px] bg-[#020817] px-4 py-3 text-[12px]">
                <div className="flex items-center gap-3">
                  <span className="h-6 w-5 rounded bg-[#0F172A]" />
                  <span className="text-[#E5E7EB]">splunk_query.spl</span>
                </div>
                <span className="text-[11px] font-semibold text-[#22C55E]">Uploaded</span>
              </div>
            </div>
          </div>
        )}
        {tab === 'mentor' && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[12px]">
              <p className="text-[#E5E7EB]">
                Mission Score: <span className="font-semibold">87/100</span>
              </p>
              <span className="rounded-full bg-[#22C55E] px-3 py-1 text-[11px] font-semibold text-[#020617]">
                APPROVED
              </span>
            </div>
            <div className="mt-2 rounded-[12px] bg-[#020617] border border-[rgba(34,197,94,0.5)] px-4 py-3 space-y-2">
              <p className="text-[10px] font-semibold tracking-[0.16em] text-[#9CA3AF] uppercase">Mentor Feedback</p>
              <p className="text-[12px] text-[#E5E7EB]">
                &quot;Strong log analysis and clear methodology. For next time, consider enriching IOC data with WHOIS
                before concluding. Your incident summary was concise — good instinct for executive communication.&quot;
              </p>
              <p className="text-[11px] text-[#9CA3AF]">— Reviewed by Mentor J.M. · 2h ago</p>
            </div>
          </div>
        )}
        {tab === 'portfolio' && (
          <div className="space-y-2">
            <div className="rounded-[12px] bg-[#020617] border border-[rgba(148,163,184,0.5)] px-4 py-3 space-y-1.5">
              <p className="text-[11px] font-semibold text-[#E5E7EB]">Portfolio Entry Added</p>
              <p className="text-[11px] text-[#22C55E]">Auto-published</p>
              <p className="text-[13px] font-semibold text-[#F9FAFB]">Operation Dark Harvest</p>
              <p className="text-[12px] text-[#E5E7EB]">
                DNS exfiltration analysis, threat intel correlation, incident reporting
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
              <span className="rounded-full bg-[#0B1120] px-3 py-1 text-[#E5E7EB]">DNS</span>
              <span className="rounded-full bg-[#0B1120] px-3 py-1 text-[#E5E7EB]">SIEM</span>
              <span className="rounded-full bg-[#0B1120] px-3 py-1 text-[#E5E7EB]">Threat Intel</span>
              <span className="rounded-full bg-[#0B1120] px-3 py-1 text-[#E5E7EB]">IR</span>
              <span className="ml-auto flex items-center gap-2 text-[11px] text-[#E5E7EB]">
                <span>87</span>
                <span className="text-[#9CA3AF]">Score</span>
                <span className="mx-2 h-4 w-px bg-[#1F2937]" />
                <span>3</span>
                <span className="text-[#9CA3AF]">Skills</span>
                <span className="text-[#22C55E] text-[13px]">✓</span>
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
