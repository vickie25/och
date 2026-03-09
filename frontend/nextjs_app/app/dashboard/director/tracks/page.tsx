'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
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
} from '@mui/material'
import {
  MoreVert,
  Edit,
  Delete,
  Visibility,
  Refresh,
  Add,
  ViewModule,
} from '@mui/icons-material'

interface CurriculumTrack {
  id: string
  slug: string
  name: string
  title: string
  code: string
  description: string
  level: string
  tier: number
  order_number: number
  thumbnail_url: string
  is_active: boolean
}

export default function DirectorTracksPage() {
  const [tracks, setTracks] = useState<CurriculumTrack[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [selectedTrack, setSelectedTrack] = useState<CurriculumTrack | null>(null)
  const [trackToDelete, setTrackToDelete] = useState<CurriculumTrack | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const router = useRouter()

  const fetchTracks = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await apiGateway.get('/curriculum/tracks/') as any
      const trackList = data?.results || data?.data || data || []
      setTracks(trackList)
    } catch (err) {
      setError('Failed to fetch tracks')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTracks()
  }, [])

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, track: CurriculumTrack) => {
    setAnchorEl(event.currentTarget)
    setSelectedTrack(track)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedTrack(null)
  }

  const handleDeleteClick = () => {
    setTrackToDelete(selectedTrack)
    setDeleteDialogOpen(true)
    handleMenuClose()
  }

  const handleDeleteConfirm = async () => {
    if (!trackToDelete) return
    setDeleting(true)
    try {
      await apiGateway.delete(`/curriculum/tracks/${trackToDelete.slug}/`)
      await fetchTracks()
      setDeleteDialogOpen(false)
      setTrackToDelete(null)
    } catch (err: any) {
      alert(err?.message || 'Failed to delete track. It may have linked progress or enrollments.')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false)
    setTrackToDelete(null)
  }

  const filteredTracks = useMemo(() => {
    return tracks.filter((track) => {
      if (searchQuery && 
          !track.title?.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !track.name?.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !track.description?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      return true
    })
  }, [tracks, searchQuery])

  const kpis = useMemo(() => {
    const total = tracks.length
    const active = tracks.filter(t => t.is_active).length
    const inactive = tracks.filter(t => !t.is_active).length
    const avgTier = tracks.length > 0 
      ? Math.round(tracks.reduce((sum, t) => sum + (t.tier || 0), 0) / tracks.length)
      : 0
    
    return { total, active, inactive, avgTier }
  }, [tracks])

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold mb-2 text-white">Curriculum Tracks</h1>
            <p className="text-och-steel">Manage curriculum tracks and learning paths</p>
          </div>
          <Link href="/dashboard/director/tracks/new">
            <Button variant="defender" size="sm" className="gap-2">
              <Add className="w-4 h-4" />
              Create Track
            </Button>
          </Link>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <Card className="bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/30">
            <div className="p-4">
              <p className="text-och-steel text-sm mb-1">Total Tracks</p>
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
              <p className="text-och-steel text-sm mb-1">Avg Tier</p>
              <p className="text-3xl font-bold text-och-gold">{kpis.avgTier}</p>
            </div>
          </Card>
        </div>

        {/* Search */}
        <Card className="border-och-steel/20 bg-gradient-to-r from-och-midnight/50 to-och-midnight/30">
          <div className="p-4">
            <label className="block text-sm font-medium text-white mb-2">Search Tracks</label>
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
        ) : error ? (
          <Box p={6} textAlign="center">
            <Typography variant="h6" color="#FF6B35" mb={2}>
              {error}
            </Typography>
            <Button onClick={fetchTracks} variant="outline">Retry</Button>
          </Box>
        ) : filteredTracks.length === 0 ? (
          <Box p={6} textAlign="center">
            <Typography variant="h6" color="#8B9DAF" mb={2}>
              No tracks found
            </Typography>
            <Link href="/dashboard/director/tracks/new">
              <Button variant="defender">Create Your First Track</Button>
            </Link>
          </Box>
        ) : (
          <TableContainer component={Paper} sx={{ backgroundColor: 'transparent', boxShadow: 'none' }}>
            <Table sx={{ border: '1px solid rgba(139, 157, 175, 0.2)' }}>
              <TableHead>
                <TableRow sx={{ borderBottom: '2px solid rgba(139, 157, 175, 0.3)', backgroundColor: 'rgba(0, 217, 255, 0.05)' }}>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>#</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Track Name</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Code</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Tier</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }}>Status</TableCell>
                  <TableCell sx={{ color: '#fff', fontWeight: 700, fontSize: '0.875rem', border: '1px solid rgba(139, 157, 175, 0.2)' }} align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTracks.map((track: CurriculumTrack, index: number) => (
                  <TableRow
                    key={track.id}
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
                        <div className="font-semibold">{track.title || track.name}</div>
                        <div className="text-sm text-och-steel line-clamp-1 hover:line-clamp-none" title={track.description}>
                          {track.description}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <code className="px-2 py-1 bg-och-midnight/50 rounded text-och-mint font-mono text-xs">
                        {track.code}
                      </code>
                    </TableCell>
                    <TableCell sx={{ color: '#8B9DAF', border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      Tier {track.tier}
                    </TableCell>
                    <TableCell sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <Badge
                        variant={track.is_active ? 'defender' : 'steel'}
                        className="text-xs"
                      >
                        {track.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell align="right" sx={{ border: '1px solid rgba(139, 157, 175, 0.1)' }}>
                      <IconButton
                        onClick={(e) => handleMenuOpen(e, track)}
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
            router.push(`/dashboard/director/tracks/${selectedTrack?.slug}`)
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
            router.push(`/dashboard/director/tracks/${selectedTrack?.slug}/edit`)
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
            router.push(`/dashboard/director/modules?track=${selectedTrack?.slug}`)
            handleMenuClose()
          }}
          sx={{ color: '#8B9DAF', '&:hover': { backgroundColor: 'rgba(0, 217, 255, 0.1)', color: '#00D9FF' } }}
        >
          <ListItemIcon>
            <ViewModule sx={{ color: '#8B9DAF' }} fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Modules</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            fetchTracks()
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
            Are you sure you want to delete "{trackToDelete?.title || trackToDelete?.name}"? This will also delete all modules linked to this track. This action cannot be undone.
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
