'use client'

import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Search } from 'lucide-react'
import { AFRICA_COUNTRIES, filterAfricaCountries, getAfricaCountryByCode } from '@/lib/africa-countries'
import { cn } from '@/lib/utils'

export interface AfricaCountrySelectProps {
  value: string
  onChange: (code: string) => void
  placeholder?: string
  disabled?: boolean
  id?: string
  className?: string
  label?: string
  required?: boolean
  error?: string
}

export function AfricaCountrySelect({
  value,
  onChange,
  placeholder = 'Select country',
  disabled = false,
  id = 'country',
  className,
  label = 'Country',
  required = false,
  error,
}: AfricaCountrySelectProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)

  const selected = getAfricaCountryByCode(value)
  const displayValue = selected ? selected.name : ''
  const filtered = filterAfricaCountries(search)

  useEffect(() => {
    if (!open) setSearch('')
  }, [open])

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-och-steel mb-1">
          {label}
          {required && <span className="text-och-orange ml-0.5">*</span>}
        </label>
      )}
      <button
        type="button"
        id={id}
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={`${id}-listbox`}
        aria-label={label}
        disabled={disabled}
        onClick={() => !disabled && setOpen((o) => !o)}
        className={cn(
          'w-full flex items-center justify-between gap-2 px-4 py-2 rounded-lg text-left',
          'bg-och-midnight border border-och-steel/20 text-white',
          'focus:outline-none focus:ring-2 focus:ring-och-defender',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          error && 'border-och-orange/50'
        )}
      >
        <span className={displayValue ? 'text-white' : 'text-och-steel'}>{displayValue || placeholder}</span>
        <ChevronDown className={cn('w-4 h-4 text-och-steel shrink-0 transition-transform', open && 'rotate-180')} />
      </button>
      {error && <p className="mt-1 text-xs text-och-orange">{error}</p>}

      {open && (
        <div
          id={`${id}-listbox`}
          role="listbox"
          className="absolute z-50 mt-1 w-full rounded-lg border border-och-steel/20 bg-och-midnight shadow-lg overflow-hidden"
        >
          <div className="p-2 border-b border-och-steel/20">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-och-steel" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search countries (e.g. ke, Kenya)"
                className="w-full pl-9 pr-3 py-2 bg-slate-900/80 border border-och-steel/20 rounded-md text-white text-sm placeholder:text-och-steel focus:outline-none focus:ring-2 focus:ring-och-defender"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Escape') setOpen(false)
                }}
              />
            </div>
          </div>
          <ul className="max-h-60 overflow-auto py-1">
            {filtered.length === 0 ? (
              <li className="px-4 py-3 text-sm text-och-steel">No countries match &quot;{search}&quot;</li>
            ) : (
              filtered.map((c) => (
                <li
                  key={c.code}
                  role="option"
                  aria-selected={value === c.code}
                  className={cn(
                    'px-4 py-2.5 text-sm cursor-pointer transition-colors',
                    value === c.code
                      ? 'bg-och-defender/20 text-och-mint'
                      : 'text-white hover:bg-och-steel/20'
                  )}
                  onClick={() => {
                    onChange(c.code)
                    setOpen(false)
                  }}
                >
                  <span className="font-medium">{c.name}</span>
                  <span className="ml-2 text-och-steel text-xs">{c.code}</span>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  )
}
