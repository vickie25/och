'use client'

import { useState, useMemo } from 'react'
import { usePrograms, useDeleteProgram } from '@/hooks/usePrograms'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
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
  Refresh,
  BarChart,
  Add,
} from '@mui/icons-material'

export default function ProgramsPage() {
  const { programs, isLoading, reload } = usePrograms()
  const { deleteProgram, isLoading: isDeleting } = useDeleteProgram()
  const router = useRouter()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [selectedProgram, setSelectedProgram] = useState<any>(null)
  const [programToDelete, setProgramToDelete] = useState<any>(null)
  const [filterCategory, setFilterCategory] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, program: any) => {
    setAnchorEl(event.currentTarget)
    setSelectedProgram(program)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedProgram(null)
  }

  const handleDeleteClick = () => {
    setProgramToDelete(selectedProgram)
    setDeleteDialogOpen(true)
    handleMenuClose()
  }

  const handleDeleteConfirm = async () => {
    if (!programToDelete) return
    try {
      await deleteProgram(programToDelete.id)
      await reload()
      setDeleteDialogOpen(false)
      setProgramToDelete(null)
    } catch (err) {
      console.error('Failed to delete program:', err)
      alert('Failed to delete program. Please try again.')
    }
  }

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false)
    setProgramToDelete(null)
  }

  const filteredPrograms = useMemo(() => {
    return programs.filter((program) => {
      if (filterCategory !== 'all' && program.category !== filterCategory) return false
      if (filterStatus !== 'all' && program.status !== filterStatus) return false
      if (searchQuery && !program.name.toLowerCase().includes(searchQuery.toLowerCase()) && 
          !program.description?.toLowerCase().includes(searchQuery.toLowerCase())) return false
      return true
    })
  }, [programs, filterCategory, filterStatus, searchQuery])

  const kpis = useMemo(() => {
    const total = programs.length
    const active = programs.filter(p => p.status === 'active').length
    const inactive = programs.filter(p => p.status === 'inactive').length
    const archived = programs.filter(p => p.status === 'archived').length
    const avgDuration = programs.length > 0 
      ? Math.round(programs.reduce((sum, p) => sum + (p.duration_months || 0), 0) / programs.length)
      : 0
    
    return { total, active, inactive, archived, avgDuration }
  }, [programs])

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold mb-2 text-white">Programs Management</h1>
            <p className="text-och-steel">Manage your learning programs, tracks, and cohorts</p>
          </div>
          <Link href="/dashboard/director/programs/new">
            <Button variant="defender" size="sm" className="gap-2">
              <Add className="w-4 h-4" />
              Create Program
            </Button>
          </Link>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <Card className="bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">Total Programs</p>
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
              <p className="text-och-steel text-sm mb-1">Inactive</p>
              <p className="text-3xl font-bold text-och-orange">{kpis.inactive}</p>
            </div>
          </Card>
          <Card className="bg-gradient-to-br from-och-steel/20 to-och-steel/5 border-och-steel/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">Archived</p>
              <p className="text-3xl font-bold text-och-steel">{kpis.archived}</p>
            </div>
          </Card>
          <Card className="bg-gradient-to-br from-och-gold/20 to-och-gold/5 border-och-gold/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">Avg Duration</p>
              <p className="text-3xl font-bold text-och-gold">{kpis.avgDuration}mo</p>
            </div>
          </Card>
        </div>

        {/* Filters */}
        <Card className="border-och-steel/20 bg-gradient-to-r from-och-midnight/50 to-och-midnight/30">
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Search Programs</label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by name or description..."
                  className="w-full px-4 py-2.5 bg-och-midnight/70 border border-och-steel/30 rounded-lg text-white placeholder-och-steel/50 focus:outline-none focus:border-och-defender focus:ring-2 focus:ring-och-defender/20"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Category</label>
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="w-full px-4 py-2.5 bg-och-midnight/70 border border-och-steel/30 rounded-lg text-white focus:outline-none focus:border-och-defender focus:ring-2 focus:ring-och-defender/20"
                >
                  <option value="all">All Categories</option>
                  <option value="technical">Technical</option>
                  <option value="leadership">Leadership</option>
                  <option value="mentorship">Mentorship</option>
                  <option value="executive">Executive</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Status</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full px-4 py-2.5 bg-och-midnight/70 border border-och-steel/30 rounded-lg text-white focus:outline-none focus:border-och-defender focus:ring-2 focus:ring-och-defender/20"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        {isLoading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
            <CircularProgress sx={{ color: '#00D9FF' }} />
          </Box>
        ) : filteredPrograms.length === 0 ? (
          <Box p={6} textAlign="center">
            <Typography variant="h6" color="#8B9DAF" mb={2}>
              No programs found
            </Typography>
            <Link href="/dashboard/director/programs/new">
              <Button variant="defender">Create Your First Program</Button>
            </Link>
          </Box>
        ) : (
          <TableContainer component={Paper} sx={{ backgroundColor: 'transparent', boxShadow: 'none' }}>
            <Table sx={{ border: '1px solid rgba(139, 157, 175, 0.2)' }}>
              <TableHead>
                <TableRow sx={{ borderBottom: '2px solid rgba(139, 157, 175, 0.3)', backgroundColor: 'rgba(0, 217, 255, 0.05)' }}>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>#</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Program Name</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Category</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Status</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Duration</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Price</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }} align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPrograms.map((program: any, index: number) => (
                  <TableRow
                    key={program.id}
                    sx={{
                      '&:hover': { backgroundColor: 'rgba(0, 217, 255, 0.05)' },
                      borderBottom: '1px solid rgba(139, 157, 175, 0.1)',
                    }}
                  >
                    <TableCell sx={{ color: '#8B9DAF', fontWeight: 600, border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      {index + 1}
                    </TableCell>
                    <TableCell sx={{ color: '#fff', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <div>
                        <div className="font-semibold">{program.name}</div>
                        <div className="text-sm text-och-steel line-clamp-1">{program.description}</div>
                      </div>
                    </TableCell>
                    <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <Badge variant="outline" className="text-xs">
                        {program.category || 'General'}
                      </Badge>
                    </TableCell>
                    <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <Badge
                        variant={program.status === 'active' ? 'defender' : program.status === 'archived' ? 'steel' : 'outline'}
                        className="text-xs"
                      >
                        {program.status || 'active'}
                      </Badge>
                    </TableCell>
                    <TableCell sx={{ color: '#8B9DAF', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      {program.duration_months ? `${program.duration_months} months` : 'N/A'}
                    </TableCell>
                    <TableCell sx={{ color: '#8B9DAF', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      {program.currency} {program.default_price || 0}
                    </TableCell>
                    <TableCell align="right" sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <IconButton
                        onClick={(e) => handleMenuOpen(e, program)}
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
            router.push(`/dashboard/director/programs/${selectedProgram?.id}`)
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
            router.push(`/dashboard/director/programs/${selectedProgram?.id}/edit`)
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
          onClick={() => {
            reload()
            handleMenuClose()
          }}
          sx={{ color: '#8B9DAF', '&:hover': { backgroundColor: 'rgba(0, 217, 255, 0.1)', color: '#00D9FF' } }}
        >
          <ListItemIcon>
            <Refresh sx={{ color: '#8B9DAF' }} fontSize="small" />
          </ListItemIcon>
          <ListItemText>Refresh</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            router.push(`/dashboard/director/programs/${selectedProgram?.id}/analytics`)
            handleMenuClose()
          }}
          sx={{ color: '#8B9DAF', '&:hover': { backgroundColor: 'rgba(0, 217, 255, 0.1)', color: '#00D9FF' } }}
        >
          <ListItemIcon>
            <BarChart sx={{ color: '#8B9DAF' }} fontSize="small" />
          </ListItemIcon>
          <ListItemText>Analytics</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={handleDeleteClick}
          disabled={isDeleting}
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
            Are you sure you want to delete "{programToDelete?.name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ padding: '16px 24px' }}>
          <Button
            onClick={handleDeleteCancel}
            variant="outline"
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="orange"
            disabled={isDeleting}
            className="bg-och-orange hover:bg-och-orange/90"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}
