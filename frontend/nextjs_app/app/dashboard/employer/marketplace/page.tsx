'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Briefcase, Users, TrendingUp, Heart, Bookmark, Mail } from 'lucide-react'
import {
  marketplaceClient,
  MarketplaceProfile,
  EmployerInterestLog,
  JobPosting,
  JobApplication,
} from '@/services/marketplaceClient'
import { apiGateway } from '@/services/apiGateway'

const MAX_RECENT_ITEMS = 5

interface SnapshotStats {
  totalTalent: number
  jobReady: number
  activeJobs: number
}

type ShortlistItem =
  | { type: 'interest'; log: EmployerInterestLog }
  | { type: 'application'; app: JobApplication }

interface ContractRow {
  id: string
  organization_name: string
  type: string
  total_value: string | number
  seat_cap?: number
  seats_used?: number
}

function parseContractList(data: unknown): ContractRow[] {
  if (Array.isArray(data)) return data as ContractRow[]
  if (
    data &&
    typeof data === 'object' &&
    'results' in data &&
    Array.isArray((data as { results: unknown }).results)
  ) {
    return (data as { results: ContractRow[] }).results
  }
  return []
}

interface MarketplaceState {
  snapshot: SnapshotStats
  primaryContract: ContractRow | null
  talentSample: MarketplaceProfile[]
  favorites: EmployerInterestLog[]
  contacts: EmployerInterestLog[]
  shortlist: ShortlistItem[]
  jobs: JobPosting[]
}

export default function EmployerMarketplacePage() {
  const [state, setState] = useState<MarketplaceState>({
    snapshot: { totalTalent: 0, jobReady: 0, activeJobs: 0 },
    primaryContract: null,
    talentSample: [],
    favorites: [],
    contacts: [],
    shortlist: [],
    jobs: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadMarketplace()

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadMarketplace()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  const loadMarketplace = async () => {
    try {
      setLoading(true)
      setError(null)

      const [
        contractsRaw,
        talentPage,
        jobsData,
        favoritesLogs,
        contactLogs,
        shortlistLogs,
        applicationsData,
      ] = await Promise.all([
        apiGateway.get<unknown>('/finance/contracts/').catch(() => null),
        marketplaceClient
          .browseTalent({ page_size: 12 })
          .catch(() => ({
            results: [],
            count: 0,
            page: 1,
            page_size: 0,
          })),
        marketplaceClient.getJobPostings().catch(() => []),
        marketplaceClient.getInterestLogs('favorite').catch(() => []),
        marketplaceClient.getInterestLogs('contact_request').catch(() => []),
        marketplaceClient.getInterestLogs('shortlist').catch(() => []),
        marketplaceClient.getAllApplications().catch(() => ({ results: [] })),
      ])

      const employerContracts = parseContractList(contractsRaw).filter((c) => c.type === 'employer')
      const primaryContract = employerContracts[0] ?? null

      const jobsArray: JobPosting[] = Array.isArray(jobsData)
        ? jobsData
        : jobsData && Array.isArray((jobsData as { results?: unknown }).results)
          ? ((jobsData as { results: JobPosting[] }).results)
          : []

      const favoritesArray: EmployerInterestLog[] = Array.isArray(favoritesLogs)
        ? favoritesLogs
        : (favoritesLogs as { results?: EmployerInterestLog[] }).results || []

      const contactsArray: EmployerInterestLog[] = Array.isArray(contactLogs)
        ? contactLogs
        : (contactLogs as { results?: EmployerInterestLog[] }).results || []

      const shortlistArray: EmployerInterestLog[] = Array.isArray(shortlistLogs)
        ? shortlistLogs
        : (shortlistLogs as { results?: EmployerInterestLog[] }).results || []

      const appsList: JobApplication[] = Array.isArray(applicationsData?.results)
        ? applicationsData.results
        : []
      const shortlistedApps = appsList.filter((a) => a.status === 'shortlisted')
      const unifiedShortlist: ShortlistItem[] = [
        ...shortlistArray.map((log) => ({ type: 'interest' as const, log })),
        ...shortlistedApps.map((app) => ({ type: 'application' as const, app })),
      ]

      const snapshot: SnapshotStats = {
        totalTalent: talentPage.count || talentPage.results.length || 0,
        jobReady: talentPage.results.filter((t) => t.profile_status === 'job_ready').length,
        activeJobs: jobsArray.filter((job) => job.is_active !== false).length,
      }

      setState({
        snapshot,
        primaryContract,
        talentSample: talentPage.results.slice(0, MAX_RECENT_ITEMS),
        favorites: favoritesArray.slice(0, MAX_RECENT_ITEMS),
        contacts: contactsArray.slice(0, MAX_RECENT_ITEMS),
        shortlist: unifiedShortlist,
        jobs: jobsArray.slice(0, MAX_RECENT_ITEMS),
      })
    } catch (err: unknown) {
      console.error('Failed to load employer marketplace:', err)
      const msg = err instanceof Error ? err.message : 'Unable to load marketplace right now.'
      setError(msg)
      setState((prev) => ({
        ...prev,
        snapshot: { totalTalent: 0, jobReady: 0, activeJobs: 0 },
        primaryContract: null,
        talentSample: [],
        favorites: [],
        contacts: [],
        shortlist: [],
        jobs: [],
      }))
    } finally {
      setLoading(false)
    }
  }

  const pc = state.primaryContract
  const seatCap = typeof pc?.seat_cap === 'number' ? pc.seat_cap : 0
  const seatsUsed = typeof pc?.seats_used === 'number' ? pc.seats_used : 0
  const seatsUtilization = seatCap > 0 ? Math.round((seatsUsed / seatCap) * 100) : 0

  const contractValue =
    pc && pc.total_value !== undefined && pc.total_value !== ''
      ? typeof pc.total_value === 'string'
        ? parseFloat(pc.total_value)
        : pc.total_value
      : 0
  const hasContractValue = Number.isFinite(contractValue) && contractValue > 0

  return (
    <div className="min-h-screen bg-och-midnight p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex flex-col gap-2">
          <h1 className="text-3xl sm:text-4xl font-bold text-och-gold tracking-tight">
            Talent Marketplace
          </h1>
          <p className="text-och-steel max-w-2xl text-sm sm:text-base">
            Discover, engage, and hire talent. Your contract seat cap and job pipeline are summarized here
            alongside favorites, contacts, and shortlists—mirroring the sponsor marketplace workflow.
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-och-orange/40 bg-och-orange/10 px-4 py-3 text-sm text-och-orange">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
          <Card className="lg:col-span-2 bg-och-midnight border border-och-steel/30">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-och-steel">
                  Contract & seats
                </p>
                <p className="text-sm text-och-steel mt-1">
                  Entitlement from your employer finance contract.
                </p>
              </div>
              <Link
                href="/dashboard/employer"
                className="text-xs font-semibold text-och-mint hover:text-och-mint/80"
              >
                View dashboard
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-lg bg-och-midnight/80 border border-och-steel/30 p-4">
                <p className="text-xs text-och-steel mb-1">Seats used</p>
                <p className="text-2xl font-bold text-white">
                  {loading ? '...' : seatsUsed}
                  <span className="text-sm text-och-steel font-normal"> / {seatCap || '—'}</span>
                </p>
                <p className="mt-1 text-xs text-och-steel">
                  {seatCap
                    ? seatsUtilization
                      ? `${seatsUtilization}% of cap in use`
                      : 'Capacity available'
                    : 'No seat cap on file yet'}
                </p>
              </div>
              <div className="rounded-lg bg-och-midnight/80 border border-och-steel/30 p-4">
                <p className="text-xs text-och-steel mb-1">Contract value</p>
                <p className="text-2xl font-bold text-white">
                  {loading ? '...' : hasContractValue ? `Ksh ${(contractValue / 1000).toFixed(0)}K` : '—'}
                </p>
                <p className="mt-1 text-xs text-och-steel">
                  {pc?.organization_name
                    ? `${pc.organization_name}`
                    : 'Link your organization via onboarding'}
                </p>
              </div>
            </div>
          </Card>

          <Card className="bg-och-midnight border border-och-steel/30">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-och-steel">
                Total talent
              </p>
              <Users className="w-5 h-5 text-och-mint" />
            </div>
            <p className="text-3xl font-bold text-white">
              {loading ? '...' : state.snapshot.totalTalent}
            </p>
            <p className="mt-1 text-xs text-och-steel">Profiles you can browse</p>
            <Link
              href="/dashboard/employer/marketplace/talent"
              className="mt-4 inline-flex text-xs font-semibold text-och-mint hover:text-och-mint/80"
            >
              Browse all talent →
            </Link>
          </Card>

          <Card className="bg-och-midnight border border-och-steel/30">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-och-steel">
                Job ready
              </p>
              <TrendingUp className="w-5 h-5 text-och-gold" />
            </div>
            <p className="text-3xl font-bold text-white">
              {loading ? '...' : state.snapshot.jobReady}
            </p>
            <p className="mt-1 text-xs text-och-steel">
              In sample view (first page); filter on the talent browser for full counts.
            </p>
          </Card>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-8">
          <Card className="xl:col-span-2 bg-och-midnight border border-och-steel/30">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-och-steel">
                  Browse talent
                </p>
                <p className="text-sm text-och-steel">
                  Filter by readiness, skills, and portfolio depth to discover matches.
                </p>
              </div>
              <Link
                href="/dashboard/employer/marketplace/talent"
                className="text-xs font-semibold text-och-mint hover:text-och-mint/80"
              >
                Open talent browser
              </Link>
            </div>

            <div className="mb-4 grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="flex items-center gap-2 text-xs text-och-steel">
                <span className="h-2 w-2 rounded-full bg-och-mint" />
                <span>Job ready ≥ 70 readiness</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-och-steel">
                <span className="h-2 w-2 rounded-full bg-och-gold" />
                <span>Emerging talent with strong portfolios</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-och-steel">
                <span className="h-2 w-2 rounded-full bg-och-orange" />
                <span>Foundation mode – nurture over time</span>
              </div>
            </div>

            <div className="overflow-x-auto -mx-4 sm:mx-0">
              <table className="w-full text-sm">
                <thead className="border-b border-och-steel/30 text-xs uppercase tracking-wide text-och-steel">
                  <tr>
                    <th className="py-2 px-4 text-left">Talent</th>
                    <th className="py-2 px-4 text-left">Readiness</th>
                    <th className="py-2 px-4 text-left">Primary role</th>
                    <th className="py-2 px-4 text-left">Portfolio</th>
                    <th className="py-2 px-4 text-left">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-och-steel/20">
                  {loading ? (
                    <tr>
                      <td colSpan={5} className="py-8 px-4 text-center text-och-steel text-sm">
                        Loading marketplace profiles...
                      </td>
                    </tr>
                  ) : state.talentSample.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 px-4 text-center text-och-steel text-sm">
                        No visible talent profiles yet. As students progress through TalentScope, they’ll appear
                        here.
                      </td>
                    </tr>
                  ) : (
                    state.talentSample.map((profile) => (
                      <tr key={profile.id} className="hover:bg-och-steel/10 transition-colors">
                        <td className="py-3 px-4">
                          <div className="flex flex-col">
                            <span className="font-semibold text-white">{profile.mentee_name}</span>
                            <span className="text-xs text-och-steel">
                              {profile.mentee_email || 'Contact via marketplace'}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-och-mint font-semibold">
                            {profile.readiness_score != null
                              ? `${Number(profile.readiness_score).toFixed(1)}`
                              : '—'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-och-steel">{profile.primary_role || '—'}</td>
                        <td className="py-3 px-4 text-och-steel">
                          {profile.portfolio_depth
                            ? profile.portfolio_depth === 'deep'
                              ? 'Deep portfolio'
                              : profile.portfolio_depth === 'moderate'
                                ? 'Moderate portfolio'
                                : 'Basic portfolio'
                            : '—'}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={
                              profile.profile_status === 'job_ready'
                                ? 'inline-flex rounded-full bg-och-mint/20 px-2.5 py-1 text-xs font-semibold text-och-mint'
                                : profile.profile_status === 'emerging_talent'
                                  ? 'inline-flex rounded-full bg-och-gold/20 px-2.5 py-1 text-xs font-semibold text-och-gold'
                                  : 'inline-flex rounded-full bg-och-orange/20 px-2.5 py-1 text-xs font-semibold text-och-orange'
                            }
                          >
                            {profile.profile_status.replace('_', ' ')}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          <div className="space-y-4">
            <Card className="bg-och-midnight border border-och-steel/30">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Heart className="w-4 h-4 text-pink-400" />
                  <p className="text-xs font-semibold uppercase tracking-wide text-och-steel">
                    Favorites
                  </p>
                </div>
                <span className="text-xs text-och-steel">{state.favorites.length} recent</span>
              </div>
              <ul className="space-y-2 text-xs">
                {loading ? (
                  <li className="text-och-steel">Loading favorites…</li>
                ) : state.favorites.length === 0 ? (
                  <li className="text-och-steel">Start building a watchlist as you browse talent.</li>
                ) : (
                  state.favorites.map((log) => (
                    <li key={log.id} className="flex justify-between gap-2">
                      <span className="text-white truncate">{log.profile?.mentee_name ?? 'Talent'}</span>
                      <span className="text-och-steel shrink-0">
                        {Number(log.profile?.readiness_score ?? 0).toFixed(1)}
                      </span>
                    </li>
                  ))
                )}
              </ul>
            </Card>

            <Card className="bg-och-midnight border border-och-steel/30">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-och-gold" />
                  <p className="text-xs font-semibold uppercase tracking-wide text-och-steel">
                    Contacted students
                  </p>
                </div>
                <span className="text-xs text-och-steel">{state.contacts.length} recent</span>
              </div>
              <ul className="space-y-2 text-xs">
                {loading ? (
                  <li className="text-och-steel">Loading contacted students…</li>
                ) : state.contacts.length === 0 ? (
                  <li className="text-och-steel">
                    Contact requests are tracked here to avoid duplicate outreach.
                  </li>
                ) : (
                  state.contacts.map((log) => (
                    <li key={log.id} className="flex justify-between gap-2">
                      <span className="text-white truncate">{log.profile?.mentee_name ?? 'Talent'}</span>
                      <span className="text-och-steel shrink-0">
                        {new Date(log.created_at).toLocaleDateString()}
                      </span>
                    </li>
                  ))
                )}
              </ul>
            </Card>

            <Card className="bg-och-midnight border border-och-steel/30">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Bookmark className="w-4 h-4 text-blue-400" />
                  <p className="text-xs font-semibold uppercase tracking-wide text-och-steel">
                    Shortlist
                  </p>
                </div>
                <span className="text-xs text-och-steel">{state.shortlist.length} in funnel</span>
              </div>
              <ul className="space-y-2 text-xs">
                {loading ? (
                  <li className="text-och-steel">Loading shortlist…</li>
                ) : state.shortlist.length === 0 ? (
                  <li className="text-och-steel">
                    Move serious candidates here as you progress toward hire.
                  </li>
                ) : (
                  state.shortlist.slice(0, MAX_RECENT_ITEMS).map((item) =>
                    item.type === 'interest' ? (
                      <li key={`interest-${item.log.id}`} className="flex justify-between gap-2">
                        <span className="text-white truncate">
                          {item.log.profile?.mentee_name ?? 'Talent'}
                        </span>
                        <span className="text-och-steel shrink-0">
                          {Number(item.log.profile?.job_fit_score ?? 0).toFixed(1)}
                        </span>
                      </li>
                    ) : (
                      <li key={`app-${item.app.id}`} className="flex justify-between gap-2">
                        <span className="text-white truncate">
                          {item.app.applicant_name ?? item.app.applicant_email ?? 'Applicant'}
                        </span>
                        <span className="text-och-steel shrink-0">
                          {item.app.match_score != null
                            ? `${Number(item.app.match_score).toFixed(1)}%`
                            : '—'}
                        </span>
                      </li>
                    )
                  )
                )}
              </ul>
            </Card>
          </div>
        </div>

        <Card className="bg-och-midnight border border-och-steel/30 mb-10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-och-steel">
                Job postings
              </p>
              <p className="text-sm text-och-steel">
                Your live roles in the marketplace. Seat caps apply when creating new jobs where configured.
              </p>
            </div>
            <Link
              href="/dashboard/employer/jobs"
              className="inline-flex items-center justify-center rounded-lg bg-och-gold px-4 py-2 text-xs font-semibold text-och-midnight hover:bg-och-gold/90"
            >
              <Briefcase className="mr-2 h-4 w-4" />
              Manage job postings
            </Link>
          </div>

          <div className="overflow-x-auto -mx-4 sm:mx-0">
            <table className="w-full text-sm">
              <thead className="border-b border-och-steel/30 text-xs uppercase tracking-wide text-och-steel">
                <tr>
                  <th className="py-2 px-4 text-left">Title</th>
                  <th className="py-2 px-4 text-left">Location</th>
                  <th className="py-2 px-4 text-left">Type</th>
                  <th className="py-2 px-4 text-left">Status</th>
                  <th className="py-2 px-4 text-left">Posted</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-och-steel/20">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-8 px-4 text-center text-och-steel text-sm">
                      Loading job postings…
                    </td>
                  </tr>
                ) : state.jobs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 px-4 text-center text-och-steel text-sm">
                      No job postings yet. Create your first role to start attracting applications.
                    </td>
                  </tr>
                ) : (
                  state.jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-och-steel/10 transition-colors">
                      <td className="py-3 px-4 text-white">{job.title}</td>
                      <td className="py-3 px-4 text-och-steel">{job.location || 'Remote / flexible'}</td>
                      <td className="py-3 px-4 text-och-steel">{job.job_type.replace('_', ' ')}</td>
                      <td className="py-3 px-4">
                        <span
                          className={
                            job.is_active
                              ? 'inline-flex rounded-full bg-och-mint/20 px-2.5 py-1 text-xs font-semibold text-och-mint'
                              : 'inline-flex rounded-full bg-och-steel/20 px-2.5 py-1 text-xs font-semibold text-och-steel'
                          }
                        >
                          {job.is_active ? 'Active' : 'Archived'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-och-steel">
                        {new Date(job.posted_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
