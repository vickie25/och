'use client'
 
import { useState, useEffect, useMemo, useCallback } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { programsClient, type Enrollment } from '@/services/programsClient'
import { djangoClient } from '@/services/djangoClient'
import { apiGateway } from '@/services/apiGateway'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { Menu, MenuItem, IconButton } from '@mui/material'
import MoreVertIcon from '@mui/icons-material/MoreVert'

interface EnrolledStudent extends Omit<Enrollment, 'enrollment_type'> {
  enrollment_type: 'self' | 'invite' | 'director'
  cohort_name?: string | null
  track_name?: string | null
  user_name?: string
  user_email?: string
  subscription_tier?: string
  subscription_plan_name?: string
  onboarded_email_status?: 'sent' | 'sent_and_seen' | null
  organization_name?: string | null
  organization_id?: string | null
  cohorts?: Array<{
    id: string
    name: string
    track_name?: string
    status: string
    joined_at: string
  }>
}

interface StudentFormData {
  first_name: string
  last_name: string
  email: string
  gender?: string
  phone?: string
  country?: string
  subscription_plan_id: string
  send_onboarding_email?: boolean
}

interface SubscriptionPlan {
  id: string
  name: string
  tier: 'free' | 'starter' | 'premium'
  price_monthly: number | null
  ai_coach_daily_limit: number | null
  portfolio_item_limit: number | null
  missions_access_type: 'none' | 'ai_only' | 'full'
  mentorship_access: boolean
  talentscope_access: 'none' | 'basic' | 'preview' | 'full'
  marketplace_contact: boolean
  enhanced_access_days: number | null
  features: string[]
  created_at?: string
  updated_at?: string
}

interface EnrollmentFormState {
  step: 'method' | 'organization' | 'orgDetails' | 'student' | 'import' | 'preview'
  isFromOrganization: boolean | null
  enrollmentMethod: 'manual' | 'import' | null
  organizationName: string
  selectedOrganizationId: string | null
  isCreatingNewOrg: boolean
  numberOfStudents: number
  currentStudentIndex: number
  students: StudentFormData[]
  organizationId: string | null
  subscriptionPlans: SubscriptionPlan[]
  availableOrganizations: any[]
  /** Org contact for billing/invoice (required when enrolling from org) */
  contactPersonName: string
  contactEmail: string
  contactPhone: string
  importFile: File | null
  csvPreview: {
    headers: string[]
    matchedHeaders: string[]
    missingHeaders: string[]
    extraHeaders: string[]
    rows: any[]
  } | null
}

const ENROLLMENT_TYPE_LABELS: Record<string, string> = {
  'self': 'Self-enroll',
  'invite': 'Invite',
  'director': 'Director assign',
}

const GENDER_OPTIONS = [
  { value: '', label: 'Select gender (optional)' },
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
]

export default function EnrollmentPage() {
  const [cohorts, setCohorts] = useState<any[]>([])
  const [organizations, setOrganizations] = useState<any[]>([])
  const [selectedOrganization, setSelectedOrganization] = useState<string>('all')
  const [selectedTrack, setSelectedTrack] = useState<string>('all')
  const [enrolledStudents, setEnrolledStudents] = useState<EnrolledStudent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showEnrollmentForm, setShowEnrollmentForm] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [enrolledCount, setEnrolledCount] = useState(0)
  const [selectedStudents, setSelectedStudents] = useState<Set<string>>(new Set())
  const [isSendingEmails, setIsSendingEmails] = useState(false)
  const [emailProgress, setEmailProgress] = useState({ current: 0, total: 0 })
  const [selectedStudentDetails, setSelectedStudentDetails] = useState<EnrolledStudent | null>(null)
  const [showStudentDetailsModal, setShowStudentDetailsModal] = useState(false)
  const [selectedOrganizationDetails, setSelectedOrganizationDetails] = useState<any | null>(null)
  const [actionMenuAnchor, setActionMenuAnchor] = useState<null | HTMLElement>(null)
  const [actionMenuStudentId, setActionMenuStudentId] = useState<string | null>(null)
  const [showChangeTrackModal, setShowChangeTrackModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false)
  const [bulkDeleteConfirmText, setBulkDeleteConfirmText] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)
  const [curriculumTracks, setCurriculumTracks] = useState<any[]>([])
  const [selectedTrackSlug, setSelectedTrackSlug] = useState('')
  const [studentForAction, setStudentForAction] = useState<EnrolledStudent | null>(null)
  const [editFormData, setEditFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    country: '',
    organization_id: '',
  })
  
  // Enrollment form state
  const [enrollmentForm, setEnrollmentForm] = useState<EnrollmentFormState>({
    step: 'method',
    isFromOrganization: null,
    enrollmentMethod: null,
    organizationName: '',
    selectedOrganizationId: null,
    isCreatingNewOrg: false,
    numberOfStudents: 1,
    currentStudentIndex: 0,
    students: [{ 
      first_name: '', 
      last_name: '', 
      email: '', 
      gender: '',
      phone: '',
      country: '',
      subscription_plan_id: '',
      send_onboarding_email: false
    }],
    organizationId: null,
    subscriptionPlans: [],
    availableOrganizations: [],
    contactPersonName: '',
    contactEmail: '',
    contactPhone: '',
    importFile: null,
    csvPreview: null,
  })

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 20

  // Load subscription plans from admin endpoint
  useEffect(() => {
    const loadSubscriptionPlans = async () => {
      try {
        const response = await apiGateway.get('/admin/plans/') as any
        // Handle paginated response
        let plansData: SubscriptionPlan[] = []
        if (response?.results && Array.isArray(response.results)) {
          plansData = response.results
        } else if (Array.isArray(response)) {
          plansData = response
        } else if (response?.data && Array.isArray(response.data)) {
          plansData = response.data
        }
        
        // Show all plans including free tier
        setEnrollmentForm(prev => ({ ...prev, subscriptionPlans: plansData }))
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail || err?.message || err?.detail || 'Failed to load subscription plans'
        setError(`Failed to load subscription plans: ${errorMessage}. Please ensure you have permission to view subscription plans.`)
      }
    }
    if (showEnrollmentForm) {
      loadSubscriptionPlans()
    }
  }, [showEnrollmentForm])
  
  // Load organizations for enrollment form
  const loadOrganizationsForEnrollment = useCallback(async () => {
    try {
      const orgsData = await apiGateway.get('/orgs/') as any
      const orgsList = orgsData?.results || orgsData?.data || orgsData || []
      setEnrollmentForm(prev => ({ ...prev, availableOrganizations: orgsList }))
    } catch (err: any) {
      setEnrollmentForm(prev => ({ ...prev, availableOrganizations: [] }))
    }
  }, [])
  
  // Load organizations when entering orgDetails step or import step
  useEffect(() => {
    if (showEnrollmentForm && (enrollmentForm.step === 'orgDetails' || enrollmentForm.step === 'import')) {
      loadOrganizationsForEnrollment()
    }
  }, [showEnrollmentForm, enrollmentForm.step, loadOrganizationsForEnrollment])

  // Load all data function (optimized to reduce API calls)
  const loadData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Load cohorts and organizations in parallel
      const [cohortsData, orgsData] = await Promise.all([
        apiGateway.get('/cohorts/').catch(() => ({ results: [], data: [] })),
        apiGateway.get('/orgs/').catch(() => ({ results: [], data: [] })),
      ])
      
      const cohortsList = (cohortsData as any)?.results || (cohortsData as any)?.data || cohortsData || []
      const orgsList = (orgsData as any)?.results || (orgsData as any)?.data || orgsData || []
      
      setCohorts(cohortsList)
      setOrganizations(orgsList)
      
      // Create organization lookup map to avoid duplicate API calls
      const orgMap = new Map<string, { id: string; name: string }>()
      for (const org of orgsList) {
        orgMap.set(String(org.id), { id: String(org.id), name: org.name })
      }

      // Fetch all students using the director students endpoint
      const studentsResponse = await apiGateway.get('/director/students/').catch((err) => {
        return null
      }) as any
      
      if (!studentsResponse || !studentsResponse.students) {
        setEnrolledStudents([])
        return
      }
      
      const allStudents = studentsResponse.students || []
      
      // Fetch cohort enrollments for each student to get cohort details
      const enrollmentPromises = cohortsList.map((cohort: any) =>
        programsClient.getCohortEnrollments(cohort.id)
          .then((enrollments: Enrollment[]) => ({
            cohort,
            enrollments: enrollments.filter((e: Enrollment) => e.status !== 'withdrawn'),
          }))
          .catch((err: any) => {
            return { cohort, enrollments: [] }
          })
      )
      
      const cohortEnrollments = await Promise.all(enrollmentPromises)
      
      // Build a map of user ID to their cohort enrollments
      const userCohortsMap = new Map<string, Array<{ cohort: any; enrollment: Enrollment }>>()
      for (const { cohort, enrollments } of cohortEnrollments) {
        for (const e of enrollments) {
          const userId = String(e.user)
          if (!userCohortsMap.has(userId)) {
            userCohortsMap.set(userId, [])
          }
          userCohortsMap.get(userId)!.push({ cohort, enrollment: e })
        }
      }
      
      // Batch fetch user details for onboarded_email_status
      const userDataMap = new Map<string, { onboarded_email_status: any }>()
      if (allStudents.length > 0) {
        const batchSize = 50
        const maxConcurrentBatches = 3
        
        for (let i = 0; i < allStudents.length; i += batchSize * maxConcurrentBatches) {
          const batchGroup = []
          for (let j = 0; j < maxConcurrentBatches && i + j * batchSize < allStudents.length; j++) {
            const batch = allStudents.slice(i + j * batchSize, i + (j + 1) * batchSize)
            if (batch.length > 0) {
              batchGroup.push(
                Promise.all(
                  batch.map((student: any) =>
                    apiGateway.get(`/users/${student.id}/`)
                      .then((user: any) => ({ userId: String(student.id), onboarded_email_status: user.onboarded_email_status || null }))
                      .catch(() => ({ userId: String(student.id), onboarded_email_status: null }))
                  )
                )
              )
            }
          }
          
          const userResults = await Promise.all(batchGroup)
          for (const batch of userResults) {
            for (const { userId, onboarded_email_status } of batch) {
              userDataMap.set(userId, { onboarded_email_status })
            }
          }
        }
      }
      
      // Fetch subscription data for tier information
      const subscriptionsResponse = await apiGateway.get('/admin/subscriptions/', {
        params: { page_size: 1000 }
      }).catch(() => null) as any
      
      const subscriptionsMap = new Map<string, any>()
      if (subscriptionsResponse) {
        const subscriptions = subscriptionsResponse?.results || subscriptionsResponse?.data || subscriptionsResponse || []
        for (const sub of subscriptions) {
          const userId = String(sub.user?.id || sub.user_id || sub.user)
          if (userId) {
            subscriptionsMap.set(userId, sub)
          }
        }
      }
      
      // Build enrolled students list from all students
      const allEnrolled: EnrolledStudent[] = allStudents.map((student: any) => {
        const userId = String(student.id)
        const userCohorts = userCohortsMap.get(userId) || []
        const userData = userDataMap.get(userId) || { onboarded_email_status: null }
        const subscription = subscriptionsMap.get(userId)

        // Get organization data from backend response
        const orgName = student.organization_name || null
        const orgId = student.organization_id || null
        
        // Build cohorts array
        const cohorts = userCohorts.map(({ cohort, enrollment }) => ({
          id: cohort.id || '',
          name: cohort.name || '',
          track_name: cohort.track?.name || cohort.track_name || cohort.track_slug || '',
          status: enrollment.status,
          joined_at: enrollment.joined_at,
        }))
        
        // Determine enrollment type and status
        const hasEnrollments = userCohorts.length > 0
        const primaryEnrollment = hasEnrollments ? userCohorts[0].enrollment : null
        
        return {
          id: hasEnrollments ? primaryEnrollment!.id : `director-${userId}`,
          cohort: hasEnrollments ? primaryEnrollment!.cohort : '',
          cohort_name: hasEnrollments ? userCohorts[0].cohort.name : null,
          track_name: hasEnrollments ? (userCohorts[0].cohort.track?.name || userCohorts[0].cohort.track_name || userCohorts[0].cohort.track_slug) : student.track_display,
          user: userId,
          user_email: student.email,
          user_name: `${student.first_name || ''} ${student.last_name || ''}`.trim() || student.email,
          org: orgId,
          enrollment_type: (hasEnrollments ? primaryEnrollment!.enrollment_type : 'director') as 'self' | 'invite' | 'director',
          seat_type: (hasEnrollments ? primaryEnrollment!.seat_type : 'paid') as 'paid' | 'scholarship' | 'sponsored',
          payment_status: (hasEnrollments ? primaryEnrollment!.payment_status : 'paid') as 'paid' | 'pending' | 'failed',
          status: (hasEnrollments ? primaryEnrollment!.status : 'active') as 'active' | 'pending' | 'withdrawn',
          joined_at: hasEnrollments ? primaryEnrollment!.joined_at : student.created_at,
          completed_at: hasEnrollments ? primaryEnrollment!.completed_at : null,
          subscription_tier: subscription?.plan?.tier || 'free',
          subscription_plan_name: subscription?.plan?.name || null,
          onboarded_email_status: userData.onboarded_email_status,
          organization_name: orgName,
          organization_id: orgId,
          cohorts,
        }
      })
      
      setEnrolledStudents(allEnrolled)
    } catch (err: any) {
      setError(err?.message || 'Failed to load enrollment data')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Load data on mount (only once)
  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Empty deps - only run on mount

  const handleOpenActionMenu = (event: React.MouseEvent<HTMLElement>, studentId: string, student: EnrolledStudent) => {
    setActionMenuAnchor(event.currentTarget)
    setActionMenuStudentId(studentId)
    setStudentForAction(student)
  }

  const handleCloseActionMenu = () => {
    setActionMenuAnchor(null)
    setActionMenuStudentId(null)
  }

  // Fetch full organization details when view-details modal opens and student has organization_id
  useEffect(() => {
    if (!showStudentDetailsModal || !selectedStudentDetails?.organization_id) {
      setSelectedOrganizationDetails(null)
      return
    }
    const orgId = selectedStudentDetails.organization_id
    let cancelled = false
    apiGateway.get(`/orgs/${orgId}/`)
      .then((data: any) => {
        if (!cancelled) setSelectedOrganizationDetails(data)
      })
      .catch(() => {
        if (!cancelled) setSelectedOrganizationDetails(null)
      })
    return () => { cancelled = true }
  }, [showStudentDetailsModal, selectedStudentDetails?.organization_id])

  const handleChangeTrack = async () => {
    if (!studentForAction || !selectedTrackSlug) return
    try {
      await apiGateway.post('/director/students/change-track/', {
        student_id: studentForAction.user,
        curriculum_track_slug: selectedTrackSlug,
      })
      setShowChangeTrackModal(false)
      setStudentForAction(null)
      setSelectedTrackSlug('')
      toast.success('Track changed successfully')
      await loadData()
    } catch (e: any) {
      const errMsg = e?.response?.data?.error || e?.message || 'Failed to change track'
      toast.error(errMsg)
    }
  }

  const handleDeleteStudent = async () => {
    if (!studentForAction) return
    setIsDeleting(true)
    try {
      await apiGateway.delete(`/users/${studentForAction.user}/`, { params: { permanent: true } })
      setShowDeleteModal(false)
      setStudentForAction(null)
      toast.success('Student deleted permanently from the database')
      await loadData()
    } catch (e: any) {
      const errMsg = e?.response?.data?.error || e?.message || 'Failed to delete student'
      toast.error(errMsg)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleBulkDelete = async () => {
    if (selectedStudents.size === 0) {
      toast.error('Please select at least one student')
      return
    }

    const studentIds = Array.from(selectedStudents)
    const studentsToDelete = enrolledStudents.filter(s => studentIds.includes(s.id))
    
    // Validate confirmation text
    if (bulkDeleteConfirmText !== 'DELETE') {
      toast.error('Please type "DELETE" to confirm')
      return
    }
    
    setIsDeleting(true)
    let successCount = 0
    let failCount = 0
    const errors: string[] = []

    for (const student of studentsToDelete) {
      try {
        await apiGateway.delete(`/users/${student.user}/`, { params: { permanent: true } })
        successCount++
      } catch (e: any) {
        failCount++
        const errMsg = e?.response?.data?.error || e?.message || 'Failed to delete student'
        errors.push(`${student.user_name || student.user_email}: ${errMsg}`)
      }
    }

    setIsDeleting(false)
    setShowBulkDeleteModal(false)
    setBulkDeleteConfirmText('')
    setSelectedStudents(new Set())
    
    if (successCount > 0) {
      toast.success(`Successfully deleted ${successCount} student(s) permanently from the database`)
      await loadData()
    }
    
    if (failCount > 0) {
      toast.error(`Failed to delete ${failCount} student(s). Check console for details.`)
      if (errors.length > 0) {
        console.error('Deletion errors:', errors)
      }
    }
  }

  const handleEditStudent = async () => {
    if (!studentForAction) return
    try {
      // Update user data
      const updateData: any = {
        first_name: editFormData.first_name,
        last_name: editFormData.last_name,
        email: editFormData.email,
      }
      
      if (editFormData.phone_number) {
        updateData.phone_number = editFormData.phone_number
      }
      
      if (editFormData.country) {
        updateData.country = editFormData.country.toUpperCase()
      }
      
      await apiGateway.patch(`/users/${studentForAction.user}/`, updateData)
      
      // Update organization assignment if changed
      // Note: Organization is stored on enrollments, not directly on users
      // We'll update each enrollment's org field
      if (editFormData.organization_id !== studentForAction.organization_id && studentForAction.cohorts && studentForAction.cohorts.length > 0) {
        for (const cohort of studentForAction.cohorts) {
          try {
            // Get enrollment ID for this cohort
            const enrollments = await programsClient.getCohortEnrollments(cohort.id)
            const enrollment = enrollments.find((e: Enrollment) => e.user === studentForAction.user)
            if (enrollment) {
              // Update enrollment organization
              await apiGateway.patch(`/cohorts/${cohort.id}/enrollments/${enrollment.id}/`, {
                org: editFormData.organization_id || null,
              })
            }
          } catch (err) {
            // Don't fail the entire update if enrollment org update fails
          }
        }
      }
      
      setShowEditModal(false)
      setStudentForAction(null)
      setEditFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone_number: '',
        country: '',
        organization_id: '',
      })
      toast.success('Student updated successfully')
      await loadData()
    } catch (e: any) {
      const errMsg = e?.response?.data?.error || e?.message || 'Failed to update student'
      toast.error(errMsg)
    }
  }

  const handleGenerateReport = async () => {
    if (!studentForAction) return
    setIsGeneratingReport(true)
    try {
      // Use fetch directly for PDF blob response
      const baseUrl = process.env.NEXT_PUBLIC_DJANGO_API_URL;
      const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token')
      
      const response = await fetch(`${baseUrl}/api/v1/admin/students/${studentForAction.user}/progress-report/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({ format: 'pdf' }),
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || 'Failed to generate report')
      }
      
      // Get PDF blob
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `student_progress_report_${studentForAction.user_email || studentForAction.user}_${new Date().toISOString().split('T')[0]}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast.success('Report generated and downloaded successfully')
      setShowReportModal(false)
      setStudentForAction(null)
    } catch (e: any) {
      const errMsg = e?.message || 'Failed to generate report'
      toast.error(errMsg)
    } finally {
      setIsGeneratingReport(false)
    }
  }

  // Filter and sort enrolled students (by joined_at descending - recent first)
  const filteredEnrolled = useMemo(() => {
    const filtered = enrolledStudents.filter((student) => {
      if (selectedOrganization !== 'all' && student.organization_id !== selectedOrganization) return false
      if (selectedTrack !== 'all' && student.track_name !== selectedTrack) return false
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          student.user_email?.toLowerCase().includes(query) ||
          student.user_name?.toLowerCase().includes(query) ||
          student.organization_name?.toLowerCase().includes(query) ||
          student.id.toLowerCase().includes(query)
        )
      }
      return true
    })
    
    // Sort by joined_at descending (most recent first)
    return filtered.sort((a, b) => {
      const dateA = a.joined_at ? new Date(a.joined_at).getTime() : 0
      const dateB = b.joined_at ? new Date(b.joined_at).getTime() : 0
      return dateB - dateA // Descending order
    })
  }, [enrolledStudents, selectedOrganization, selectedTrack, searchQuery])

  // Paginated data
  const paginatedEnrolled = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage
    const end = start + itemsPerPage
    return filteredEnrolled.slice(start, end)
  }, [filteredEnrolled, currentPage, itemsPerPage])

  const totalPages = Math.ceil(filteredEnrolled.length / itemsPerPage)

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, selectedOrganization, selectedTrack])

  // Get or create "Director Enrollments" cohort (only used for display purposes)
  const getDirectorEnrollmentsCohort = async (): Promise<string | null> => {
    try {
      // Try to find existing "Director Enrollments" cohort
      const cohortsData = await apiGateway.get('/cohorts/') as any
      const cohortsList = cohortsData?.results || cohortsData?.data || cohortsData || []
      const directorCohort = cohortsList.find((c: any) => 
        c.name?.toLowerCase().includes('director enrollments') || 
        c.name?.toLowerCase().includes('director-enrolled')
      )
      
      if (directorCohort) {
        return directorCohort.id
      }

      // Don't create cohort automatically - return null if not found
      // Directors can enroll students without requiring a cohort
      return null
    } catch (err: any) {
      return null
    }
  }

  // Handle enrollment form steps
  const handleOrganizationChoice = (isFromOrg: boolean) => {
    setEnrollmentForm(prev => ({
      ...prev,
      isFromOrganization: isFromOrg,
      step: isFromOrg ? 'orgDetails' : 'student',
    }))
  }

  const handleOrgDetailsSubmit = async () => {
    if (enrollmentForm.numberOfStudents < 1) {
      setError('Number of students is required')
      return
    }
    
    if (!enrollmentForm.selectedOrganizationId) {
      setError('Please select an organization')
      return
    }
    if (!enrollmentForm.contactPersonName?.trim()) {
      setError('Contact person name is required')
      return
    }
    if (!enrollmentForm.contactEmail?.trim()) {
      setError('Contact email is required for sending the invoice')
      return
    }
    
    const students = Array(enrollmentForm.numberOfStudents).fill(null).map(() => ({
      first_name: '',
      last_name: '',
      email: '',
      gender: '',
      phone: '',
      country: '',
      subscription_plan_id: '',
    }))
    
    setEnrollmentForm(prev => ({
      ...prev,
      step: 'student',
      students,
      currentStudentIndex: 0,
      organizationId: enrollmentForm.selectedOrganizationId,
    }))
  }

  const handleStudentFieldChange = useCallback((field: keyof StudentFormData, value: string | boolean) => {
    setEnrollmentForm(prev => {
      const newStudents = [...prev.students]
      const currentStudent = newStudents[prev.currentStudentIndex]
      if (currentStudent) {
        // Handle boolean values (for checkbox)
        const processedValue = typeof value === 'boolean' ? value : value
        newStudents[prev.currentStudentIndex] = {
          ...currentStudent,
          [field]: processedValue,
        }
      }
      return {
        ...prev,
        students: newStudents,
      }
    })
  }, [])

  // Enroll a single student
  const enrollSingleStudent = async (student: StudentFormData): Promise<string | null> => {
    try {
      // Check if user already exists
      let userId: string | null = null
      try {
        const users = await apiGateway.get('/users/', { params: { search: student.email } }) as any
        const existingUser = users.results?.find((u: any) => u.email === student.email)
        
        if (existingUser) {
          userId = String(existingUser.id)
        }
      } catch (err) {
        // User doesn't exist, continue to create
      }

      // Create user if doesn't exist
      if (!userId) {
        const userData: any = {
          email: student.email.trim(),
          first_name: student.first_name.trim(),
          last_name: student.last_name.trim(),
          role: 'student',
          passwordless: true,
        }

        if (student.country && student.country.length === 2) {
          userData.country = student.country.toUpperCase()
        }

        if (student.phone) {
          userData.phone_number = student.phone.trim()
        }

        if (student.gender) {
          userData.gender = student.gender
        }

        // Add organization ID if enrolling from organization
        if (enrollmentForm.organizationId) {
          userData.org_id = enrollmentForm.organizationId
        }

        const signupResponse = await djangoClient.auth.signup(userData)
        if (signupResponse.user_id) {
          userId = String(signupResponse.user_id)
        } else {
          // Fallback: try to find user by email
          try {
            const users = await apiGateway.get('/users/', { params: { search: student.email } }) as any
            const newUser = users.results?.find((u: any) => u.email === student.email)
            if (newUser) {
              userId = String(newUser.id)
            } else {
              throw new Error(`Failed to find created user: ${student.email}`)
            }
          } catch (lookupErr) {
            throw new Error(`Failed to find created user: ${student.email}`)
          }
        }
      } else {
        // Update existing user with organization if enrolling from organization
        if (enrollmentForm.organizationId) {
          try {
            await apiGateway.patch(`/users/${userId}/`, {
              org_id: enrollmentForm.organizationId,
            })
          } catch (updateErr) {
            // Don't throw - user exists, org can be updated later
          }
        }
      }

      // Assign subscription plan
      const selectedPlan = enrollmentForm.subscriptionPlans.find(
        p => p.id === student.subscription_plan_id
      )
      
      if (selectedPlan) {
        let subscriptionAssigned = false
        try {
          // Check if subscription exists - use correct API path
          const existingSub = await apiGateway.get(`/admin/subscriptions/?user=${student.email}`).catch(() => null)
          const subscriptions = existingSub?.results || existingSub || []
          
          if (subscriptions.length > 0) {
            // Update existing subscription
            await apiGateway.patch(`/admin/subscriptions/${subscriptions[0].id}/`, {
              plan_id: selectedPlan.id,
              status: 'active',
            })
            subscriptionAssigned = true
          } else {
            // Create new subscription - use correct API path
            try {
              await apiGateway.post(`/admin/subscriptions/`, {
                user_id: userId,
                plan_id: selectedPlan.id,
                status: 'active',
              })
              subscriptionAssigned = true
            } catch (postErr: any) {
              // Fallback: try with 'user' field
              try {
                await apiGateway.post(`/admin/subscriptions/`, {
                  user: userId,
                  plan_id: selectedPlan.id,
                  status: 'active',
                })
                subscriptionAssigned = true
              } catch (fallbackErr: any) {
                // Log but don't throw - user is created, subscription can be assigned later
                throw new Error(`Subscription assignment failed: ${fallbackErr?.response?.data?.detail || fallbackErr?.message || 'Unknown error'}`)
              }
            }
          }
        } catch (subErr: any) {
          // If subscription assignment fails, still return userId but log warning
          // User is created successfully, subscription can be assigned manually later
          if (!subscriptionAssigned) {
          }
        }
      } else {
      }

      // Send onboarding email if checkbox is checked
      if (student.send_onboarding_email && userId) {
        try {
          await apiGateway.post('/admin/students/send-onboarding-email/', {
            user_id: userId,
          })
        } catch (emailErr: any) {
          // Don't throw - enrollment succeeded, email can be sent later
        }
      }

      return userId
    } catch (err: any) {
      throw err
    }
  }

  const handleNextStudent = async () => {
    const currentStudent = enrollmentForm.students[enrollmentForm.currentStudentIndex]
    
    // Validate current student
    if (!currentStudent.first_name || !currentStudent.last_name || !currentStudent.email) {
      setError('First name, last name, and email are required')
      return
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(currentStudent.email)) {
      setError('Please enter a valid email address')
      return
    }

    // Validate subscription plan
    if (!currentStudent.subscription_plan_id) {
      setError('Please select a subscription plan')
      return
    }

    // Validate country if provided (must be 2 letters)
    if (currentStudent.country && currentStudent.country.length !== 2) {
      setError('Country code must be 2 letters (e.g., BW, US, KE)')
      return
    }

    setError(null)
    setIsSubmitting(true)

    try {
      // Enroll the current student immediately
      const userId = await enrollSingleStudent(currentStudent)
      
      if (!userId) {
        throw new Error('Failed to create user account')
      }
      
      const currentIndex = enrollmentForm.currentStudentIndex + 1
      const totalStudents = enrollmentForm.students.length
      const newEnrolledCount = enrolledCount + 1
      
      setEnrolledCount(newEnrolledCount)
      
      // Show success toast with progress
      toast.success(
        `Student ${currentIndex}/${totalStudents} enrolled successfully!`,
        {
          duration: 3000,
          icon: '✅',
        }
      )

      // Reload enrollment data to show newly enrolled student immediately
      await loadData()

      // If this is the last student, complete and optionally create org invoice
      if (currentIndex >= totalStudents) {
        if (enrollmentForm.organizationId && enrollmentForm.contactEmail) {
          try {
            const plansMap = new Map(enrollmentForm.subscriptionPlans.map(p => [p.id, p]))
            const lineItems = enrollmentForm.students.map(s => {
              const plan = plansMap.get(s.subscription_plan_id)
              const amount = plan?.price_monthly ?? 0
              return {
                student_name: `${s.first_name} ${s.last_name}`.trim() || s.email,
                email: s.email,
                plan_name: plan?.name || '',
                amount_kes: amount,
              }
            })
            const totalAmountKes = lineItems.reduce((sum, i) => sum + (i.amount_kes || 0), 0)
            if (totalAmountKes > 0) {
              await apiGateway.post('/billing/org-enrollment-invoices/', {
                organization_id: enrollmentForm.organizationId,
                contact_person_name: enrollmentForm.contactPersonName?.trim() || enrollmentForm.organizationName,
                contact_email: enrollmentForm.contactEmail.trim(),
                contact_phone: enrollmentForm.contactPhone?.trim() || undefined,
                line_items: lineItems,
                total_amount_kes: totalAmountKes,
              })
              toast.success('Invoice sent to organization contact by email.', { duration: 5000 })
            }
          } catch (invErr: any) {
            toast.error(invErr?.response?.data?.error || 'Enrollment succeeded but invoice could not be sent. You can create it from Finance.')
          }
        }
        toast.success(
          `All ${totalStudents} student(s) enrolled successfully!`,
          {
            duration: 4000,
            icon: '🎉',
          }
        )
        
        // Close form and reset
        setTimeout(() => {
          setShowEnrollmentForm(false)
          setEnrolledCount(0)
          setEnrollmentForm(prev => ({
            ...prev,
            step: 'method',
            isFromOrganization: null,
            enrollmentMethod: null,
            organizationName: '',
            selectedOrganizationId: null,
            isCreatingNewOrg: false,
            numberOfStudents: 1,
            currentStudentIndex: 0,
            students: [{ 
              first_name: '', 
              last_name: '', 
              email: '', 
              gender: '',
              phone: '',
              country: '',
              subscription_plan_id: '',
              send_onboarding_email: false
            }],
            organizationId: null,
            subscriptionPlans: [],
            availableOrganizations: [],
            contactPersonName: '',
            contactEmail: '',
            contactPhone: '',
          }))
        }, 1500)
        return
      }

      // Move to next student
      setEnrollmentForm(prev => ({
        ...prev,
        currentStudentIndex: currentIndex,
      }))
    } catch (err: any) {
      const errorMessage = err?.message || 'Unknown error'
      setError(`Failed to enroll ${currentStudent.email}: ${errorMessage}`)
      toast.error(`Failed to enroll ${currentStudent.email}: ${errorMessage}`, {
        duration: 4000,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCompleteEnrollment = async () => {
    // This function is no longer needed since we enroll students one by one
    // But keeping it for backward compatibility - it will just enroll the current student
    // The "Complete" button should just call handleNextStudent which enrolls the last student
    await handleNextStudent()
  }

  const handleToggleStudentSelection = (studentId: string) => {
    setSelectedStudents(prev => {
      const newSet = new Set(prev)
      if (newSet.has(studentId)) {
        newSet.delete(studentId)
      } else {
        newSet.add(studentId)
      }
      return newSet
    })
  }

  const handleSelectAll = () => {
    if (selectedStudents.size === paginatedEnrolled.length) {
      setSelectedStudents(new Set())
    } else {
      setSelectedStudents(new Set(paginatedEnrolled.map(s => s.id)))
    }
  }

  const handleBulkSendOnboardingEmails = async () => {
    if (selectedStudents.size === 0) {
      toast.error('Please select at least one student')
      return
    }

    if (!confirm(`Send onboarding emails to ${selectedStudents.size} student(s)?`)) {
      return
    }

    setIsSendingEmails(true)
    setEmailProgress({ current: 0, total: selectedStudents.size })

    const studentIds = Array.from(selectedStudents)
    let successCount = 0
    let failCount = 0

    for (let i = 0; i < studentIds.length; i++) {
      const studentId = studentIds[i]
      try {
        const student = enrolledStudents.find(s => s.id === studentId)
        if (student?.user) {
          await apiGateway.post('/admin/students/send-onboarding-email/', {
            user_id: student.user,
          })
          successCount++
        }
      } catch (err: any) {
        failCount++
      }
      setEmailProgress({ current: i + 1, total: studentIds.length })
    }

    setIsSendingEmails(false)
    setSelectedStudents(new Set())
    
    if (successCount > 0) {
      toast.success(`Successfully sent ${successCount} onboarding email(s)`)
    }
    if (failCount > 0) {
      toast.error(`Failed to send ${failCount} email(s)`)
    }

    // Reload data to update onboarded status
    await loadData()
  }

  if (isLoading) {
    return (
      <RouteGuard>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-och-defender mx-auto mb-4"></div>
            <p className="text-och-steel">Loading enrollment data...</p>
          </div>
        </div>
      </RouteGuard>
    )
  }
 
  return (
    <RouteGuard>
      <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-4xl font-bold mb-2 text-och-defender">Enrollment Management</h1>
                <p className="text-och-steel">View and manage all enrolled students</p>
              </div>
              <Button
                variant="defender"
                size="sm"
                onClick={() => setShowEnrollmentForm(true)}
                className="flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Enroll Students
              </Button>
            </div>

            {error && (
              <Card className="mb-6 border-och-orange/50">
                <div className="p-4 text-och-orange">{error}</div>
              </Card>
            )}

            {/* Filter and Search - Horizontal Layout */}
            <Card className="mb-6">
              <div className="p-4">
                <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
                  {/* Organization Selection */}
                  <div className="flex-1 w-full sm:w-auto min-w-[200px]">
                    <label className="block text-sm font-medium text-white mb-2">Filter by Organization</label>
                    <select
                      value={selectedOrganization}
                      onChange={(e) => {
                        setSelectedOrganization(e.target.value)
                        setCurrentPage(1)
                      }}
                      className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                    >
                      <option value="all">All Organizations</option>
                      {organizations.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Track Selection */}
                  <div className="flex-1 w-full sm:w-auto min-w-[200px]">
                    <label className="block text-sm font-medium text-white mb-2">Filter by Track</label>
                    <select
                      value={selectedTrack}
                      onChange={(e) => {
                        setSelectedTrack(e.target.value)
                        setCurrentPage(1)
                      }}
                      className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                    >
                      <option value="all">All Tracks</option>
                      {[...new Set(enrolledStudents.map(s => s.track_name).filter(Boolean))].sort().map((track) => (
                        <option key={track} value={track}>
                          {track}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Search */}
                  <div className="flex-1 w-full sm:w-auto sm:min-w-[300px]">
                    <label className="block text-sm font-medium text-white mb-2">Search</label>
                    <Input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search by email, name, or ID..."
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Enrolled Students Table */}
          <Card>
            <div className="p-6">
              <h2 className="text-xl font-bold text-white mb-4">
                Enrolled Students ({filteredEnrolled.length})
              </h2>

              {filteredEnrolled.length === 0 ? (
                <div className="text-center py-12 text-och-steel">
                  <p>No enrolled students found.</p>
                </div>
              ) : (
                <>
                  {/* Bulk Actions */}
                  {selectedStudents.size > 0 && (
                    <div className="mb-4 p-4 bg-och-midnight/50 rounded-lg border border-och-defender/30 flex items-center justify-between">
                      <span className="text-white font-medium">
                        {selectedStudents.size} student(s) selected
                      </span>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedStudents(new Set())}
                        >
                          Clear Selection
                        </Button>
                        <Button
                          variant="orange"
                          size="sm"
                          onClick={() => setShowBulkDeleteModal(true)}
                          disabled={isDeleting}
                        >
                          Delete Selected
                        </Button>
                        <Button
                          variant="defender"
                          size="sm"
                          onClick={handleBulkSendOnboardingEmails}
                          disabled={isSendingEmails}
                        >
                          {isSendingEmails ? (
                            `Sending... ${emailProgress.current}/${emailProgress.total}`
                          ) : (
                            'Send Onboarding Email'
                          )}
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Email Progress Bar */}
                  {isSendingEmails && (
                    <div className="mb-4">
                      <div className="w-full bg-och-midnight/50 rounded-full h-2.5">
                        <div
                          className="bg-och-defender h-2.5 rounded-full transition-all duration-300"
                          style={{ width: `${(emailProgress.current / emailProgress.total) * 100}%` }}
                        ></div>
                      </div>
                      <p className="text-sm text-och-steel mt-1 text-center">
                        Sending emails: {emailProgress.current} of {emailProgress.total}
                      </p>
                    </div>
                  )}

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-och-steel/20">
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel w-12">
                            <input
                              type="checkbox"
                              checked={selectedStudents.size === paginatedEnrolled.length && paginatedEnrolled.length > 0}
                              onChange={handleSelectAll}
                              className="w-4 h-4 rounded border-och-steel/30 bg-och-midnight text-och-defender focus:ring-och-defender"
                            />
                          </th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel w-12">#</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Name</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Email</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Track</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Organization</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Enrollment Type</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Status</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Subscription</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Joined At</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Onboarded</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {paginatedEnrolled.map((student, index) => {
                          const rowNumber = (currentPage - 1) * itemsPerPage + index + 1
                          const joinedDate = student.joined_at 
                            ? new Date(student.joined_at)
                            : null
                          const formattedDate = joinedDate
                            ? joinedDate.toLocaleDateString('en-US', { 
                                year: 'numeric', 
                                month: 'short', 
                                day: 'numeric' 
                              })
                            : 'N/A'
                          const formattedTime = joinedDate
                            ? joinedDate.toLocaleTimeString('en-US', { 
                                hour: '2-digit', 
                                minute: '2-digit',
                                hour12: true
                              })
                            : ''
                          
                          const onboardedStatus = student.onboarded_email_status || null
                          const onboardedLabel = onboardedStatus === 'sent_and_seen' 
                            ? 'Sent & Seen' 
                            : onboardedStatus === 'sent' 
                            ? 'Sent' 
                            : 'Not Sent'
                          
                          return (
                            <tr
                              key={student.id}
                              className="border-b border-och-steel/10 hover:bg-och-midnight/30 transition-colors"
                            >
                              <td className="py-3 px-4">
                                <input
                                  type="checkbox"
                                  checked={selectedStudents.has(student.id)}
                                  onChange={() => handleToggleStudentSelection(student.id)}
                                  className="w-4 h-4 rounded border-och-steel/30 bg-och-midnight text-och-defender focus:ring-och-defender"
                                />
                              </td>
                              <td className="py-3 px-4 text-och-steel text-sm font-medium">
                                {rowNumber}
                              </td>
                              <td className="py-3 px-4 text-white">
                                {student.user_name || 'N/A'}
                              </td>
                              <td className="py-3 px-4 text-och-steel">
                                {student.user_email || student.user}
                              </td>
                              <td className="py-3 px-4">
                                {student.track_name ? (
                                  <Badge variant="outline">{student.track_name}</Badge>
                                ) : (
                                  <span className="text-och-steel/50">No track</span>
                                )}
                              </td>
                              <td className="py-3 px-4 text-och-steel">
                                {student.organization_name || 'N/A'}
                              </td>
                              <td className="py-3 px-4">
                                <Badge variant="outline">
                                  {ENROLLMENT_TYPE_LABELS[student.enrollment_type] || student.enrollment_type}
                                </Badge>
                              </td>
                              <td className="py-3 px-4">
                                <Badge
                                  variant={
                                    student.status === 'active' ? 'mint' :
                                    student.status === 'pending_payment' || student.status === 'pending' ? 'orange' :
                                    'outline'
                                  }
                                >
                                  {student.status}
                                </Badge>
                              </td>
                              <td className="py-3 px-4">
                                {student.subscription_plan_name ? (
                                  <Badge variant="mint">{student.subscription_plan_name}</Badge>
                                ) : (
                                  <Badge variant="outline">Not Set</Badge>
                                )}
                              </td>
                              <td className="py-3 px-4 text-och-steel text-sm">
                                {joinedDate ? (
                                  <div>
                                    <div>{formattedDate}</div>
                                    <div className="text-xs text-och-steel/70">{formattedTime}</div>
                                  </div>
                                ) : (
                                  <span className="text-och-steel/50">N/A</span>
                                )}
                              </td>
                              <td className="py-3 px-4">
                                <Badge
                                  variant={
                                    onboardedStatus === 'sent_and_seen' ? 'mint' :
                                    onboardedStatus === 'sent' ? 'orange' :
                                    'outline'
                                  }
                                >
                                  {onboardedLabel}
                                </Badge>
                              </td>
                              <td className="py-3 px-4">
                                <IconButton
                                  onClick={(e) => handleOpenActionMenu(e, student.id, student)}
                                  size="small"
                                  sx={{ color: '#00d4ff' }}
                                >
                                  <MoreVertIcon />
                                </IconButton>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="mt-6 flex items-center justify-between border-t border-och-steel/20 pt-4">
                      <div className="text-sm text-och-steel">
                        Showing {(currentPage - 1) * itemsPerPage + 1} to{' '}
                        {Math.min(currentPage * itemsPerPage, filteredEnrolled.length)} of {filteredEnrolled.length} entries
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                          disabled={currentPage === 1}
                        >
                          Previous
                        </Button>
                        <div className="flex items-center gap-1">
                          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                            let pageNum: number
                            if (totalPages <= 5) {
                              pageNum = i + 1
                            } else if (currentPage <= 3) {
                              pageNum = i + 1
                            } else if (currentPage >= totalPages - 2) {
                              pageNum = totalPages - 4 + i
                            } else {
                              pageNum = currentPage - 2 + i
                            }
                            return (
                              <Button
                                key={pageNum}
                                variant={currentPage === pageNum ? 'defender' : 'outline'}
                                size="sm"
                                onClick={() => setCurrentPage(pageNum)}
                                className="min-w-[2.5rem]"
                              >
                                {pageNum}
                              </Button>
                            )
                          })}
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                          disabled={currentPage === totalPages}
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </Card>

          {/* MUI Action Menu */}
          <Menu
            anchorEl={actionMenuAnchor}
            open={Boolean(actionMenuAnchor)}
            onClose={handleCloseActionMenu}
            PaperProps={{
              sx: {
                bgcolor: '#0f1419',
                border: '1px solid rgba(148, 163, 184, 0.2)',
                borderRadius: '8px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
              }
            }}
          >
            <MenuItem
              onClick={() => {
                if (studentForAction) {
                  setSelectedStudentDetails(studentForAction)
                  setShowStudentDetailsModal(true)
                }
                handleCloseActionMenu()
              }}
              sx={{ color: '#fff', fontSize: '14px', '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.05)' } }}
            >
              View Details
            </MenuItem>
            <MenuItem
              onClick={() => {
                setShowChangeTrackModal(true)
                handleCloseActionMenu()
                apiGateway.get('/curriculum/tracks/').then((data: any) => {
                  const list = data?.results ?? data?.data ?? data ?? []
                  setCurriculumTracks(Array.isArray(list) ? list : [])
                }).catch(() => setCurriculumTracks([]))
              }}
              sx={{ color: '#fff', fontSize: '14px', '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.05)' } }}
            >
              Change Track
            </MenuItem>
            <MenuItem
              onClick={() => {
                if (studentForAction) {
                  apiGateway.get(`/users/${studentForAction.user}/`).then((userData: any) => {
                    setEditFormData({
                      first_name: userData.first_name || '',
                      last_name: userData.last_name || '',
                      email: userData.email || '',
                      phone_number: userData.phone_number || '',
                      country: userData.country || '',
                      organization_id: studentForAction.organization_id || '',
                    })
                    setShowEditModal(true)
                    handleCloseActionMenu()
                  }).catch(() => {
                    toast.error('Failed to load student data')
                    handleCloseActionMenu()
                  })
                }
              }}
              sx={{ color: '#fff', fontSize: '14px', '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.05)' } }}
            >
              Edit
            </MenuItem>
            <MenuItem
              onClick={() => {
                setShowDeleteModal(true)
                handleCloseActionMenu()
              }}
              sx={{ color: '#ff6b6b', fontSize: '14px', '&:hover': { bgcolor: 'rgba(255, 107, 107, 0.1)' } }}
            >
              Delete
            </MenuItem>
            <MenuItem
              onClick={() => {
                setShowReportModal(true)
                handleCloseActionMenu()
              }}
              sx={{ color: '#fff', fontSize: '14px', '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.05)' } }}
            >
              Report
            </MenuItem>
          </Menu>

          {/* Enrollment Form Modal */}
          {showEnrollmentForm && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-white">Enroll Students</h2>
                    <button
                      onClick={() => {
                        setShowEnrollmentForm(false)
        // Reset form and counters
        setEnrolledCount(0)
        setShowEnrollmentForm(false)
        setEnrollmentForm({
          step: 'method',
          isFromOrganization: null,
          enrollmentMethod: null,
          organizationName: '',
          selectedOrganizationId: null,
          isCreatingNewOrg: false,
          numberOfStudents: 1,
          currentStudentIndex: 0,
          students: [{ 
            first_name: '', 
            last_name: '', 
            email: '', 
            gender: '',
            phone: '',
            country: '',
            subscription_plan_id: '',
            send_onboarding_email: false
          }],
          organizationId: null,
          subscriptionPlans: [],
          availableOrganizations: [],
          contactPersonName: '',
          contactEmail: '',
          contactPhone: '',
          importFile: null,
          csvPreview: null,
        })
                        setError(null)
                      }}
                      className="text-och-steel hover:text-white"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>

                  {error && (
                    <div className="mb-4 p-3 bg-och-orange/10 border border-och-orange/30 rounded-lg">
                      <p className="text-och-orange text-sm">{error}</p>
                    </div>
                  )}

                  {/* Step 0: Enrollment method (manual vs import) */}
                  {enrollmentForm.step === 'method' && (
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-white">How would you like to add students?</h3>
                      <p className="text-sm text-och-steel">
                        Choose whether to enter students one-by-one or prepare a CSV/Excel file to import.
                      </p>
                      <div className="flex flex-col gap-3">
                        <Button
                          variant="defender"
                          className="w-full justify-start"
                          onClick={() =>
                            setEnrollmentForm(prev => ({
                              ...prev,
                              enrollmentMethod: 'manual',
                              step: 'organization',
                            }))
                          }
                        >
                          <span>Add students manually</span>
                        </Button>
                        <Button
                          variant="outline"
                          className="w-full justify-start"
                          onClick={() =>
                            setEnrollmentForm(prev => ({
                              ...prev,
                              enrollmentMethod: 'import',
                              step: 'import',
                            }))
                          }
                        >
                          <span>Import from CSV / Excel</span>
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Step 1: Organization Question */}
                  {enrollmentForm.step === 'organization' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-white mb-4">
                          Is the student from an organization?
                        </label>
                        <div className="flex gap-4">
                          <Button
                            variant={enrollmentForm.isFromOrganization === true ? 'defender' : 'outline'}
                            onClick={() => handleOrganizationChoice(true)}
                          >
                            Yes
                          </Button>
                          <Button
                            variant={enrollmentForm.isFromOrganization === false ? 'defender' : 'outline'}
                            onClick={() => handleOrganizationChoice(false)}
                          >
                            No
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Step 2: Organization Details */}
                  {enrollmentForm.step === 'orgDetails' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Select Organization *
                        </label>
                        <select
                          value={enrollmentForm.selectedOrganizationId || ''}
                          onChange={(e) => {
                            const orgId = e.target.value || null
                            setEnrollmentForm(prev => {
                              const selectedOrg = prev.availableOrganizations.find((org: any) => String(org.id) === String(orgId))
                              return {
                                ...prev,
                                selectedOrganizationId: orgId,
                                organizationId: orgId,
                                contactPersonName: selectedOrg?.contact_person_name || prev.contactPersonName,
                                contactEmail: selectedOrg?.contact_email || prev.contactEmail,
                                contactPhone: selectedOrg?.contact_phone || prev.contactPhone,
                              }
                            })
                          }}
                          className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                        >
                          <option value="">Select an organization</option>
                          {enrollmentForm.availableOrganizations.map((org: any) => (
                            <option key={org.id} value={org.id}>
                              {org.name} {org.org_type ? `(${org.org_type})` : ''}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      {enrollmentForm.selectedOrganizationId && (
                        <>
                          <div className="space-y-3">
                            <label className="block text-sm font-medium text-white mb-2">
                              Organization contact *
                            </label>
                            <Input
                              type="text"
                              value={enrollmentForm.contactPersonName}
                              onChange={(e) => setEnrollmentForm(prev => ({ ...prev, contactPersonName: e.target.value }))}
                              placeholder="Contact person name"
                            />
                            <Input
                              type="email"
                              value={enrollmentForm.contactEmail}
                              onChange={(e) => setEnrollmentForm(prev => ({ ...prev, contactEmail: e.target.value }))}
                              placeholder="Contact email"
                            />
                            <Input
                              type="tel"
                              value={enrollmentForm.contactPhone}
                              onChange={(e) => setEnrollmentForm(prev => ({ ...prev, contactPhone: e.target.value }))}
                              placeholder="Contact phone (optional)"
                            />
                          </div>
                          
                          {enrollmentForm.enrollmentMethod === 'manual' && (
                            <div>
                              <label className="block text-sm font-medium text-white mb-2">
                                Number of Students *
                              </label>
                              <Input
                                type="number"
                                min="1"
                                value={enrollmentForm.numberOfStudents}
                                onChange={(e) => setEnrollmentForm(prev => ({ ...prev, numberOfStudents: parseInt(e.target.value) || 1 }))}
                                placeholder="Enter number of students"
                              />
                            </div>
                          )}
                        </>
                      )}
                      
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          onClick={() => setEnrollmentForm(prev => ({ ...prev, step: 'organization' }))}
                        >
                          Back
                        </Button>
                        <Button
                          variant="defender"
                          onClick={handleOrgDetailsSubmit}
                        >
                          Continue
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Step: Import CSV/Excel */}
                  {enrollmentForm.step === 'import' && (
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-white mb-4">Import Students from CSV/Excel</h3>
                      
                      <div>
                        <label className="block text-sm font-medium text-white mb-4">
                          Is the student from an organization?
                        </label>
                        <div className="flex gap-4 mb-6">
                          <Button
                            variant={enrollmentForm.isFromOrganization === true ? 'defender' : 'outline'}
                            onClick={() => setEnrollmentForm(prev => ({ ...prev, isFromOrganization: true }))}
                          >
                            Yes
                          </Button>
                          <Button
                            variant={enrollmentForm.isFromOrganization === false ? 'defender' : 'outline'}
                            onClick={() => setEnrollmentForm(prev => ({ ...prev, isFromOrganization: false }))}
                          >
                            No
                          </Button>
                        </div>
                      </div>

                      {enrollmentForm.isFromOrganization === true && (
                        <div className="space-y-4 mb-6">
                          <div>
                            <label className="block text-sm font-medium text-white mb-2">
                              Select Organization *
                            </label>
                            <select
                              value={enrollmentForm.selectedOrganizationId || ''}
                              onChange={(e) => {
                                const orgId = e.target.value || null
                                setEnrollmentForm(prev => {
                                  const selectedOrg = prev.availableOrganizations.find((org: any) => String(org.id) === String(orgId))
                                  return {
                                    ...prev,
                                    selectedOrganizationId: orgId,
                                    organizationId: orgId,
                                    contactPersonName: selectedOrg?.contact_person_name || prev.contactPersonName,
                                    contactEmail: selectedOrg?.contact_email || prev.contactEmail,
                                    contactPhone: selectedOrg?.contact_phone || prev.contactPhone,
                                  }
                                })
                              }}
                              className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                            >
                              <option value="">Select an organization</option>
                              {enrollmentForm.availableOrganizations.map((org: any) => (
                                <option key={org.id} value={org.id}>
                                  {org.name} {org.org_type ? `(${org.org_type})` : ''}
                                </option>
                              ))}
                            </select>
                          </div>
                          
                          {enrollmentForm.selectedOrganizationId && (
                            <div className="space-y-3">
                              <label className="block text-sm font-medium text-white mb-2">
                                Organization contact *
                              </label>
                              <Input
                                type="text"
                                value={enrollmentForm.contactPersonName}
                                onChange={(e) => setEnrollmentForm(prev => ({ ...prev, contactPersonName: e.target.value }))}
                                placeholder="Contact person name"
                              />
                              <Input
                                type="email"
                                value={enrollmentForm.contactEmail}
                                onChange={(e) => setEnrollmentForm(prev => ({ ...prev, contactEmail: e.target.value }))}
                                placeholder="Contact email"
                              />
                              <Input
                                type="tel"
                                value={enrollmentForm.contactPhone}
                                onChange={(e) => setEnrollmentForm(prev => ({ ...prev, contactPhone: e.target.value }))}
                                placeholder="Contact phone (optional)"
                              />
                            </div>
                          )}
                        </div>
                      )}

                      {(enrollmentForm.isFromOrganization === false || (enrollmentForm.isFromOrganization === true && enrollmentForm.selectedOrganizationId && enrollmentForm.contactPersonName && enrollmentForm.contactEmail)) && (
                        <>
                          <div className="p-4 bg-och-midnight/50 border border-och-steel/20 rounded-lg mb-4">
                            <h4 className="text-sm font-medium text-white mb-2">CSV Format Requirements:</h4>
                            <p className="text-xs text-och-steel mb-2">Your CSV file must include these columns:</p>
                            <ul className="text-xs text-och-steel list-disc list-inside space-y-1">
                              <li><span className="text-white">first_name</span> (required)</li>
                              <li><span className="text-white">last_name</span> (required)</li>
                              <li><span className="text-white">email</span> (required)</li>
                              <li><span className="text-white">subscription_plan_id</span> (required)</li>
                              <li><span className="text-white">gender</span> (optional: male, female, other, prefer_not_to_say)</li>
                              <li><span className="text-white">phone</span> (optional)</li>
                              <li><span className="text-white">country</span> (optional: 2-letter code like BW, US, KE)</li>
                              <li><span className="text-white">send_onboarding_email</span> (optional: true/false)</li>
                            </ul>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-white mb-2">
                              Upload CSV File *
                            </label>
                            <input
                              type="file"
                              accept=".csv"
                              onChange={async (e) => {
                                const file = e.target.files?.[0] || null
                                if (!file) {
                                  setEnrollmentForm(prev => ({ ...prev, importFile: null, csvPreview: null }))
                                  return
                                }
                                setEnrollmentForm(prev => ({ ...prev, importFile: file }))
                                
                                // Auto-preview on file select
                                setIsSubmitting(true)
                                setError(null)
                                try {
                                  const text = await file.text()
                                  const lines = text.split('\n').filter(l => l.trim())
                                  if (lines.length < 2) {
                                    throw new Error('CSV file must have at least a header row and one data row')
                                  }
                                  const headers = lines[0].split(',').map(h => h.trim())
                                  const requiredHeaders = ['first_name', 'last_name', 'email', 'subscription_plan_id']
                                  const optionalHeaders = ['gender', 'phone', 'country', 'send_onboarding_email']
                                  const allExpectedHeaders = [...requiredHeaders, ...optionalHeaders]
                                  
                                  const matchedHeaders = headers.filter(h => allExpectedHeaders.includes(h))
                                  const missingHeaders = requiredHeaders.filter(h => !headers.includes(h))
                                  const extraHeaders = headers.filter(h => !allExpectedHeaders.includes(h))
                                  
                                  const rows: any[] = []
                                  for (let i = 1; i < Math.min(6, lines.length); i++) {
                                    const values = lines[i].split(',').map(v => v.trim())
                                    const row: any = {}
                                    headers.forEach((h, idx) => {
                                      row[h] = values[idx] || ''
                                    })
                                    rows.push(row)
                                  }
                                  
                                  setEnrollmentForm(prev => ({
                                    ...prev,
                                    csvPreview: {
                                      headers,
                                      matchedHeaders,
                                      missingHeaders,
                                      extraHeaders,
                                      rows,
                                    },
                                    step: 'preview',
                                  }))
                                } catch (err: any) {
                                  setError(err.message || 'Failed to parse CSV file')
                                  setEnrollmentForm(prev => ({ ...prev, importFile: null, csvPreview: null }))
                                } finally {
                                  setIsSubmitting(false)
                                }
                              }}
                              className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-och-defender file:text-white hover:file:bg-och-defender/80"
                            />
                          </div>
                        </>
                      )}

                      <div className="flex gap-2 pt-4">
                        <Button
                          variant="outline"
                          onClick={() => setEnrollmentForm(prev => ({ ...prev, step: 'method', importFile: null, isFromOrganization: null, selectedOrganizationId: null, csvPreview: null }))}
                        >
                          Back
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Step: Preview CSV */}
                  {enrollmentForm.step === 'preview' && enrollmentForm.csvPreview && (
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-white mb-4">CSV Preview - Edit if needed</h3>
                      
                      <div className="space-y-4">
                        {enrollmentForm.csvPreview.missingHeaders.length > 0 && (
                          <div className="p-4 bg-och-orange/10 border border-och-orange/30 rounded-lg">
                            <h4 className="text-sm font-medium text-och-orange mb-2">⚠ Missing Required Columns ({enrollmentForm.csvPreview.missingHeaders.length})</h4>
                            <div className="flex flex-wrap gap-2">
                              {enrollmentForm.csvPreview.missingHeaders.map(h => (
                                <Badge key={h} variant="orange">{h}</Badge>
                              ))}
                            </div>
                            <p className="text-xs text-och-orange mt-2">Please add these columns to your CSV file</p>
                          </div>
                        )}
                        
                        {enrollmentForm.csvPreview.extraHeaders.length > 0 && (
                          <div className="p-4 bg-och-steel/10 border border-och-steel/30 rounded-lg">
                            <h4 className="text-sm font-medium text-och-steel mb-2">ℹ Extra Columns ({enrollmentForm.csvPreview.extraHeaders.length})</h4>
                            <div className="flex flex-wrap gap-2">
                              {enrollmentForm.csvPreview.extraHeaders.map(h => (
                                <Badge key={h} variant="outline">{h}</Badge>
                              ))}
                            </div>
                            <p className="text-xs text-och-steel mt-2">These columns will be ignored</p>
                          </div>
                        )}
                        
                        <div className="p-4 bg-och-midnight/50 border border-och-steel/20 rounded-lg">
                          <h4 className="text-sm font-medium text-white mb-3">Preview - Click cells to edit</h4>
                          <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="border-b border-och-steel/20">
                                  <th className="text-left py-2 px-3 text-och-steel">Status</th>
                                  {enrollmentForm.csvPreview.matchedHeaders.map(h => (
                                    <th key={h} className="text-left py-2 px-3 text-och-steel">{h}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {enrollmentForm.csvPreview.rows.map((row, idx) => {
                                  const requiredFields = ['first_name', 'last_name', 'email', 'subscription_plan_id']
                                  const missingFields = requiredFields.filter(f => !row[f] || !row[f].trim())
                                  const isValid = missingFields.length === 0
                                  
                                  return (
                                    <tr key={idx} className="border-b border-och-steel/10">
                                      <td className="py-2 px-3">
                                        {isValid ? (
                                          <Badge variant="mint">OK</Badge>
                                        ) : (
                                          <Badge variant="orange">Fix</Badge>
                                        )}
                                      </td>
                                      {enrollmentForm.csvPreview!.matchedHeaders.map(h => {
                                        const value = row[h] || ''
                                        const isRequired = requiredFields.includes(h)
                                        const isEmpty = !value.trim()
                                        const needsFix = isRequired && isEmpty
                                        
                                        if (h === 'subscription_plan_id') {
                                          return (
                                            <td key={h} className={`py-2 px-3 ${needsFix ? 'bg-och-orange/10' : ''}`}>
                                              <select
                                                value={value}
                                                onChange={(e) => {
                                                  const newRows = [...enrollmentForm.csvPreview!.rows]
                                                  newRows[idx][h] = e.target.value
                                                  setEnrollmentForm(prev => ({
                                                    ...prev,
                                                    csvPreview: prev.csvPreview ? {
                                                      ...prev.csvPreview,
                                                      rows: newRows,
                                                    } : null,
                                                  }))
                                                }}
                                                className="w-full px-2 py-1 bg-och-midnight border border-och-steel/20 rounded text-white text-xs focus:outline-none focus:border-och-defender"
                                              >
                                                <option value="">Select plan</option>
                                                {enrollmentForm.subscriptionPlans.map(plan => (
                                                  <option key={plan.id} value={plan.id}>
                                                    {plan.name} ({plan.tier})
                                                  </option>
                                                ))}
                                              </select>
                                            </td>
                                          )
                                        }
                                        if (h === 'gender') {
                                          return (
                                            <td key={h} className={`py-2 px-3 ${needsFix ? 'bg-och-orange/10' : ''}`}>
                                              <select
                                                value={value}
                                                onChange={(e) => {
                                                  const newRows = [...enrollmentForm.csvPreview!.rows]
                                                  newRows[idx][h] = e.target.value
                                                  setEnrollmentForm(prev => ({
                                                    ...prev,
                                                    csvPreview: prev.csvPreview ? {
                                                      ...prev.csvPreview,
                                                      rows: newRows,
                                                    } : null,
                                                  }))
                                                }}
                                                className="w-full px-2 py-1 bg-och-midnight border border-och-steel/20 rounded text-white text-xs focus:outline-none focus:border-och-defender"
                                              >
                                                <option value="">Select</option>
                                                <option value="male">Male</option>
                                                <option value="female">Female</option>
                                                <option value="other">Other</option>
                                                <option value="prefer_not_to_say">Prefer not to say</option>
                                              </select>
                                            </td>
                                          )
                                        }
                                        if (h === 'send_onboarding_email') {
                                          return (
                                            <td key={h} className={`py-2 px-3 ${needsFix ? 'bg-och-orange/10' : ''}`}>
                                              <select
                                                value={value === true || value === 'true' ? 'true' : value === false || value === 'false' ? 'false' : value}
                                                onChange={(e) => {
                                                  const newRows = [...enrollmentForm.csvPreview!.rows]
                                                  newRows[idx][h] = e.target.value
                                                  setEnrollmentForm(prev => ({
                                                    ...prev,
                                                    csvPreview: prev.csvPreview ? {
                                                      ...prev.csvPreview,
                                                      rows: newRows,
                                                    } : null,
                                                  }))
                                                }}
                                                className="w-full px-2 py-1 bg-och-midnight border border-och-steel/20 rounded text-white text-xs focus:outline-none focus:border-och-defender"
                                              >
                                                <option value="">Select</option>
                                                <option value="true">Yes</option>
                                                <option value="false">No</option>
                                              </select>
                                            </td>
                                          )
                                        }
                                        
                                        return (
                                          <td key={h} className={`py-2 px-3 ${needsFix ? 'bg-och-orange/10' : ''}`}>
                                            <input
                                              type="text"
                                              value={value}
                                              onChange={(e) => {
                                                const newRows = [...enrollmentForm.csvPreview!.rows]
                                                newRows[idx][h] = e.target.value
                                                setEnrollmentForm(prev => ({
                                                  ...prev,
                                                  csvPreview: prev.csvPreview ? {
                                                    ...prev.csvPreview,
                                                    rows: newRows,
                                                  } : null,
                                                }))
                                              }}
                                              className={`w-full px-2 py-1 bg-transparent border-0 focus:bg-och-midnight focus:outline-none focus:ring-1 focus:ring-och-defender rounded ${needsFix ? 'text-och-orange' : 'text-white'}`}
                                            />
                                          </td>
                                        )
                                      })}
                                    </tr>
                                  )
                                })}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>

                      <div className="flex gap-2 pt-4">
                        <Button
                          variant="outline"
                          onClick={() => setEnrollmentForm(prev => ({ ...prev, step: 'import', csvPreview: null }))}
                        >
                          Back
                        </Button>
                        <Button
                          variant="defender"
                          onClick={async () => {
                            if (enrollmentForm.csvPreview!.missingHeaders.length > 0) {
                              setError(`Missing required columns: ${enrollmentForm.csvPreview!.missingHeaders.join(', ')}`)
                              return
                            }
                            
                            // Validate all rows
                            const requiredFields = ['first_name', 'last_name', 'email', 'subscription_plan_id']
                            const invalidRows = enrollmentForm.csvPreview!.rows.filter((row, idx) => {
                              return requiredFields.some(f => !row[f] || !row[f].trim())
                            })
                            
                            if (invalidRows.length > 0) {
                              setError(`${invalidRows.length} row(s) have missing required fields. Please fix them before continuing.`)
                              return
                            }
                            
                            setIsSubmitting(true)
                            setError(null)
                            try {
                              const students: StudentFormData[] = enrollmentForm.csvPreview!.rows.map(row => ({
                                first_name: row.first_name || '',
                                last_name: row.last_name || '',
                                email: row.email || '',
                                gender: row.gender || '',
                                phone: row.phone || '',
                                country: row.country || '',
                                subscription_plan_id: row.subscription_plan_id || '',
                                send_onboarding_email: row.send_onboarding_email === 'true',
                              }))
                              
                              // Enroll all students directly
                              let successCount = 0
                              let failCount = 0
                              const errors: string[] = []
                              
                              for (let i = 0; i < students.length; i++) {
                                try {
                                  const userId = await enrollSingleStudent(students[i])
                                  if (userId) {
                                    successCount++
                                    toast.success(`Enrolled ${students[i].email} (${i + 1}/${students.length})`, { duration: 2000 })
                                  } else {
                                    failCount++
                                    errors.push(students[i].email)
                                  }
                                } catch (err: any) {
                                  failCount++
                                  errors.push(`${students[i].email}: ${err.message}`)
                                }
                              }
                              
                              if (successCount > 0) {
                                toast.success(`Successfully enrolled ${successCount} student(s)!`, { duration: 4000, icon: '🎉' })
                                await loadData()
                              }
                              
                              if (failCount > 0) {
                                toast.error(`Failed to enroll ${failCount} student(s). Check console for details.`, { duration: 4000 })
                                console.error('Enrollment errors:', errors)
                              }
                              
                              // Create invoice if from organization
                              if (enrollmentForm.organizationId && enrollmentForm.contactEmail && successCount > 0) {
                                try {
                                  const plansMap = new Map(enrollmentForm.subscriptionPlans.map(p => [p.id, p]))
                                  const lineItems = students.map(s => {
                                    const plan = plansMap.get(s.subscription_plan_id)
                                    const amount = plan?.price_monthly ?? 0
                                    return {
                                      student_name: `${s.first_name} ${s.last_name}`.trim() || s.email,
                                      email: s.email,
                                      plan_name: plan?.name || '',
                                      amount_kes: amount,
                                    }
                                  })
                                  const totalAmountKes = lineItems.reduce((sum, i) => sum + (i.amount_kes || 0), 0)
                                  if (totalAmountKes > 0) {
                                    await apiGateway.post('/billing/org-enrollment-invoices/', {
                                      organization_id: enrollmentForm.organizationId,
                                      contact_person_name: enrollmentForm.contactPersonName?.trim() || enrollmentForm.organizationName,
                                      contact_email: enrollmentForm.contactEmail.trim(),
                                      contact_phone: enrollmentForm.contactPhone?.trim() || undefined,
                                      line_items: lineItems,
                                      total_amount_kes: totalAmountKes,
                                    })
                                    toast.success('Invoice sent to organization contact by email.', { duration: 5000 })
                                  }
                                } catch (invErr: any) {
                                  toast.error('Enrollment succeeded but invoice could not be sent.')
                                }
                              }
                              
                              // Close form
                              setTimeout(() => {
                                setShowEnrollmentForm(false)
                                setEnrolledCount(0)
                                setEnrollmentForm({
                                  step: 'method',
                                  isFromOrganization: null,
                                  enrollmentMethod: null,
                                  organizationName: '',
                                  selectedOrganizationId: null,
                                  isCreatingNewOrg: false,
                                  numberOfStudents: 1,
                                  currentStudentIndex: 0,
                                  students: [{ 
                                    first_name: '', 
                                    last_name: '', 
                                    email: '', 
                                    gender: '',
                                    phone: '',
                                    country: '',
                                    subscription_plan_id: '',
                                    send_onboarding_email: false
                                  }],
                                  organizationId: null,
                                  subscriptionPlans: [],
                                  availableOrganizations: [],
                                  contactPersonName: '',
                                  contactEmail: '',
                                  contactPhone: '',
                                  importFile: null,
                                  csvPreview: null,
                                })
                              }, 1500)
                            } catch (err: any) {
                              setError(err.message || 'Failed to enroll students')
                            } finally {
                              setIsSubmitting(false)
                            }
                          }}
                          disabled={enrollmentForm.csvPreview.missingHeaders.length > 0 || isSubmitting}
                        >
                          {isSubmitting ? 'Enrolling...' : `Enroll All ${enrollmentForm.csvPreview.rows.length} Students`}
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Step 3: Student Form */}
                  {enrollmentForm.step === 'student' && (
                    <div className="space-y-4">
                      <div className="mb-4 p-3 bg-och-midnight/50 rounded-lg border border-och-steel/20">
                        <div className="flex items-center justify-between">
                          <span className="text-white font-semibold">
                            Student {enrollmentForm.currentStudentIndex + 1} of {enrollmentForm.students.length}
                          </span>
                          {enrolledCount > 0 && (
                            <Badge variant="mint" className="text-sm">
                              {enrolledCount} enrolled
                            </Badge>
                          )}
                        </div>
                        {enrolledCount > 0 && (
                          <p className="text-xs text-och-steel mt-1">
                            Progress: {enrolledCount}/{enrollmentForm.students.length} students enrolled
                          </p>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          First Name *
                        </label>
                        <Input
                          type="text"
                          value={enrollmentForm.students[enrollmentForm.currentStudentIndex]?.first_name || ''}
                          onChange={(e) => handleStudentFieldChange('first_name', e.target.value)}
                          placeholder="John"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Last Name *
                        </label>
                        <Input
                          type="text"
                          value={enrollmentForm.students[enrollmentForm.currentStudentIndex]?.last_name || ''}
                          onChange={(e) => handleStudentFieldChange('last_name', e.target.value)}
                          placeholder="Doe"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Email Address *
                        </label>
                        <Input
                          type="email"
                          value={enrollmentForm.students[enrollmentForm.currentStudentIndex]?.email || ''}
                          onChange={(e) => handleStudentFieldChange('email', e.target.value)}
                          placeholder="your.email@example.com"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Gender (Optional)
                        </label>
                        <select
                          value={enrollmentForm.students[enrollmentForm.currentStudentIndex]?.gender || ''}
                          onChange={(e) => handleStudentFieldChange('gender', e.target.value)}
                          className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                        >
                          {GENDER_OPTIONS.map(option => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Phone (Optional)
                        </label>
                        <Input
                          type="tel"
                          value={enrollmentForm.students[enrollmentForm.currentStudentIndex]?.phone || ''}
                          onChange={(e) => handleStudentFieldChange('phone', e.target.value)}
                          placeholder="+1234567890"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Country (Optional)
                        </label>
                        <Input
                          type="text"
                          maxLength={2}
                          value={enrollmentForm.students[enrollmentForm.currentStudentIndex]?.country || ''}
                          onChange={(e) => handleStudentFieldChange('country', e.target.value.toUpperCase())}
                          placeholder="BW"
                        />
                        <p className="text-xs text-och-steel mt-1">
                          2-letter ISO code (e.g., BW, US, KE)
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Subscription Plan *
                        </label>
                        <select
                          value={enrollmentForm.students[enrollmentForm.currentStudentIndex]?.subscription_plan_id || ''}
                          onChange={(e) => handleStudentFieldChange('subscription_plan_id', e.target.value)}
                          className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                        >
                          <option value="">Select subscription plan</option>
                          {enrollmentForm.subscriptionPlans.map(plan => {
                            const price = typeof plan.price_monthly === 'number' 
                              ? plan.price_monthly 
                              : plan.price_monthly 
                                ? parseFloat(String(plan.price_monthly)) 
                                : 0
                            const priceDisplay = price > 0 ? `$${price.toFixed(2)}/month` : 'Free'
                            return (
                              <option key={plan.id} value={plan.id}>
                                {plan.name} ({plan.tier}) - {priceDisplay}
                              </option>
                            )
                          })}
                        </select>
                        <p className="text-xs text-och-steel mt-1">
                          Select a plan created by admin. Assumes student has already paid for registration.
                        </p>
                      </div>
                      <div className="mt-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={enrollmentForm.students[enrollmentForm.currentStudentIndex]?.send_onboarding_email || false}
                            onChange={(e) => handleStudentFieldChange('send_onboarding_email', e.target.checked)}
                            className="w-4 h-4 rounded border-och-steel/30 bg-och-midnight text-och-defender focus:ring-och-defender"
                          />
                          <span className="text-sm text-white">
                            Send onboarding email (leave blank to send later)
                          </span>
                        </label>
                        <p className="text-xs text-och-steel mt-1 ml-6">
                          If checked, an onboarding email will be sent immediately after enrollment.
                        </p>
                      </div>
                      <div className="flex gap-2 pt-4">
                        {enrollmentForm.currentStudentIndex > 0 && (
                          <Button
                            variant="outline"
                            onClick={() => setEnrollmentForm(prev => ({
                              ...prev,
                              currentStudentIndex: prev.currentStudentIndex - 1,
                            }))}
                          >
                            Previous
                          </Button>
                        )}
                        {enrollmentForm.isFromOrganization && enrollmentForm.currentStudentIndex === 0 && (
                          <Button
                            variant="outline"
                            onClick={() => setEnrollmentForm(prev => ({ ...prev, step: 'orgDetails' }))}
                          >
                            Back
                          </Button>
                        )}
                        {!enrollmentForm.isFromOrganization && enrollmentForm.currentStudentIndex === 0 && (
                          <Button
                            variant="outline"
                            onClick={() => setEnrollmentForm(prev => ({ ...prev, step: 'organization' }))}
                          >
                            Back
                          </Button>
                        )}
                        <Button
                          variant="defender"
                          onClick={handleNextStudent}
                          disabled={isSubmitting}
                        >
                          {isSubmitting 
                            ? 'Enrolling...' 
                            : enrollmentForm.currentStudentIndex === enrollmentForm.students.length - 1
                              ? `Complete (${enrollmentForm.currentStudentIndex + 1}/${enrollmentForm.students.length})`
                              : `Next & Enroll (${enrollmentForm.currentStudentIndex + 1}/${enrollmentForm.students.length})`}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}

          {/* Student Details Modal — two columns: Student Details (left) + Organization full details (right) */}
          {showStudentDetailsModal && selectedStudentDetails && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-5xl max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-white">View Details</h2>
                    <button
                      onClick={() => {
                        setShowStudentDetailsModal(false)
                        setSelectedStudentDetails(null)
                      }}
                      className="text-och-steel hover:text-white"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Left: Student Details */}
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-white border-b border-och-steel/20 pb-2">Student Details</h3>
                      <div>
                        <h4 className="text-sm font-medium text-och-steel mb-3">Basic Information</h4>
                        <div className="space-y-3">
                          <div>
                            <label className="text-xs text-och-steel">Name</label>
                            <p className="text-white">{selectedStudentDetails.user_name || 'N/A'}</p>
                          </div>
                          <div>
                            <label className="text-xs text-och-steel">Email</label>
                            <p className="text-white">{selectedStudentDetails.user_email || 'N/A'}</p>
                          </div>
                          <div>
                            <label className="text-xs text-och-steel">Organization</label>
                            <p className="text-white">{selectedStudentDetails.organization_name || 'N/A'}</p>
                          </div>
                          <div>
                            <label className="text-xs text-och-steel">Enrollment Type</label>
                            <p>
                              <Badge variant="outline">
                                {ENROLLMENT_TYPE_LABELS[selectedStudentDetails.enrollment_type] || selectedStudentDetails.enrollment_type}
                              </Badge>
                            </p>
                          </div>
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-och-steel mb-3">Cohorts</h4>
                        {selectedStudentDetails.cohorts && selectedStudentDetails.cohorts.length > 0 ? (
                          <div className="space-y-2">
                            {selectedStudentDetails.cohorts.map((cohort) => (
                              <div key={cohort.id} className="p-3 bg-och-midnight/50 rounded-lg border border-och-steel/20">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-white font-medium">{cohort.name}</p>
                                    <p className="text-sm text-och-steel">Track: {cohort.track_name || 'N/A'}</p>
                                  </div>
                                  <Badge variant={cohort.status === 'active' ? 'mint' : 'outline'}>
                                    {cohort.status}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-och-steel">No cohorts assigned</p>
                        )}
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-och-steel mb-3">Tracks</h4>
                        {selectedStudentDetails.cohorts && selectedStudentDetails.cohorts.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {[...new Set(selectedStudentDetails.cohorts.map(c => c.track_name).filter(Boolean))].map((trackName) => (
                              <Badge key={trackName} variant="outline">
                                {trackName}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <p className="text-och-steel">No tracks assigned</p>
                        )}
                      </div>
                    </div>

                    {/* Right: Organization full details */}
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-white border-b border-och-steel/20 pb-2">Organization Details</h3>
                      {selectedStudentDetails.organization_id ? (
                        selectedOrganizationDetails ? (
                          <div className="space-y-4">
                            <div>
                              <label className="text-xs text-och-steel">Name</label>
                              <p className="text-white font-medium">{selectedOrganizationDetails.name ?? '—'}</p>
                            </div>
                            {selectedOrganizationDetails.slug != null && (
                              <div>
                                <label className="text-xs text-och-steel">Slug</label>
                                <p className="text-white">{selectedOrganizationDetails.slug}</p>
                              </div>
                            )}
                            {selectedOrganizationDetails.org_type != null && (
                              <div>
                                <label className="text-xs text-och-steel">Type</label>
                                <p className="text-white capitalize">{selectedOrganizationDetails.org_type}</p>
                              </div>
                            )}
                            {selectedOrganizationDetails.status != null && (
                              <div>
                                <label className="text-xs text-och-steel">Status</label>
                                <p className="text-white capitalize">{selectedOrganizationDetails.status}</p>
                              </div>
                            )}
                            {selectedOrganizationDetails.description != null && selectedOrganizationDetails.description !== '' && (
                              <div>
                                <label className="text-xs text-och-steel">Description</label>
                                <p className="text-white text-sm">{selectedOrganizationDetails.description}</p>
                              </div>
                            )}
                            {selectedOrganizationDetails.website != null && selectedOrganizationDetails.website !== '' && (
                              <div>
                                <label className="text-xs text-och-steel">Website</label>
                                <p className="text-white text-sm break-all">{selectedOrganizationDetails.website}</p>
                              </div>
                            )}
                            {selectedOrganizationDetails.country != null && selectedOrganizationDetails.country !== '' && (
                              <div>
                                <label className="text-xs text-och-steel">Country</label>
                                <p className="text-white">{selectedOrganizationDetails.country}</p>
                              </div>
                            )}
                            <div>
                              <h4 className="text-sm font-medium text-och-steel mb-2">Contact (billing)</h4>
                              <div className="space-y-2 pl-0">
                                <div>
                                  <label className="text-xs text-och-steel">Contact person</label>
                                  <p className="text-white">{selectedOrganizationDetails.contact_person_name ?? '—'}</p>
                                </div>
                                <div>
                                  <label className="text-xs text-och-steel">Contact email</label>
                                  <p className="text-white">{selectedOrganizationDetails.contact_email ?? '—'}</p>
                                </div>
                                <div>
                                  <label className="text-xs text-och-steel">Contact phone</label>
                                  <p className="text-white">{selectedOrganizationDetails.contact_phone ?? '—'}</p>
                                </div>
                              </div>
                            </div>
                            {selectedOrganizationDetails.member_count != null && (
                              <div>
                                <label className="text-xs text-och-steel">Members</label>
                                <p className="text-white">{selectedOrganizationDetails.member_count}</p>
                              </div>
                            )}
                            {(selectedOrganizationDetails.created_at != null || selectedOrganizationDetails.updated_at != null) && (
                              <div className="pt-2 border-t border-och-steel/20 text-xs text-och-steel">
                                {selectedOrganizationDetails.created_at && (
                                  <p>Created: {new Date(selectedOrganizationDetails.created_at).toLocaleDateString()}</p>
                                )}
                                {selectedOrganizationDetails.updated_at && (
                                  <p>Updated: {new Date(selectedOrganizationDetails.updated_at).toLocaleDateString()}</p>
                                )}
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-och-steel">Loading organization…</p>
                        )
                      ) : (
                        <p className="text-och-steel">No organization linked</p>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Change Track Modal */}
          {showChangeTrackModal && studentForAction && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-md">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Change Track</h3>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-white mb-2">Select New Track</label>
                    <select
                      value={selectedTrackSlug}
                      onChange={(e) => setSelectedTrackSlug(e.target.value)}
                      className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                    >
                      <option value="">Select track</option>
                      {curriculumTracks.map((track) => (
                        <option key={track.slug} value={track.slug}>
                          {track.title || track.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex gap-2 justify-end">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowChangeTrackModal(false)
                        setStudentForAction(null)
                        setSelectedTrackSlug('')
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="defender"
                      onClick={handleChangeTrack}
                      disabled={!selectedTrackSlug}
                    >
                      Change Track
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Delete Confirmation Modal */}
          {showDeleteModal && studentForAction && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-md">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">⚠️ Delete Student Permanently</h3>
                  <p className="text-och-steel mb-4">
                    Are you sure you want to <span className="text-och-orange font-bold">permanently delete</span> <span className="text-white font-medium">{studentForAction.user_name || studentForAction.user_email}</span>?
                  </p>
                  <div className="mb-6 p-3 bg-och-orange/10 border border-och-orange/30 rounded-lg">
                    <p className="text-och-orange text-sm font-medium mb-2">This will completely erase:</p>
                    <ul className="text-och-steel text-sm space-y-1 list-disc list-inside">
                      <li>User account and profile</li>
                      <li>All enrollments and cohort data</li>
                      <li>All progress and submissions</li>
                      <li>All related records</li>
                    </ul>
                    <p className="text-och-orange text-sm font-bold mt-3">This action CANNOT be undone!</p>
                  </div>
                  <div className="flex gap-2 justify-end">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowDeleteModal(false)
                        setStudentForAction(null)
                      }}
                      disabled={isDeleting}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleDeleteStudent}
                      disabled={isDeleting}
                      className="bg-och-orange/20 text-och-orange border-och-orange/50 hover:bg-och-orange/30"
                    >
                      {isDeleting ? 'Deleting...' : 'Delete Permanently'}
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Bulk Delete Confirmation Modal */}
          {showBulkDeleteModal && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-md">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">⚠️ Delete Selected Students Permanently</h3>
                  <p className="text-och-steel mb-4">
                    Are you sure you want to <span className="text-och-orange font-bold">permanently delete</span> <span className="text-white font-medium">{selectedStudents.size} student(s)</span>?
                  </p>
                  <div className="mb-6 p-3 bg-och-orange/10 border border-och-orange/30 rounded-lg">
                    <p className="text-och-orange text-sm font-medium mb-2">This will completely erase:</p>
                    <ul className="text-och-steel text-sm space-y-1 list-disc list-inside">
                      <li>User accounts and profiles</li>
                      <li>All enrollments and cohort data</li>
                      <li>All progress and submissions</li>
                      <li>All related records</li>
                    </ul>
                    <p className="text-och-orange text-sm font-bold mt-3">This action CANNOT be undone!</p>
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-white mb-2">
                      Type <span className="font-mono font-bold text-och-orange">DELETE</span> to confirm:
                    </label>
                    <Input
                      type="text"
                      value={bulkDeleteConfirmText}
                      onChange={(e) => setBulkDeleteConfirmText(e.target.value)}
                      placeholder="Type DELETE here"
                      className="font-mono"
                    />
                  </div>
                  <div className="flex gap-2 justify-end">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowBulkDeleteModal(false)
                        setBulkDeleteConfirmText('')
                      }}
                      disabled={isDeleting}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleBulkDelete}
                      disabled={isDeleting || bulkDeleteConfirmText !== 'DELETE'}
                      className="bg-och-orange/20 text-och-orange border-och-orange/50 hover:bg-och-orange/30 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isDeleting ? 'Deleting...' : `Delete ${selectedStudents.size} Student(s) Permanently`}
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Edit Student Modal */}
          {showEditModal && studentForAction && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-white">Edit Student</h2>
                    <button
                      onClick={() => {
                        setShowEditModal(false)
                        setStudentForAction(null)
                        setEditFormData({
                          first_name: '',
                          last_name: '',
                          email: '',
                          phone_number: '',
                          country: '',
                          organization_id: '',
                        })
                      }}
                      className="text-och-steel hover:text-white"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        First Name *
                      </label>
                      <Input
                        type="text"
                        value={editFormData.first_name}
                        onChange={(e) => setEditFormData({ ...editFormData, first_name: e.target.value })}
                        placeholder="John"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Last Name *
                      </label>
                      <Input
                        type="text"
                        value={editFormData.last_name}
                        onChange={(e) => setEditFormData({ ...editFormData, last_name: e.target.value })}
                        placeholder="Doe"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Email Address *
                      </label>
                      <Input
                        type="email"
                        value={editFormData.email}
                        onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
                        placeholder="your.email@example.com"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Phone Number
                      </label>
                      <Input
                        type="tel"
                        value={editFormData.phone_number}
                        onChange={(e) => setEditFormData({ ...editFormData, phone_number: e.target.value })}
                        placeholder="+1234567890"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Country (2-letter code)
                      </label>
                      <Input
                        type="text"
                        value={editFormData.country}
                        onChange={(e) => setEditFormData({ ...editFormData, country: e.target.value.toUpperCase().slice(0, 2) })}
                        placeholder="KE"
                        maxLength={2}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Organization
                      </label>
                      <select
                        value={editFormData.organization_id}
                        onChange={(e) => setEditFormData({ ...editFormData, organization_id: e.target.value })}
                        className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                      >
                        <option value="">No Organization</option>
                        {organizations.map((org) => (
                          <option key={org.id} value={org.id}>
                            {org.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="flex gap-2 pt-4">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowEditModal(false)
                          setStudentForAction(null)
                          setEditFormData({
                            first_name: '',
                            last_name: '',
                            email: '',
                            phone_number: '',
                            country: '',
                            organization_id: '',
                          })
                        }}
                      >
                        Cancel
                      </Button>
                      <Button
                        variant="defender"
                        onClick={handleEditStudent}
                        disabled={!editFormData.first_name || !editFormData.last_name || !editFormData.email}
                      >
                        Save Changes
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Report Generation Modal */}
          {showReportModal && studentForAction && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-md">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Generate Progress Report</h3>
                  <p className="text-och-steel mb-6">
                    Generate a comprehensive progress report for <span className="text-white font-medium">{studentForAction.user_name || studentForAction.user_email}</span>. The report will include curriculum progress, track completion, missions, and other metrics.
                  </p>
                  <div className="flex gap-2 justify-end">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowReportModal(false)
                        setStudentForAction(null)
                      }}
                      disabled={isGeneratingReport}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="defender"
                      onClick={handleGenerateReport}
                      disabled={isGeneratingReport}
                    >
                      {isGeneratingReport ? 'Generating...' : 'Generate PDF Report'}
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
    </RouteGuard>
  )
}
