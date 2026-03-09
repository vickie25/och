'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { MilestoneResponse } from '@/types/api'
import { apiGateway } from '@/services/apiGateway'
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
  Tooltip,
} from '@mui/material'
import {
  MoreVert,
  Edit,
  Delete,
  Visibility,
  Refresh,
  Add,
} from '@mui/icons-material'

export default function MilestonesPage() {
  const router = useRouter()
  const [milestones, setMilestones] = useState<MilestoneResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [selectedMilestone, setSelectedMilestone] = useState<MilestoneResponse | null>(null)
  const [milestoneToDelete, setMilestoneToDelete] = useState<MilestoneResponse | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchMilestones()
  }, [])

  const fetchMilestones = async () => {
    try {
      setLoading(true)
      const data = await apiGateway.get('/milestones/') as any
      setMilestones(data?.results || data?.data || data || [])
    } catch (error) {
      console.error('Failed to fetch milestones:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, milestone: MilestoneResponse) => {
    setAnchorEl(event.currentTarget)
    setSelectedMilestone(milestone)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedMilestone(null)
  }

  const handleDeleteClick = () => {
    setMilestoneToDelete(selectedMilestone)
    setDeleteDialogOpen(true)
    handleMenuClose()
  }

  const handleDeleteConfirm = async () => {
    if (!milestoneToDelete) return
    setDeleting(true)
    try {
      await apiGateway.delete(`/milestones/${milestoneToDelete.id}/`)
      await fetchMilestones()
      setDeleteDialogOpen(false)
      setMilestoneToDelete(null)
    } catch (err: any) {
      alert(err?.message || 'Failed to delete milestone.')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false)
    setMilestoneToDelete(null)
  }

  const filteredMilestones = useMemo(() => {
    return milestones.filter((milestone) => {
      if (searchQuery && 
          !milestone.name?.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !milestone.description?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      return true
    })
  }, [milestones, searchQuery])

  const kpis = useMemo(() => {
    const total = milestones.length
    const avgDuration = milestones.length > 0 
      ? Math.round(milestones.reduce((sum, m) => sum + (m.duration_weeks || 0), 0) / milestones.length)
      : 0
    const withModules = milestones.filter(m => m.modules && m.modules.length > 0).length
    const avgModules = milestones.length > 0
      ? Math.round(milestones.reduce((sum, m) => sum + (m.modules?.length || 0), 0) / milestones.length)
      : 0
    
    return { total, avgDuration, withModules, avgModules }
  }, [milestones])

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold mb-2 text-white">Milestones</h1>
            <p className="text-och-steel">Manage major checkpoints and learning milestones</p>
          </div>
          <Button variant="defender" size="sm" className="gap-2">
            <Add className="w-4 h-4" />
            Create Milestone
          </Button>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <Card className="bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">Total Milestones</p>
              <p className="text-3xl font-bold text-white">{kpis.total}</p>
            </div>
          </Card>
          <Card className="bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">With Modules</p>
              <p className="text-3xl font-bold text-och-mint">{kpis.withModules}</p>
            </div>
          </Card>
          <Card className="bg-gradient-to-br from-och-orange/20 to-och-orange/5 border-och-orange/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">Avg Duration</p>
              <p className="text-3xl font-bold text-och-orange">{kpis.avgDuration}w</p>
            </div>
          </Card>
          <Card className="bg-gradient-to-br from-och-gold/20 to-och-gold/5 border-och-gold/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">Avg Modules</p>
              <p className="text-3xl font-bold text-och-gold">{kpis.avgModules}</p>
            </div>
          </Card>
        </div>

        {/* Search */}
        <Card className="border-och-steel/20 bg-gradient-to-r from-och-midnight/50 to-och-midnight/30">
          <div className="p-4">
            <label className="block text-sm font-medium text-white mb-2">Search Milestones</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or description..."
              className="w-full px-4 py-2.5 bg-och-midnight/70 border border-och-steel/30 rounded-lg text-white placeholder-och-steel/50 focus:outline-none focus:border-och-defender focus:ring-2 focus:ring-och-defender/20"
            />
          </div>
        </Card>
      </div>

      <Card>
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
            <CircularProgress sx={{ color: '#00D9FF' }} />
          </Box>
        ) : filteredMilestones.length === 0 ? (
          <Box p={6} textAlign="center">
            <Typography variant="h6" color="#8B9DAF" mb={2}>
              No milestones found
            </Typography>
            <Button variant="defender">Create Your First Milestone</Button>
          </Box>
        ) : (
          <TableContainer component={Paper} sx={{ backgroundColor: 'transparent', boxShadow: 'none' }}>
            <Table sx={{ border: '1px solid rgba(139, 157, 175, 0.2)' }}>
              <TableHead>
                <TableRow sx={{ borderBottom: '2px solid rgba(139, 157, 175, 0.3)', backgroundColor: 'rgba(0, 217, 255, 0.05)' }}>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>#</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Milestone Name</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Track</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Order</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Duration</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Modules</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }} align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredMilestones.map((milestone: MilestoneResponse, index: number) => (
                  <TableRow
                    key={milestone.id}
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
                        <div className="font-semibold">{milestone.name}</div>
                        <Tooltip title={milestone.description || ''} arrow>
                          <div className="text-sm text-och-steel line-clamp-1 hover:line-clamp-none cursor-help">
                            {milestone.description}
                          </div>
                        </Tooltip>
                      </div>
                    </TableCell>
                    <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <div>
                        <div className="text-sm text-och-mint">{milestone.track?.name}</div>
                        <div className="text-xs text-och-steel">{milestone.track?.program?.name}</div>
                      </div>
                    </TableCell>
                    <TableCell sx={{ color: '#8B9DAF', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <Badge variant="outline" className="text-xs">
                        #{milestone.order}
                      </Badge>
                    </TableCell>
                    <TableCell sx={{ color: '#8B9DAF', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      {milestone.duration_weeks ? `${milestone.duration_weeks} weeks` : 'N/A'}
                    </TableCell>
                    <TableCell sx={{ color: '#8B9DAF', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      {milestone.modules?.length || 0}
                    </TableCell>
                    <TableCell align="right" sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <IconButton
                        onClick={(e) => handleMenuOpen(e, milestone)}
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
            // View action
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
            // Edit action
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
            fetchMilestones()
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
            Are you sure you want to delete "{milestoneToDelete?.name}"? This will also delete all modules linked to this milestone. This action cannot be undone.
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
  )
}
