'use client'

import Link from 'next/link'
import { OCH_LOGO_BLUE, OCH_LOGO_WHITE } from '@/lib/brand'

export type OchLogoVariant = 'white' | 'blue'

const srcFor = (v: OchLogoVariant) => (v === 'blue' ? OCH_LOGO_BLUE : OCH_LOGO_WHITE)

/**
 * Wordmark only — use on dark UIs with `white`, on light UIs with `blue`.
 */
export function OchLogoMark({
  variant = 'white',
  className = '',
  priority = false,
}: {
  variant?: OchLogoVariant
  className?: string
  /** Set on LCP / above-the-fold brand rows */
  priority?: boolean
}) {
  return (
    <img
      src={srcFor(variant)}
      alt="Ongoza CyberHub"
      width={200}
      height={48}
      className={`h-8 w-auto max-w-[220px] object-contain object-left ${className}`}
      loading={priority ? 'eager' : 'lazy'}
      decoding="async"
    />
  )
}

/**
 * Sidebar / header row: logo + role title (e.g. "Student", "Finance").
 */
export function OchBrandLockup({
  href,
  title,
  variant = 'white',
  className = '',
  onClick,
}: {
  href: string
  title: string
  variant?: OchLogoVariant
  className?: string
  /** e.g. close mobile drawer after navigation */
  onClick?: () => void
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={`flex flex-col gap-1.5 min-w-0 ${className}`}
    >
      <OchLogoMark variant={variant} className="h-8" priority />
      <span className="text-xs font-bold text-och-mint tracking-tight truncate">{title}</span>
    </Link>
  )
}
