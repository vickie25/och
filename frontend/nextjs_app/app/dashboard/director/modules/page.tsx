'use client'
 
import { useState, useEffect, useMemo } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { apiGateway } from '@/services/apiGateway'
import { Loader2, Trash2 } from 'lucide-react'

// --- Track colors mapping ---
const TRACK_COLORS: Record<string, string> = {
  'defender': 'bg-blue-600',
  'offensive': 'bg-red-600',
  'grc': 'bg-green-600',
  'innovation': 'bg-purple-600',
  'leadership': 'bg-orange-500',
}

const LEVELS = [
  { key: 'beginner',     label: 'Beginner',     tier: 'Tier 2' },
  { key: 'intermediate', label: 'Intermediate', tier: 'Tier 3' },
  { key: 'advanced',     label: 'Advanced',     tier: 'Tier 4' },
  { key: 'capstone',     label: 'Mastery',      tier: 'Tier 5' },
]

const LESSON_TYPES = [
  { key: 'video',      label: 'Video' },
  { key: 'guide',      label: 'Guide / Article' },
  { key: 'quiz',       label: 'Quiz' },
  { key: 'assessment', label: 'Assessment' },
  { key: 'lab',        label: 'Lab' },
  { key: 'reading',    label: 'Reading' },
]

// --- Types ---

interface CurriculumModule {
  id: string
  title: string
  description: string
  track_key: string
  level: string
  order_index: number
  estimated_time_minutes?: number
  lesson_count: number
  mission_count: number
  is_core: boolean
  is_required: boolean
}

interface Lesson {
  id: string
  title: string
  lesson_type: string
  content_url: string
  duration_minutes?: number
  order_index: number
}

// --- Main Page ---

interface Track {
  slug: string
  name: string
  code: string
}

export default function ModulesPage() {
  const [modules, setModules] = useState<CurriculumModule[]>([])
  const [tracks, setTracks] = useState<Track[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filterTrack, setFilterTrack] = useState<string>('all')
  const [filterLevel, setFilterLevel] = useState<string>('all')
  const [showCreateModule, setShowCreateModule] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedModuleId, setExpandedModuleId] = useState<string | null>(null)
  const [expandedTrackKey, setExpandedTrackKey] = useState<string | null>(null)
  const [moduleLessons, setModuleLessons] = useState<Record<string, Lesson[]>>({})
  const [addLessonToModule, setAddLessonToModule] = useState<CurriculumModule | null>(null)
  const [deletingModuleId, setDeletingModuleId] = useState<string | null>(null)
  const [deletingLessonId, setDeletingLessonId] = useState<string | null>(null)
  const [deleteModuleDialog, setDeleteModuleDialog] = useState<CurriculumModule | null>(null)
  const [deleteLessonDialog, setDeleteLessonDialog] = useState<{ moduleId: string; lesson: Lesson } | null>(null)
  const [previewContent, setPreviewContent] = useState<{ url: string; title: string; type: string } | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'student'>('list')
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null)
  const [selectedModule, setSelectedModule] = useState<CurriculumModule | null>(null)
  const [editModule, setEditModule] = useState<CurriculumModule | null>(null)
  const [editLesson, setEditLesson] = useState<{ moduleId: string; lesson: Lesson } | null>(null)

  useEffect(() => {
    fetchTracks()
    fetchModules()
  }, [filterTrack, filterLevel])

  const fetchTracks = async () => {
    try {
      const data = await apiGateway.get('/curriculum/tracks/') as any
      const trackList = data?.results || data?.data || data || []
      setTracks(trackList)
    } catch (error) {
      console.error('Failed to fetch tracks:', error)
    }
  }

  const fetchModules = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterTrack !== 'all') params.append('track', filterTrack)
      if (filterLevel !== 'all') params.append('level', filterLevel)
      const url = `/curriculum/modules/${params.toString() ? `?${params}` : ''}`
      const data = await apiGateway.get(url) as any
      setModules(data?.results || data?.data || data || [])
    } catch (error) {
      console.error('Failed to fetch modules:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchLessons = async (moduleId: string) => {
    try {
      const data = await apiGateway.get(`/curriculum/lessons/?module=${moduleId}`) as any
      const lessons = data?.results || data?.data || data || []
      setModuleLessons(prev => ({ ...prev, [moduleId]: lessons }))
    } catch (error) {
      console.error('Failed to fetch lessons:', error)
    }
  }

  const toggleExpand = (module: CurriculumModule) => {
    if (expandedModuleId === module.id) {
      setExpandedModuleId(null)
    } else {
      setExpandedModuleId(module.id)
      if (!moduleLessons[module.id]) {
        fetchLessons(module.id)
      }
    }
  }

  const toggleTrackExpand = (trackKey: string) => {
    setExpandedTrackKey(expandedTrackKey === trackKey ? null : trackKey)
  }

  const groupedModules = useMemo(() => {
    const groups: Record<string, CurriculumModule[]> = {}
    modules.forEach(module => {
      if (!groups[module.track_key]) {
        groups[module.track_key] = []
      }
      groups[module.track_key].push(module)
    })
    
    const levelOrder = { 'beginner': 1, 'intermediate': 2, 'advanced': 3, 'capstone': 4 }
    Object.keys(groups).forEach(trackKey => {
      groups[trackKey].sort((a, b) => {
        const levelDiff = (levelOrder[a.level as keyof typeof levelOrder] || 999) - (levelOrder[b.level as keyof typeof levelOrder] || 999)
        if (levelDiff !== 0) return levelDiff
        return a.order_index - b.order_index
      })
    })
    
    return groups
  }, [modules])

  const kpis = useMemo(() => {
    const total = modules.length
    const withLessons = modules.filter(m => m.lesson_count > 0).length
    const avgLessons = modules.length > 0
      ? Math.round(modules.reduce((sum, m) => sum + m.lesson_count, 0) / modules.length)
      : 0
    const totalLessons = modules.reduce((sum, m) => sum + m.lesson_count, 0)
    
    return { total, withLessons, avgLessons, totalLessons }
  }, [modules])

  const handleDeleteModule = async () => {
    if (!deleteModuleDialog) return
    setDeletingModuleId(deleteModuleDialog.id)
    try {
      await apiGateway.delete(`/curriculum/modules/${deleteModuleDialog.id}/`)
      setExpandedModuleId(prev => (prev === deleteModuleDialog.id ? null : prev))
      setModuleLessons(prev => {
        const next = { ...prev }
        delete next[deleteModuleDialog.id]
        return next
      })
      await fetchModules()
      setDeleteModuleDialog(null)
    } catch (error) {
      console.error('Failed to delete module:', error)
    } finally {
      setDeletingModuleId(null)
    }
  }

  const handleDeleteLesson = async () => {
    if (!deleteLessonDialog) return
    setDeletingLessonId(deleteLessonDialog.lesson.id)
    try {
      await apiGateway.delete(`/curriculum/lessons/${deleteLessonDialog.lesson.id}/`)
      await fetchLessons(deleteLessonDialog.moduleId)
      await fetchModules()
      setDeleteLessonDialog(null)
    } catch (error) {
      console.error('Failed to delete lesson:', error)
    } finally {
      setDeletingLessonId(null)
    }
  }

  const trackInfo = (slug: string) => {
    const track = tracks.find(t => t.slug === slug)
    return track ? {
      slug: track.slug,
      label: track.name,
      color: TRACK_COLORS[track.slug] || 'bg-slate-600'
    } : { slug, label: slug, color: 'bg-slate-600' }
  }
  const levelInfo = (key: string) => LEVELS.find(l => l.key === key) || { key, label: key, tier: '' }

  return (
    <RouteGuard requiredRoles={['program_director', 'admin']}>
      <div className="max-w-7xl mx-auto">

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Curriculum Modules</h1>
              <p className="text-och-steel">
                Manage learning modules linked to tracks and levels — these appear in student learning paths
              </p>
            </div>
            <Button
              onClick={() => setShowCreateModule(true)}
              variant="defender"
              className="flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create Module
            </Button>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <Card className="bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/30">
              <div className="p-4">
                <p className="text-och-steel text-sm mb-1">Total Modules</p>
                <p className="text-3xl font-bold text-white">{kpis.total}</p>
              </div>
            </Card>
            <Card className="bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/30">
              <div className="p-4">
                <p className="text-och-steel text-sm mb-1">With Lessons</p>
                <p className="text-3xl font-bold text-och-mint">{kpis.withLessons}</p>
              </div>
            </Card>
            <Card className="bg-gradient-to-br from-och-orange/20 to-och-orange/5 border-och-orange/30">
              <div className="p-4">
                <p className="text-och-steel text-sm mb-1">Total Lessons</p>
                <p className="text-3xl font-bold text-och-orange">{kpis.totalLessons}</p>
              </div>
            </Card>
            <Card className="bg-gradient-to-br from-och-gold/20 to-och-gold/5 border-och-gold/30">
              <div className="p-4">
                <p className="text-och-steel text-sm mb-1">Avg Lessons</p>
                <p className="text-3xl font-bold text-och-gold">{kpis.avgLessons}</p>
              </div>
            </Card>
          </div>

          {/* View Mode Toggle */}
          <div className="flex justify-center gap-2 mb-4">
            <Button
              onClick={() => setViewMode('list')}
              variant={viewMode === 'list' ? 'defender' : 'outline'}
              size="sm"
            >
              List View
            </Button>
            <Button
              onClick={() => setViewMode('student')}
              variant={viewMode === 'student' ? 'defender' : 'outline'}
              size="sm"
            >
              Student View
            </Button>
          </div>

          {/* Filters */}
          <Card className="border-och-steel/20 bg-gradient-to-r from-och-midnight/50 to-och-midnight/30 mb-4">
            <div className="p-4">
              <div className="flex flex-wrap gap-3">
                <div className="flex-1 min-w-[200px]">
                  <label className="text-xs text-och-steel block mb-1">Search Modules</label>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by module title or description..."
                    className="w-full px-3 py-2 bg-och-midnight/70 border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none focus:ring-2 focus:ring-och-defender/20"
                  />
                </div>
                <div>
                  <label className="text-xs text-och-steel block mb-1">Track</label>
                  <select
                    value={filterTrack}
                    onChange={e => setFilterTrack(e.target.value)}
                    className="px-3 py-2 bg-och-midnight/70 border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none focus:ring-2 focus:ring-och-defender/20"
                  >
                    <option value="all">All Tracks</option>
                    {tracks.map(t => (
                      <option key={t.slug} value={t.slug}>{t.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-och-steel block mb-1">Level</label>
                  <select
                    value={filterLevel}
                    onChange={e => setFilterLevel(e.target.value)}
                    className="px-3 py-2 bg-och-midnight/70 border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none focus:ring-2 focus:ring-och-defender/20"
                  >
                    <option value="all">All Levels</option>
                    {LEVELS.map(l => (
                      <option key={l.key} value={l.key}>{l.label} ({l.tier})</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </Card>

          {/* Module Count Summary */}
          {!isLoading && tracks.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {tracks.map(t => {
                const count = modules.filter(m => m.track_key === t.slug).length
                const color = TRACK_COLORS[t.slug] || 'bg-slate-600'
                return count > 0 ? (
                  <span key={t.slug} className={`text-xs px-3 py-1 rounded-full text-white ${color}`}>
                    {t.name}: {count} module{count !== 1 ? 's' : ''}
                  </span>
                ) : null
              })}
            </div>
          )}

          {/* Module List */}
          {isLoading ? (
            <div className="flex items-center justify-center min-h-[300px]">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-och-defender" />
            </div>
          ) : modules.length === 0 ? (
            <Card className="border-och-steel/20 bg-och-midnight/50">
              <div className="p-12 text-center">
                <p className="text-och-steel mb-2 text-lg">No modules found</p>
                <p className="text-och-steel/70 mb-6 text-sm">
                  Create your first curriculum module to start building the student learning path
                </p>
                <Button onClick={() => setShowCreateModule(true)} variant="defender">
                  Create First Module
                </Button>
              </div>
            </Card>
          ) : viewMode === 'student' ? (
            <div className="grid lg:grid-cols-4 gap-6">
              {/* Sidebar: Module & Lesson List */}
              <div className="lg:col-span-1">
                <Card className="p-4 bg-och-midnight/50 border-och-steel/20 sticky top-4">
                  <h3 className="text-lg font-semibold text-white mb-4">Learning Path</h3>
                  <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
                    {Object.entries(groupedModules).map(([trackKey, trackModules]) => {
                      const track = trackInfo(trackKey)
                      const filteredTrackModules = trackModules.filter(module => {
                        if (!searchQuery) return true
                        const query = searchQuery.toLowerCase()
                        return module.title.toLowerCase().includes(query) || 
                               module.description?.toLowerCase().includes(query)
                      })
                      
                      if (filteredTrackModules.length === 0 && searchQuery) return null

                      return (
                        <div key={trackKey} className="mb-4">
                          <div className="flex items-center gap-2 mb-2">
                            <div className={`w-6 h-6 rounded ${track.color} flex items-center justify-center`}>
                              <span className="text-white font-bold text-xs">{track.label.charAt(0)}</span>
                            </div>
                            <h4 className="text-sm font-bold text-white">{track.label}</h4>
                          </div>
                          {filteredTrackModules.map(module => {
                            const level = levelInfo(module.level)
                            const lessons = moduleLessons[module.id] || []
                            const isModuleExpanded = expandedModuleId === module.id
                            
                            return (
                              <div key={module.id} className="mb-2">
                                <button
                                  onClick={() => {
                                    if (expandedModuleId === module.id) {
                                      setExpandedModuleId(null)
                                    } else {
                                      setExpandedModuleId(module.id)
                                      setSelectedModule(module)
                                      if (!moduleLessons[module.id]) {
                                        fetchLessons(module.id)
                                      }
                                      if (lessons.length > 0) {
                                        setSelectedLesson(lessons[0])
                                      }
                                    }
                                  }}
                                  className="w-full text-left p-2 rounded-lg bg-och-midnight/70 border border-och-steel/30 hover:bg-och-midnight transition-all"
                                >
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">{level.label}</span>
                                    <p className="text-sm font-medium text-white truncate flex-1">{module.title}</p>
                                    <svg
                                      className={`w-4 h-4 text-och-steel transition-transform ${isModuleExpanded ? 'rotate-180' : ''}`}
                                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                                    >
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                  </div>
                                </button>
                                {isModuleExpanded && lessons.length > 0 && (
                                  <div className="ml-2 mt-1 space-y-1">
                                    {lessons.map((lesson, idx) => (
                                      <button
                                        key={lesson.id}
                                        onClick={() => {
                                          setSelectedLesson(lesson)
                                          setSelectedModule(module)
                                        }}
                                        className={`w-full text-left p-2 rounded text-xs transition-all ${
                                          selectedLesson?.id === lesson.id
                                            ? 'bg-och-defender/20 border border-och-defender/30 text-white'
                                            : 'bg-och-midnight/50 border border-och-steel/20 text-och-steel hover:text-white hover:bg-och-midnight/70'
                                        }`}
                                      >
                                        <div className="flex items-center gap-2">
                                          <span className="text-xs text-och-steel/50">{idx + 1}</span>
                                          <span className="truncate flex-1">{lesson.title}</span>
                                        </div>
                                      </button>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      )
                    })}
                  </div>
                </Card>
              </div>

              {/* Content Area */}
              <div className="lg:col-span-3">
                {selectedLesson && selectedModule ? (
                  <Card className="p-6 bg-och-midnight/50 border-och-steel/20">
                    <div className="mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-300">
                          {levelInfo(selectedModule.level).label}
                        </span>
                        <span className="text-xs px-2 py-1 rounded bg-och-defender/20 text-och-mint">
                          {selectedLesson.lesson_type}
                        </span>
                      </div>
                      <h2 className="text-xl font-semibold text-white mb-1">{selectedLesson.title}</h2>
                      <p className="text-sm text-och-steel">
                        {trackInfo(selectedModule.track_key).label} • {selectedModule.title}
                      </p>
                    </div>
                    <div className="bg-slate-800 rounded-lg overflow-hidden">
                      {selectedLesson.content_url ? (
                        selectedLesson.lesson_type === 'video' ? (
                          <div className="aspect-video">
                            {selectedLesson.content_url.includes('youtube.com') || selectedLesson.content_url.includes('youtu.be') ? (
                              <iframe
                                src={selectedLesson.content_url.replace('watch?v=', 'embed/')}
                                className="w-full h-full"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                                title={selectedLesson.title}
                              />
                            ) : (
                              <video
                                src={selectedLesson.content_url}
                                controls
                                className="w-full h-full"
                              />
                            )}
                          </div>
                        ) : (
                          <iframe
                            src={selectedLesson.content_url}
                            className="w-full h-[600px]"
                            title={selectedLesson.title}
                          />
                        )
                      ) : (
                        <div className="aspect-video flex items-center justify-center text-och-steel">
                          No content URL configured
                        </div>
                      )}
                    </div>
                    {selectedLesson.duration_minutes && (
                      <p className="text-sm text-och-steel mt-4">
                        Duration: {selectedLesson.duration_minutes} minutes
                      </p>
                    )}
                  </Card>
                ) : (
                  <Card className="p-6 bg-och-midnight/50 border-och-steel/20">
                    <div className="flex flex-col items-center justify-center h-96 text-center">
                      <p className="text-och-steel text-lg mb-2">Select a lesson to preview</p>
                      <p className="text-och-steel/70 text-sm">Choose a module and lesson from the sidebar to see how it appears to students</p>
                    </div>
                  </Card>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(groupedModules).map(([trackKey, trackModules]) => {
                const track = trackInfo(trackKey)
                const isTrackExpanded = expandedTrackKey === trackKey
                
                const filteredTrackModules = trackModules.filter(module => {
                  if (!searchQuery) return true
                  const query = searchQuery.toLowerCase()
                  return module.title.toLowerCase().includes(query) || 
                         module.description?.toLowerCase().includes(query)
                })
                
                if (filteredTrackModules.length === 0 && searchQuery) return null

                return (
                  <Card key={trackKey} className="border-och-steel/20 bg-och-midnight/50">
                    <div 
                      className="p-4 cursor-pointer hover:bg-och-defender/5 transition-colors"
                      onClick={() => toggleTrackExpand(trackKey)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-12 h-12 rounded-lg ${track.color} flex items-center justify-center`}>
                            <span className="text-white font-bold text-lg">{track.label.charAt(0)}</span>
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-white">{track.label}</h3>
                            <p className="text-sm text-och-steel">{filteredTrackModules.length} module{filteredTrackModules.length !== 1 ? 's' : ''}</p>
                          </div>
                        </div>
                        <button className="text-och-steel hover:text-white transition-colors p-2">
                          <svg
                            className={`w-6 h-6 transition-transform ${isTrackExpanded ? 'rotate-180' : ''}`}
                            fill="none" stroke="currentColor" viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                      </div>
                    </div>

                    {isTrackExpanded && (
                      <div className="border-t border-och-steel/20 p-4 space-y-3">
                        {filteredTrackModules.map(module => {
                          const level = levelInfo(module.level)
                          const isModuleExpanded = expandedModuleId === module.id
                          const lessons = moduleLessons[module.id] || []

                          return (
                            <Card key={module.id} className="border-och-steel/10 bg-och-midnight/30">
                              <div className="p-4">
                                {/* Module header row */}
                                <div className="flex items-start justify-between">
                                  <div className="flex items-start gap-3 flex-1">
                                    {/* Level badge */}
                                    <div className="flex flex-col gap-1 pt-0.5">
                                      <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300 text-center">
                                        {level.label}
                                      </span>
                                      <span className="text-xs px-2 py-0.5 rounded bg-slate-600 text-slate-400 text-center">
                                        {level.tier}
                                      </span>
                                    </div>

                                    <div className="flex-1">
                                      <div className="flex items-center gap-2">
                                        <span className="text-och-steel/60 text-xs">#{module.order_index}</span>
                                        <h4 className="text-white font-semibold">{module.title}</h4>
                                        {module.is_core && (
                                          <span className="text-xs bg-och-defender/20 text-och-mint px-2 py-0.5 rounded">Core</span>
                                        )}
                                      </div>
                                      {module.description && (
                                        <p className="text-sm text-och-steel mt-1 line-clamp-1">{module.description}</p>
                                      )}
                                      <div className="flex items-center gap-3 mt-2 text-xs text-och-steel/70">
                                        <span>{module.lesson_count} lesson{module.lesson_count !== 1 ? 's' : ''}</span>
                                        {module.mission_count > 0 && <span>{module.mission_count} mission{module.mission_count !== 1 ? 's' : ''}</span>}
                                        {module.estimated_time_minutes && <span>{module.estimated_time_minutes} min</span>}
                                      </div>
                                    </div>
                                  </div>

                                  {/* Actions */}
                                  <div className="flex items-center gap-2 ml-3">
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => setAddLessonToModule(module)}
                                      className="text-xs border-och-steel/50 text-och-steel hover:border-och-mint hover:text-och-mint"
                                    >
                                      + Lesson
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => setEditModule(module)}
                                      className="text-xs border-och-steel/50 text-och-steel hover:border-och-defender hover:text-och-defender"
                                      title="Edit module"
                                    >
                                      Edit
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => setDeleteModuleDialog(module)}
                                      disabled={!!deletingModuleId}
                                      className="text-xs border-red-500/50 text-red-400 hover:border-red-500 hover:bg-red-500/10"
                                      title="Delete module and all lessons"
                                    >
                                      {deletingModuleId === module.id ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                      ) : (
                                        <Trash2 className="w-4 h-4" />
                                      )}
                                    </Button>
                                    <button
                                      onClick={() => toggleExpand(module)}
                                      className="text-och-steel hover:text-white transition-colors p-1"
                                    >
                                      <svg
                                        className={`w-5 h-5 transition-transform ${isModuleExpanded ? 'rotate-180' : ''}`}
                                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                                      >
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                      </svg>
                                    </button>
                                  </div>
                                </div>

                                {/* Expanded lessons */}
                                {isModuleExpanded && (
                                  <div className="mt-4 border-t border-och-steel/20 pt-4">
                                    <p className="text-xs text-och-steel mb-3">Lessons in this module:</p>
                                    {lessons.length === 0 ? (
                                      <p className="text-xs text-och-steel/50 italic">
                                        No lessons yet — click "+ Lesson" to add one
                                      </p>
                                    ) : (
                                      <div className="space-y-2">
                                        {lessons.map((lesson, idx) => (
                                          <div key={lesson.id} className="flex items-center gap-3 bg-och-midnight/80 rounded-lg px-3 py-2">
                                            <span className="text-xs text-och-steel/50 w-5">{idx + 1}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded ${
                                              lesson.lesson_type === 'video' ? 'bg-blue-500/20 text-blue-300' :
                                              lesson.lesson_type === 'quiz' ? 'bg-yellow-500/20 text-yellow-300' :
                                              lesson.lesson_type === 'lab' ? 'bg-green-500/20 text-green-300' :
                                              'bg-slate-700 text-slate-300'
                                            }`}>
                                              {lesson.lesson_type}
                                            </span>
                                            <span className="text-sm text-white flex-1">{lesson.title}</span>
                                            {lesson.duration_minutes && (
                                              <span className="text-xs text-och-steel/50">{lesson.duration_minutes}m</span>
                                            )}
                                            {lesson.content_url && (
                                              <button
                                                onClick={() => setPreviewContent({ url: lesson.content_url, title: lesson.title, type: lesson.lesson_type })}
                                                className="text-xs text-och-mint hover:text-och-mint/80 hover:underline"
                                              >
                                                View
                                              </button>
                                            )}
                                            <button
                                              onClick={() => setEditLesson({ moduleId: module.id, lesson })}
                                              className="text-xs text-och-defender hover:text-och-defender/80 hover:underline"
                                            >
                                              Edit
                                            </button>
                                            <Button
                                              variant="ghost"
                                              size="sm"
                                              onClick={() => setDeleteLessonDialog({ moduleId: module.id, lesson })}
                                              disabled={!!deletingLessonId}
                                              className="text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 p-1.5 min-w-0 h-7"
                                              title="Delete lesson"
                                            >
                                              {deletingLessonId === lesson.id ? (
                                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                              ) : (
                                                <Trash2 className="w-3.5 h-3.5" />
                                              )}
                                            </Button>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            </Card>
                          )
                        })}
                      </div>
                    )}
                  </Card>
                )
              })}
            </div>
          )}
        </div>

        {/* Create Module Modal */}
        {showCreateModule && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-2xl bg-och-midnight border border-och-steel/20 rounded-lg shadow-xl">
              <CreateModuleForm
                tracks={tracks}
                onClose={() => setShowCreateModule(false)}
                onSuccess={() => { setShowCreateModule(false); fetchModules() }}
              />
            </div>
          </div>
        )}

        {/* Add Lesson Modal */}
        {addLessonToModule && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-lg bg-och-midnight border border-och-steel/20 rounded-lg shadow-xl">
              <AddLessonForm
                module={addLessonToModule}
                tracks={tracks}
                onClose={() => setAddLessonToModule(null)}
                onSuccess={() => {
                  fetchLessons(addLessonToModule.id)
                  fetchModules()
                  setAddLessonToModule(null)
                  setExpandedModuleId(addLessonToModule.id)
                }}
              />
            </div>
          </div>
        )}

        {/* Edit Module Modal */}
        {editModule && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-2xl bg-och-midnight border border-och-steel/20 rounded-lg shadow-xl">
              <EditModuleForm
                module={editModule}
                tracks={tracks}
                onClose={() => setEditModule(null)}
                onSuccess={() => { setEditModule(null); fetchModules() }}
              />
            </div>
          </div>
        )}

        {/* Edit Lesson Modal */}
        {editLesson && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-lg bg-och-midnight border border-och-steel/20 rounded-lg shadow-xl">
              <EditLessonForm
                lesson={editLesson.lesson}
                moduleId={editLesson.moduleId}
                tracks={tracks}
                onClose={() => setEditLesson(null)}
                onSuccess={() => {
                  fetchLessons(editLesson.moduleId)
                  fetchModules()
                  setEditLesson(null)
                }}
              />
            </div>
          </div>
        )}

        {/* Delete Module Modal */}
        {deleteModuleDialog && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-och-midnight border border-och-steel/20 rounded-lg shadow-xl">
              <div className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Confirm Delete</h2>
                <p className="text-och-steel mb-6">
                  Are you sure you want to delete "{deleteModuleDialog.title}" and all its lessons? This action cannot be undone.
                </p>
                <div className="flex justify-end gap-3">
                  <Button
                    variant="outline"
                    onClick={() => setDeleteModuleDialog(null)}
                    disabled={!!deletingModuleId}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="orange"
                    onClick={handleDeleteModule}
                    disabled={!!deletingModuleId}
                    className="bg-och-orange hover:bg-och-orange/90"
                  >
                    {deletingModuleId ? 'Deleting...' : 'Delete'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Delete Lesson Modal */}
        {deleteLessonDialog && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-och-midnight border border-och-steel/20 rounded-lg shadow-xl">
              <div className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Confirm Delete</h2>
                <p className="text-och-steel mb-6">
                  Are you sure you want to delete lesson "{deleteLessonDialog.lesson.title}"? This action cannot be undone.
                </p>
                <div className="flex justify-end gap-3">
                  <Button
                    variant="outline"
                    onClick={() => setDeleteLessonDialog(null)}
                    disabled={!!deletingLessonId}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="orange"
                    onClick={handleDeleteLesson}
                    disabled={!!deletingLessonId}
                    className="bg-och-orange hover:bg-och-orange/90"
                  >
                    {deletingLessonId ? 'Deleting...' : 'Delete'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Content Preview Modal */}
        {previewContent && (
          <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-4xl bg-och-midnight border border-och-steel/20 rounded-lg shadow-xl">
              <div className="p-4 border-b border-och-steel/20 flex items-center justify-between">
                <h2 className="text-lg font-bold text-white">{previewContent.title}</h2>
                <button
                  onClick={() => setPreviewContent(null)}
                  className="text-och-steel hover:text-white p-1"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-4">
                {previewContent.type === 'video' ? (
                  <video
                    controls
                    className="w-full rounded-lg"
                    src={previewContent.url}
                  >
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <iframe
                    src={previewContent.url}
                    className="w-full h-[600px] rounded-lg"
                    title={previewContent.title}
                  />
                )}
              </div>
            </div>
          </div>
        )}
    </RouteGuard>
  )
}

// --- Create Module Form ---

function CreateModuleForm({
  tracks,
  onClose,
  onSuccess,
}: {
  tracks: Track[]
  onClose: () => void
  onSuccess: () => void
}) {
  const [isLoading, setIsLoading] = useState(false)
  const [form, setForm] = useState({
    track_key: tracks.length > 0 ? tracks[0].slug : 'defender',
    level: LEVELS[0].key,
    title: '',
    description: '',
    order_index: 1,
    estimated_time_minutes: 30,
    is_core: true,
    is_required: true,
  })

  const updateField = (key: keyof typeof form, value: any) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await apiGateway.post('/curriculum/modules/', form)
      onSuccess()
    } catch (error) {
      console.error('Failed to create module:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white">Create Module</h2>
          <p className="text-och-steel text-sm mt-1">
            Module will appear in the student learning path.
          </p>
        </div>
        <button onClick={onClose} className="text-och-steel hover:text-white p-1">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Track</label>
            <select
              value={form.track_key}
              onChange={(e) => updateField('track_key', e.target.value)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            >
              {tracks.map((t) => (
                <option key={t.slug} value={t.slug}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Level</label>
            <select
              value={form.level}
              onChange={(e) => updateField('level', e.target.value)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            >
              {LEVELS.map((l) => (
                <option key={l.key} value={l.key}>
                  {l.label} ({l.tier})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-och-steel mb-1">Title *</label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => updateField('title', e.target.value)}
            required
            className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            placeholder="e.g. SOC Operations Fundamentals"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-och-steel mb-1">Description</label>
          <textarea
            value={form.description}
            onChange={(e) => updateField('description', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            placeholder="Short summary of what this module covers"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Order</label>
            <input
              type="number"
              min={1}
              value={form.order_index}
              onChange={(e) => updateField('order_index', parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Estimated Time (min)</label>
            <input
              type="number"
              min={5}
              value={form.estimated_time_minutes}
              onChange={(e) =>
                updateField('estimated_time_minutes', parseInt(e.target.value) || 0)
              }
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            />
          </div>
          <div className="flex items-center gap-4 mt-6 md:mt-0">
            <label className="flex items-center gap-2 text-sm text-och-steel">
              <input
                type="checkbox"
                checked={form.is_core}
                onChange={(e) => updateField('is_core', e.target.checked)}
              />
              Core
            </label>
            <label className="flex items-center gap-2 text-sm text-och-steel">
              <input
                type="checkbox"
                checked={form.is_required}
                onChange={(e) => updateField('is_required', e.target.checked)}
              />
              Required
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="defender" disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create Module'}
          </Button>
        </div>
      </form>
    </div>
  )
}

// --- Add Lesson Form ---

function AddLessonForm({
  module,
  tracks,
  onClose,
  onSuccess,
}: {
  module: CurriculumModule
  tracks: Track[]
  onClose: () => void
  onSuccess: () => void
}) {
  const [isLoading, setIsLoading] = useState(false)
  const [uploadMethod, setUploadMethod] = useState<'url' | 'file'>('url')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [form, setForm] = useState({
    title: '',
    lesson_type: LESSON_TYPES[0].key,
    content_url: '',
    duration_minutes: 15,
    order_index: 1,
  })

  const updateField = (key: keyof typeof form, value: any) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      let contentUrl = form.content_url || ''

      // If video type and file upload method, upload file first
      if (form.lesson_type === 'video' && uploadMethod === 'file' && selectedFile) {
        setIsUploading(true)
        const formData = new FormData()
        formData.append('video', selectedFile)
        
        const xhr = new XMLHttpRequest()
        
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100)
            setUploadProgress(percentComplete)
          }
        })
        
        const uploadPromise = new Promise<string>((resolve, reject) => {
          xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              const response = JSON.parse(xhr.responseText)
              resolve(response.url)
            } else {
              const error = JSON.parse(xhr.responseText)
              reject(new Error(error.error || 'Failed to upload video'))
            }
          })
          
          xhr.addEventListener('error', () => {
            reject(new Error('Network error during upload'))
          })
          
          xhr.open('POST', `${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/v1/curriculum/lessons/upload-video/`)
          xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('auth_token')}`)
          xhr.send(formData)
        })
        
        contentUrl = await uploadPromise
        setIsUploading(false)
      }

      // Create lesson with content URL
      await apiGateway.post('/curriculum/lessons/', {
        ...form,
        content_url: contentUrl,
        module: module.id,
      })
      onSuccess()
    } catch (error: any) {
      console.error('Failed to add lesson:', error)
      alert(error.message || 'Failed to add lesson')
      setIsUploading(false)
    } finally {
      setIsLoading(false)
      setUploadProgress(0)
    }
  }

  const track = tracks.find((t) => t.slug === module.track_key)
  const level = LEVELS.find((l) => l.key === module.level)

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white">Add Lesson</h2>
          <p className="text-och-steel text-xs mt-1">
            {track?.name} · {level?.label} · {module.title}
          </p>
        </div>
        <button onClick={onClose} className="text-och-steel hover:text-white p-1">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Lesson Type</label>
            <select
              value={form.lesson_type}
              onChange={(e) => updateField('lesson_type', e.target.value)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            >
              {LESSON_TYPES.map((t) => (
                <option key={t.key} value={t.key}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Order</label>
            <input
              type="number"
              min={1}
              value={form.order_index}
              onChange={(e) => updateField('order_index', parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-och-steel mb-1">Title *</label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => updateField('title', e.target.value)}
            required
            className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            placeholder="e.g. SOC Analyst Workflow — From Alert to Closure"
          />
        </div>

        {form.lesson_type === 'video' && (
          <div>
            <label className="block text-sm font-medium text-och-steel mb-2">Content Source</label>
            <div className="flex gap-2 mb-3">
              <Button
                type="button"
                variant={uploadMethod === 'url' ? 'defender' : 'outline'}
                size="sm"
                onClick={() => setUploadMethod('url')}
              >
                URL
              </Button>
              <Button
                type="button"
                variant={uploadMethod === 'file' ? 'defender' : 'outline'}
                size="sm"
                onClick={() => setUploadMethod('file')}
              >
                Upload File
              </Button>
            </div>
          </div>
        )}

        {form.lesson_type === 'video' && uploadMethod === 'file' ? (
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Upload Video File</label>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-och-defender file:text-white hover:file:bg-och-defender/80"
            />
            {selectedFile && (
              <p className="text-xs text-och-steel mt-1">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
            {isUploading && (
              <div className="mt-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-och-steel">Uploading...</span>
                  <span className="text-xs text-och-mint font-semibold">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-och-midnight/70 rounded-full h-2 overflow-hidden">
                  <div 
                    className="bg-och-defender h-full transition-all duration-300 ease-out"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">
              {form.lesson_type === 'video' ? 'Content URL' : 'Content URL'}
            </label>
            <input
              type="url"
              value={form.content_url || ''}
              onChange={(e) => updateField('content_url', e.target.value)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
              placeholder="https://..."
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-och-steel mb-1">Duration (minutes)</label>
          <input
            type="number"
            min={1}
            value={form.duration_minutes}
            onChange={(e) => updateField('duration_minutes', parseInt(e.target.value) || 1)}
            className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
          />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={isLoading || isUploading}>
            Cancel
          </Button>
          <Button type="submit" variant="defender" disabled={isLoading || isUploading}>
            {isUploading ? `Uploading ${uploadProgress}%` : isLoading ? 'Adding...' : 'Add Lesson'}
          </Button>
        </div>
      </form>
    </div>
  )
}

// --- Edit Module Form ---

function EditModuleForm({
  module,
  tracks,
  onClose,
  onSuccess,
}: {
  module: CurriculumModule
  tracks: Track[]
  onClose: () => void
  onSuccess: () => void
}) {
  const [isLoading, setIsLoading] = useState(false)
  const [form, setForm] = useState({
    track_key: module.track_key,
    level: module.level,
    title: module.title,
    description: module.description || '',
    order_index: module.order_index,
    estimated_time_minutes: module.estimated_time_minutes || 30,
    is_core: module.is_core,
    is_required: module.is_required,
  })

  const updateField = (key: keyof typeof form, value: any) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await apiGateway.put(`/curriculum/modules/${module.id}/`, form)
      onSuccess()
    } catch (error) {
      console.error('Failed to update module:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white">Edit Module</h2>
          <p className="text-och-steel text-sm mt-1">
            Update module details and settings.
          </p>
        </div>
        <button onClick={onClose} className="text-och-steel hover:text-white p-1">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Track</label>
            <select
              value={form.track_key}
              onChange={(e) => updateField('track_key', e.target.value)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            >
              {tracks.map((t) => (
                <option key={t.slug} value={t.slug}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Level</label>
            <select
              value={form.level}
              onChange={(e) => updateField('level', e.target.value)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            >
              {LEVELS.map((l) => (
                <option key={l.key} value={l.key}>
                  {l.label} ({l.tier})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-och-steel mb-1">Title *</label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => updateField('title', e.target.value)}
            required
            className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            placeholder="e.g. SOC Operations Fundamentals"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-och-steel mb-1">Description</label>
          <textarea
            value={form.description}
            onChange={(e) => updateField('description', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            placeholder="Short summary of what this module covers"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Order</label>
            <input
              type="number"
              min={1}
              value={form.order_index}
              onChange={(e) => updateField('order_index', parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Estimated Time (min)</label>
            <input
              type="number"
              min={5}
              value={form.estimated_time_minutes}
              onChange={(e) =>
                updateField('estimated_time_minutes', parseInt(e.target.value) || 0)
              }
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            />
          </div>
          <div className="flex items-center gap-4 mt-6 md:mt-0">
            <label className="flex items-center gap-2 text-sm text-och-steel">
              <input
                type="checkbox"
                checked={form.is_core}
                onChange={(e) => updateField('is_core', e.target.checked)}
              />
              Core
            </label>
            <label className="flex items-center gap-2 text-sm text-och-steel">
              <input
                type="checkbox"
                checked={form.is_required}
                onChange={(e) => updateField('is_required', e.target.checked)}
              />
              Required
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="defender" disabled={isLoading}>
            {isLoading ? 'Updating...' : 'Update Module'}
          </Button>
        </div>
      </form>
    </div>
  )
}

// --- Edit Lesson Form ---

function EditLessonForm({
  lesson,
  moduleId,
  tracks,
  onClose,
  onSuccess,
}: {
  lesson: Lesson
  moduleId: string
  tracks: Track[]
  onClose: () => void
  onSuccess: () => void
}) {
  const [isLoading, setIsLoading] = useState(false)
  const [uploadMethod, setUploadMethod] = useState<'url' | 'file'>('url')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [form, setForm] = useState({
    title: lesson.title,
    lesson_type: lesson.lesson_type,
    content_url: lesson.content_url || '',
    duration_minutes: lesson.duration_minutes || 15,
    order_index: lesson.order_index,
  })

  const updateField = (key: keyof typeof form, value: any) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      let contentUrl = form.content_url || ''

      // If video type and file upload method, upload file first
      if (form.lesson_type === 'video' && uploadMethod === 'file' && selectedFile) {
        setIsUploading(true)
        const formData = new FormData()
        formData.append('video', selectedFile)
        
        const xhr = new XMLHttpRequest()
        
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100)
            setUploadProgress(percentComplete)
          }
        })
        
        const uploadPromise = new Promise<string>((resolve, reject) => {
          xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              const response = JSON.parse(xhr.responseText)
              resolve(response.url)
            } else {
              const error = JSON.parse(xhr.responseText)
              reject(new Error(error.error || 'Failed to upload video'))
            }
          })
          
          xhr.addEventListener('error', () => {
            reject(new Error('Network error during upload'))
          })
          
          xhr.open('POST', `${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/v1/curriculum/lessons/upload-video/`)
          xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('auth_token')}`)
          xhr.send(formData)
        })
        
        contentUrl = await uploadPromise
        setIsUploading(false)
      }

      // Update lesson with content URL
      await apiGateway.put(`/curriculum/lessons/${lesson.id}/`, {
        ...form,
        content_url: contentUrl,
        module: moduleId,
      })
      onSuccess()
    } catch (error: any) {
      console.error('Failed to update lesson:', error)
      alert(error.message || 'Failed to update lesson')
      setIsUploading(false)
    } finally {
      setIsLoading(false)
      setUploadProgress(0)
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white">Edit Lesson</h2>
          <p className="text-och-steel text-xs mt-1">
            Update lesson details and content.
          </p>
        </div>
        <button onClick={onClose} className="text-och-steel hover:text-white p-1">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Lesson Type</label>
            <select
              value={form.lesson_type}
              onChange={(e) => updateField('lesson_type', e.target.value)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            >
              {LESSON_TYPES.map((t) => (
                <option key={t.key} value={t.key}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Order</label>
            <input
              type="number"
              min={1}
              value={form.order_index}
              onChange={(e) => updateField('order_index', parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-och-steel mb-1">Title *</label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => updateField('title', e.target.value)}
            required
            className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
            placeholder="e.g. SOC Analyst Workflow — From Alert to Closure"
          />
        </div>

        {form.lesson_type === 'video' && (
          <div>
            <label className="block text-sm font-medium text-och-steel mb-2">Content Source</label>
            <div className="flex gap-2 mb-3">
              <Button
                type="button"
                variant={uploadMethod === 'url' ? 'defender' : 'outline'}
                size="sm"
                onClick={() => setUploadMethod('url')}
              >
                URL
              </Button>
              <Button
                type="button"
                variant={uploadMethod === 'file' ? 'defender' : 'outline'}
                size="sm"
                onClick={() => setUploadMethod('file')}
              >
                Upload File
              </Button>
            </div>
          </div>
        )}

        {form.lesson_type === 'video' && uploadMethod === 'file' ? (
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">Upload Video File</label>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-och-defender file:text-white hover:file:bg-och-defender/80"
            />
            {selectedFile && (
              <p className="text-xs text-och-steel mt-1">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
            {isUploading && (
              <div className="mt-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-och-steel">Uploading...</span>
                  <span className="text-xs text-och-mint font-semibold">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-och-midnight/70 rounded-full h-2 overflow-hidden">
                  <div 
                    className="bg-och-defender h-full transition-all duration-300 ease-out"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-och-steel mb-1">
              {form.lesson_type === 'video' ? 'Content URL' : 'Content URL'}
            </label>
            <input
              type="url"
              value={form.content_url || ''}
              onChange={(e) => updateField('content_url', e.target.value)}
              className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
              placeholder="https://..."
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-och-steel mb-1">Duration (minutes)</label>
          <input
            type="number"
            min={1}
            value={form.duration_minutes}
            onChange={(e) => updateField('duration_minutes', parseInt(e.target.value) || 1)}
            className="w-full px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white text-sm focus:border-och-defender focus:outline-none"
          />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={isLoading || isUploading}>
            Cancel
          </Button>
          <Button type="submit" variant="defender" disabled={isLoading || isUploading}>
            {isUploading ? `Uploading ${uploadProgress}%` : isLoading ? 'Updating...' : 'Update Lesson'}
          </Button>
        </div>
      </form>
    </div>
  )
}
