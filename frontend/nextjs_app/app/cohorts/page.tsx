'use client'

import { PublicCohortRegistration } from '@/components/home/PublicCohortRegistration'
import { Shield, ArrowLeft } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function CohortsPage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-[#06090F] text-[#E2E8F0]">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(10,14,26,1),_transparent_55%),radial-gradient(circle_at_top_left,_rgba(245,158,11,0.12),_transparent_55%),radial-gradient(circle_at_bottom_right,_rgba(56,189,248,0.12),_transparent_55%)]" />
      <div className="pointer-events-none fixed inset-0 -z-10 opacity-[0.03]" style={{backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '50px 50px'}} />
      
      <header className="fixed top-0 inset-x-0 z-50 bg-[rgba(6,9,15,0.85)] backdrop-blur-[20px] border-b border-[rgba(255,255,255,0.06)] h-[70px]">
        <nav className="max-w-[1140px] mx-auto px-6">
          <div className="flex h-[70px] items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => router.push('/')}
                className="flex items-center gap-2 text-[13px] font-medium text-[#64748B] hover:text-[#F59E0B] transition-colors duration-200"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back to Home</span>
              </button>
            </div>
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
          </div>
        </nav>
      </header>

      <main className="pt-[70px]">
        <PublicCohortRegistration />
      </main>
    </div>
  )
}

