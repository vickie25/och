'use client'

import { useState, useEffect, useMemo } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { CohortResponse } from '@/types/api'
import { apiGateway } from '@/services/apiGateway'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Box,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
} from '@mui/material'
import {
  MoreVert,
  Edit,
  Delete,
  Visibility,
  Add,
} from '@mui/icons-material'

export default function CohortsPage() {
  const [cohorts, setCohorts] = useState<CohortResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [selectedCohort, setSelectedCohort] = useState<CohortResponse | null>(null)
  const [cohortToDelete, setCohortToDelete] = useState<CohortResponse | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const router = useRouter()

  useEffect(() => {
    fetchCohorts()
  }, [])

  const fetchCohorts = async () => {
    try {
      setIsLoading(true)
      const data = await apiGateway.get('/cohorts/') as any
      setCohorts(data?.results || data?.data || data || [])
    } catch (error) {
      console.error('Failed to fetch cohorts:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, cohort: CohortResponse) => {
    setAnchorEl(event.currentTarget)
    setSelectedCohort(cohort)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedCohort(null)
  }

  const handleDeleteClick = () => {
    setCohortToDelete(selectedCohort)
    setDeleteDialogOpen(true)
    handleMenuClose()
  }

  const handleDeleteConfirm = async () => {
    if (!cohortToDelete) return
    setDeleting(true)
    try {
      await apiGateway.delete(`/cohorts/${cohortToDelete.id}/`)
      await fetchCohorts()
      setDeleteDialogOpen(false)
      setCohortToDelete(null)
    } catch (err: any) {
      alert(err?.message || 'Failed to delete cohort.')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false)
    setCohortToDelete(null)
  }

  const filteredCohorts = useMemo(() => {
    return cohorts.filter((cohort) => {
      if (searchQuery && 
          !cohort.name?.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !cohort.track?.name?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      return true
    })
  }, [cohorts, searchQuery])

  const kpis = useMemo(() => {
    const total = cohorts.length
    const active = cohorts.filter(c => c.status === 'active').length
    const totalEnrollment = cohorts.reduce((sum, c) => sum + (c.enrollment_count || 0), 0)
    const totalCapacity = cohorts.reduce((sum, c) => sum + (c.seat_cap || 0), 0)
    
    return { total, active, totalEnrollment, totalCapacity }
  }, [cohorts])

  if (isLoading) {
    return (
      <RouteGuard requiredRoles={['program_director', 'admin']}>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-och-defender"></div>
        </div>
      </RouteGuard>
    )
  }

  return (
    <RouteGuard requiredRoles={['program_director', 'admin']}>
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold mb-2 text-white">Cohorts</h1>
              <p className="text-och-steel">Manage cohort instances and enrollment</p>
            </div>
            <Link href="/dashboard/director/cohorts/new">
              <Button variant="defender" size="sm" className="gap-2">
                <Add className="w-4 h-4" />
                Create Cohort
              </Button>
            </Link>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <Card className="bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/30">
              <div className="p-4">
                <p className="text-och-steel text-sm mb-1">Total Cohorts</p>
                <p className="text-3xl font-bold text-white">{kpis.total}</p>
              </div>
            </Card>
            <Card className="bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/30">
              <div className="p-4">
                <p className="text-och-steel text-sm mb-1">Active</p>
                <p className="text-3xl font-bold text-och-mint">{kpis.active}</p>
              </div>
            </Card>
            <Card className="bg-gradient-to-br from-och-orange/20 to-och-orange/5 border-och-orange/30">
              <div className="p-4">
                <p className="text-och-steel text-sm mb-1">Total Enrollment</p>
                <p className="text-3xl font-bold text-och-orange">{kpis.totalEnrollment}</p>
              </div>
            </Card>
            <Card className="bg-gradient-to-br from-och-gold/20 to-och-gold/5 border-och-gold/30">
              <div className="p-4">
                <p className="text-och-steel text-sm mb-1">Total Capacity</p>
                <p className="text-3xl font-bold text-och-gold">{kpis.totalCapacity}</p>
              </div>
            </Card>
          </div>

          {/* Search */}
          <Card className="border-och-steel/20 bg-gradient-to-r from-och-midnight/50 to-och-midnight/30">
            <div className="p-4">
              <label className="block text-sm font-medium text-white mb-2">Search Cohorts</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name or track..."
                className="w-full px-4 py-2.5 bg-och-midnight/70 border border-och-steel/30 rounded-lg text-white placeholder-och-steel/50 focus:outline-none focus:border-och-defender focus:ring-2 focus:ring-och-defender/20"
              />
            </div>
          </Card>
        </div>

        <Card>
          {isLoading ? (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
              <CircularProgress sx={{ color: '#00D9FF' }} />
            </Box>
          ) : filteredCohorts.length === 0 ? (
            <Box p={6} textAlign="center">
              <Typography variant="h6" color="#8B9DAF" mb={2}>
                No cohorts found
              </Typography>
              <Link href="/dashboard/director/cohorts/new">
                <Button variant="defender">Create Your First Cohort</Button>
              </Link>
            </Box>
          ) : (
            <TableContainer component={Paper} sx={{ backgroundColor: 'transparent', boxShadow: 'none' }}>
              <Table sx={{ border: '1px solid rgba(139, 157, 175, 0.2)' }}>
                <TableHead>
                  <TableRow sx={{ borderBottom: '2px solid rgba(139, 157, 175, 0.3)', backgroundColor: 'rgba(0, 217, 255, 0.05)' }}>
                    <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>#</TableCell>
                    <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Cohort Name</TableCell>
                    <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Track</TableCell>
                    <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Start Date</TableCell>
                    <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Enrollment</TableCell>
                    <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Status</TableCell>
                    <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }} align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredCohorts.map((cohort: CohortResponse, index: number) => (
                    <TableRow
                      key={cohort.id}
                      sx={{
                        '&:hover': { backgroundColor: 'rgba(0, 217, 255, 0.05)' },
                        borderBottom: '1px solid rgba(139, 157, 175, 0.1)',
                      }}
                    >
                      <TableCell sx={{ color: '#8B9DAF', fontWeight: 600, border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                        {index + 1}
                      </TableCell>
                      <TableCell sx={{ color: '#fff', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                        <div className="font-semibold">{cohort.name}</div>
                      </TableCell>
                      <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                        <span className="text-och-mint">
                          {cohort.track?.name || cohort.curriculum_tracks?.join(', ') || 'No Track'}
                        </span>
                      </TableCell>
                      <TableCell sx={{ color: '#8B9DAF', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                        {new Date(cohort.start_date).toLocaleDateString()}
                      </TableCell>
                      <TableCell sx={{ color: '#8B9DAF', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                        {cohort.enrollment_count}/{cohort.seat_cap}
                      </TableCell>
                      <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                        <Badge
                          variant={cohort.status === 'active' ? 'defender' : 'steel'}
                          className="text-xs"
                        >
                          {cohort.status}
                        </Badge>
                      </TableCell>
                      <TableCell align="right" sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                        <IconButton
                          onClick={(e) => handleMenuOpen(e, cohort)}
                          sx={{ color: '#8B9DAF', '&:hover': { color: '#00D9FF' } }}
                        >
                          <MoreVert />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Card>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          PaperProps={{
            sx: {
              backgroundColor: '#0A1628',
              border: '1px solid rgba(139, 157, 175, 0.2)',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
              minWidth: 180,
            },
          }}
        >
          <MenuItem
            onClick={() => {
              router.push(`/dashboard/director/cohorts/${selectedCohort?.id}`)
              handleMenuClose()
            }}
            sx={{ color: '#8B9DAF', '&:hover': { backgroundColor: 'rgba(0, 217, 255, 0.1)', color: '#00D9FF' } }}
          >
            <ListItemIcon>
              <Visibility sx={{ color: '#8B9DAF' }} fontSize="small" />
            </ListItemIcon>
            <ListItemText>View</ListItemText>
          </MenuItem>
          <MenuItem
            onClick={() => {
              router.push(`/dashboard/director/cohorts/${selectedCohort?.id}/edit`)
              handleMenuClose()
            }}
            sx={{ color: '#8B9DAF', '&:hover': { backgroundColor: 'rgba(0, 217, 255, 0.1)', color: '#00D9FF' } }}
          >
            <ListItemIcon>
              <Edit sx={{ color: '#8B9DAF' }} fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
          <MenuItem
            onClick={handleDeleteClick}
            disabled={deleting}
            sx={{ color: '#FF6B35', '&:hover': { backgroundColor: 'rgba(255, 107, 53, 0.1)' } }}
          >
            <ListItemIcon>
              <Delete sx={{ color: '#FF6B35' }} fontSize="small" />
            </ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        </Menu>

        <Dialog
          open={deleteDialogOpen}
          onClose={handleDeleteCancel}
          PaperProps={{
            sx: {
              backgroundColor: '#0A1628',
              border: '1px solid rgba(139, 157, 175, 0.2)',
              boxShadow: '0 8px 16px rgba(0, 0, 0, 0.4)',
            },
          }}
        >
          <DialogTitle sx={{ color: '#fff', fontWeight: 600 }}>Confirm Delete</DialogTitle>
          <DialogContent>
            <DialogContentText sx={{ color: '#8B9DAF' }}>
              Are you sure you want to delete "{cohortToDelete?.name}"? This action cannot be undone.
            </DialogContentText>
          </DialogContent>
          <DialogActions sx={{ padding: '16px 24px' }}>
            <Button
              onClick={handleDeleteCancel}
              variant="outline"
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleDeleteConfirm}
              variant="orange"
              disabled={deleting}
              className="bg-och-orange hover:bg-och-orange/90"
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    </RouteGuard>
  )
}