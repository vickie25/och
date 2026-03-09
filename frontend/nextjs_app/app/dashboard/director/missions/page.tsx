'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { missionsClient } from '@/services/missionsClient'
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
  Star,
  StarBorder,
} from '@mui/icons-material'

interface Mission {
  id: string
  title: string
  description: string
  difficulty: number
  mission_type: string
  estimated_duration_min: number
  is_active: boolean
  created_at: string
  track?: string
}

function normalizeMission(m: Record<string, unknown>): Mission {
  return {
    id: String(m.id ?? ''),
    title: String(m.title ?? m.code ?? ''),
    description: String(m.description ?? ''),
    difficulty: typeof m.difficulty === 'number' ? m.difficulty : (m.difficulty === 'advanced' ? 3 : m.difficulty === 'intermediate' ? 2 : 1),
    mission_type: String(m.mission_type ?? m.type ?? 'lab'),
    estimated_duration_min: Number(m.estimated_duration_min ?? m.estimated_time_minutes ?? 0),
    is_active: (m.status === 'published' || m.status === 'active' || m.is_active) === true,
    created_at: String(m.created_at ?? ''),
    track: m.track ? String(m.track) : undefined,
  }
}

export default function MissionsPage() {
  const router = useRouter()
  const [missions, setMissions] = useState<Mission[]>([])
  const [loading, setLoading] = useState(true)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [selectedMission, setSelectedMission] = useState<Mission | null>(null)
  const [missionToDelete, setMissionToDelete] = useState<Mission | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchMissions()
  }, [])

  const fetchMissions = async () => {
    try {
      setLoading(true)
      const { results } = await missionsClient.getAllMissionsAdmin()
      setMissions((results as Record<string, unknown>[]).map(normalizeMission))
    } catch (err) {
      console.error('Failed to fetch missions:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, mission: Mission) => {
    setAnchorEl(event.currentTarget)
    setSelectedMission(mission)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedMission(null)
  }

  const handleDeleteClick = () => {
    setMissionToDelete(selectedMission)
    setDeleteDialogOpen(true)
    handleMenuClose()
  }

  const handleDeleteConfirm = async () => {
    if (!missionToDelete) return
    setDeleting(true)
    try {
      await missionsClient.deleteMission(missionToDelete.id)
      await fetchMissions()
      setDeleteDialogOpen(false)
      setMissionToDelete(null)
    } catch (err: any) {
      alert(err?.message || 'Failed to delete mission.')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false)
    setMissionToDelete(null)
  }

  const filteredMissions = useMemo(() => {
    return missions.filter((mission) => {
      if (searchQuery && 
          !mission.title?.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !mission.description?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      return true
    })
  }, [missions, searchQuery])

  const kpis = useMemo(() => {
    const total = missions.length
    const active = missions.filter(m => m.is_active).length
    const inactive = missions.filter(m => !m.is_active).length
    const avgDuration = missions.length > 0 
      ? Math.round(missions.reduce((sum, m) => sum + (m.estimated_duration_min || 0), 0) / missions.length)
      : 0
    
    return { total, active, inactive, avgDuration }
  }, [missions])

  const renderDifficulty = (difficulty: number) => {
    return (
      <Box display="flex" gap={0.5}>
        {[1, 2, 3, 4, 5].map((level) => (
          level <= difficulty ? (
            <Star key={level} sx={{ fontSize: 16, color: '#FFD700' }} />
          ) : (
            <StarBorder key={level} sx={{ fontSize: 16, color: '#8B9DAF' }} />
          )
        ))}
      </Box>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold mb-2 text-white">Missions</h1>
            <p className="text-och-steel">Manage curriculum missions</p>
          </div>
          <Link href="/dashboard/director/missions/new">
            <Button variant="defender" size="sm" className="gap-2">
              <Add className="w-4 h-4" />
              Create Mission
            </Button>
          </Link>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <Card className="bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">Total Missions</p>
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
          <Card className="bg-gradient-to-br from-och-gold/20 to-och-gold/5 border-och-gold/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">Avg Duration</p>
              <p className="text-3xl font-bold text-och-gold">{kpis.avgDuration}min</p>
            </div>
          </Card>
        </div>

        {/* Search */}
        <Card className="border-och-steel/20 bg-gradient-to-r from-och-midnight/50 to-och-midnight/30">
          <div className="p-4">
            <label className="block text-sm font-medium text-white mb-2">Search Missions</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title or description..."
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
        ) : filteredMissions.length === 0 ? (
          <Box p={6} textAlign="center">
            <Typography variant="h6" color="#8B9DAF" mb={2}>
              No missions found
            </Typography>
            <Link href="/dashboard/director/missions/new">
              <Button variant="defender">Create Your First Mission</Button>
            </Link>
          </Box>
        ) : (
          <TableContainer component={Paper} sx={{ backgroundColor: 'transparent', boxShadow: 'none' }}>
            <Table sx={{ border: '1px solid rgba(139, 157, 175, 0.2)' }}>
              <TableHead>
                <TableRow sx={{ borderBottom: '2px solid rgba(139, 157, 175, 0.3)', backgroundColor: 'rgba(0, 217, 255, 0.05)' }}>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>#</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Mission Title</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Type</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Difficulty</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Duration</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Status</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }} align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredMissions.map((mission: Mission, index: number) => (
                  <TableRow
                    key={mission.id}
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
                        <div className="font-semibold">{mission.title}</div>
                        <Tooltip title={mission.description} arrow>
                          <div className="text-sm text-och-steel line-clamp-1 hover:line-clamp-none cursor-help">
                            {mission.description}
                          </div>
                        </Tooltip>
                      </div>
                    </TableCell>
                    <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <Badge variant="outline" className="text-xs">
                        {mission.mission_type}
                      </Badge>
                    </TableCell>
                    <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      {renderDifficulty(mission.difficulty)}
                    </TableCell>
                    <TableCell sx={{ color: '#8B9DAF', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      {mission.estimated_duration_min} min
                    </TableCell>
                    <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <Badge
                        variant={mission.is_active ? 'defender' : 'steel'}
                        className="text-xs"
                      >
                        {mission.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell align="right" sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <IconButton
                        onClick={(e) => handleMenuOpen(e, mission)}
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
            router.push(`/dashboard/director/missions/${selectedMission?.id}`)
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
            router.push(`/dashboard/director/missions/${selectedMission?.id}/edit`)
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
            fetchMissions()
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
            Are you sure you want to delete "{missionToDelete?.title}"? This action cannot be undone.
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
