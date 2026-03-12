'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
} from '@hello-pangea/dnd'
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  FormControlLabel,
  TextField,
  Switch,
  Chip,
  Box,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  ExpandMore,
  DragIndicator,
  PlayArrow,
  Article,
  Quiz,
  Assignment,
  Science,
  Workshop,
  VideoLibrary,
  Schedule,
  Info,
} from '@mui/icons-material'

interface Module {
  id: string
  name: string
  description: string
  content_type: string
  estimated_hours: number
  skills: string[]
  order: number
  is_selected: boolean
}

interface Milestone {
  id: string
  name: string
  description: string
  order: number
  duration_weeks: number
  modules: Module[]
}

interface Track {
  id: string
  name: string
  description: string
}

interface AvailableContent {
  track: Track
  milestones: Milestone[]
}

interface SelectedContent {
  milestone_id: string
  module_id: string
  is_required: boolean
  custom_order: number
  custom_duration_hours?: number
  custom_description?: string
}

interface DynamicContentSelectorProps {
  cohortId?: string
  trackId: string
  onContentChange?: (selectedContent: SelectedContent[]) => void
  initialContent?: SelectedContent[]
}

const getContentTypeIcon = (contentType: string) => {
  switch (contentType) {
    case 'video': return <VideoLibrary fontSize="small" />
    case 'article': return <Article fontSize="small" />
    case 'quiz': return <Quiz fontSize="small" />
    case 'assignment': return <Assignment fontSize="small" />
    case 'lab': return <Science fontSize="small" />
    case 'workshop': return <Workshop fontSize="small" />
    default: return <PlayArrow fontSize="small" />
  }
}

const getContentTypeColor = (contentType: string) => {
  switch (contentType) {
    case 'video': return '#FF6B35'
    case 'article': return '#00D9FF'
    case 'quiz': return '#FFD700'
    case 'assignment': return '#32CD32'
    case 'lab': return '#9370DB'
    case 'workshop': return '#FF69B4'
    default: return '#8B9DAF'
  }
}

export default function DynamicContentSelector({
  cohortId,
  trackId,
  onContentChange,
  initialContent = []
}: DynamicContentSelectorProps) {
  const [availableContent, setAvailableContent] = useState<AvailableContent | null>(null)
  const [selectedContent, setSelectedContent] = useState<SelectedContent[]>(initialContent)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [expandedMilestones, setExpandedMilestones] = useState<string[]>([])

  useEffect(() => {
    fetchAvailableContent()
  }, [trackId, cohortId])

  const fetchAvailableContent = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({ track_id: trackId })
      if (cohortId) {
        params.append('cohort_id', cohortId)
      }
      
      const response = await apiGateway.get(`/cohort-content/available-content/?${params}`)
      setAvailableContent(response.data)
      
      // Auto-expand first milestone
      if (response.data?.milestones?.length > 0) {
        setExpandedMilestones([response.data.milestones[0].id])
      }
    } catch (error) {
      console.error('Failed to fetch available content:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleModuleToggle = (milestone: Milestone, module: Module) => {
    const contentKey = `${milestone.id}-${module.id}`
    const isCurrentlySelected = selectedContent.some(
      item => item.milestone_id === milestone.id && item.module_id === module.id
    )

    if (isCurrentlySelected) {
      // Remove from selection
      const newSelection = selectedContent.filter(
        item => !(item.milestone_id === milestone.id && item.module_id === module.id)
      )
      setSelectedContent(newSelection)
      onContentChange?.(newSelection)
    } else {
      // Add to selection
      const newItem: SelectedContent = {
        milestone_id: milestone.id,
        module_id: module.id,
        is_required: true,
        custom_order: selectedContent.length,
        custom_duration_hours: module.estimated_hours,
      }
      const newSelection = [...selectedContent, newItem]
      setSelectedContent(newSelection)
      onContentChange?.(newSelection)
    }
  }

  const handleRequiredToggle = (milestoneId: string, moduleId: string) => {
    const newSelection = selectedContent.map(item => {
      if (item.milestone_id === milestoneId && item.module_id === moduleId) {
        return { ...item, is_required: !item.is_required }
      }
      return item
    })
    setSelectedContent(newSelection)
    onContentChange?.(newSelection)
  }

  const handleCustomDurationChange = (milestoneId: string, moduleId: string, hours: number) => {
    const newSelection = selectedContent.map(item => {
      if (item.milestone_id === milestoneId && item.module_id === moduleId) {
        return { ...item, custom_duration_hours: hours }
      }
      return item
    })
    setSelectedContent(newSelection)
    onContentChange?.(newSelection)
  }

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return

    const items = Array.from(selectedContent)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    // Update custom_order for all items
    const reorderedItems = items.map((item, index) => ({
      ...item,
      custom_order: index
    }))

    setSelectedContent(reorderedItems)
    onContentChange?.(reorderedItems)
  }

  const saveContentSelection = async () => {
    if (!cohortId) return

    try {
      setSaving(true)
      await apiGateway.post('/cohort-content/bulk-add/', {
        cohort_id: cohortId,
        content_items: selectedContent.map(item => ({
          milestone_id: item.milestone_id,
          module_id: item.module_id,
          is_required: item.is_required,
          custom_order: item.custom_order,
          custom_duration_hours: item.custom_duration_hours,
          custom_description: item.custom_description,
        }))
      })
      
      alert('Content selection saved successfully!')
    } catch (error) {
      console.error('Failed to save content selection:', error)
      alert('Failed to save content selection')
    } finally {
      setSaving(false)
    }
  }

  const getSelectedModuleData = (milestoneId: string, moduleId: string) => {
    return selectedContent.find(
      item => item.milestone_id === milestoneId && item.module_id === moduleId
    )
  }

  const isModuleSelected = (milestoneId: string, moduleId: string) => {
    return selectedContent.some(
      item => item.milestone_id === milestoneId && item.module_id === moduleId
    )
  }

  const getSelectedContentSummary = () => {
    const totalModules = selectedContent.length
    const requiredModules = selectedContent.filter(item => item.is_required).length
    const optionalModules = totalModules - requiredModules
    const totalHours = selectedContent.reduce((sum, item) => sum + (item.custom_duration_hours || 0), 0)
    
    return { totalModules, requiredModules, optionalModules, totalHours }
  }

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-och-defender"></div>
        </div>
      </Card>
    )
  }

  if (!availableContent) {
    return (
      <Card className="p-6">
        <div className="text-center text-och-steel">
          <p>No content available for this track.</p>
        </div>
      </Card>
    )
  }

  const summary = getSelectedContentSummary()

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="border-och-defender/30">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Dynamic Content Selection</h2>
              <p className="text-och-steel">
                Select and customize content from <span className="text-och-mint font-medium">{availableContent.track.name}</span>
              </p>
            </div>
            {cohortId && (
              <Button
                onClick={saveContentSelection}
                disabled={saving || selectedContent.length === 0}
                variant="defender"
              >
                {saving ? 'Saving...' : 'Save Selection'}
              </Button>
            )}
          </div>

          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-och-midnight/50 p-3 rounded-lg">
              <p className="text-och-steel text-sm">Total Modules</p>
              <p className="text-2xl font-bold text-white">{summary.totalModules}</p>
            </div>
            <div className="bg-och-midnight/50 p-3 rounded-lg">
              <p className="text-och-steel text-sm">Required</p>
              <p className="text-2xl font-bold text-och-defender">{summary.requiredModules}</p>
            </div>
            <div className="bg-och-midnight/50 p-3 rounded-lg">
              <p className="text-och-steel text-sm">Optional</p>
              <p className="text-2xl font-bold text-och-mint">{summary.optionalModules}</p>
            </div>
            <div className="bg-och-midnight/50 p-3 rounded-lg">
              <p className="text-och-steel text-sm">Total Hours</p>
              <p className="text-2xl font-bold text-och-gold">{summary.totalHours.toFixed(1)}</p>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Available Content */}
        <div className="lg:col-span-2">
          <Card>
            <div className="p-6">
              <h3 className="text-xl font-bold text-white mb-4">Available Content</h3>
              
              <div className="space-y-4">
                {availableContent.milestones.map((milestone) => (
                  <Accordion
                    key={milestone.id}
                    expanded={expandedMilestones.includes(milestone.id)}
                    onChange={(_, isExpanded) => {
                      if (isExpanded) {
                        setExpandedMilestones([...expandedMilestones, milestone.id])
                      } else {
                        setExpandedMilestones(expandedMilestones.filter(id => id !== milestone.id))
                      }
                    }}
                    sx={{
                      backgroundColor: 'rgba(10, 22, 40, 0.5)',
                      border: '1px solid rgba(139, 157, 175, 0.2)',
                      '&:before': { display: 'none' },
                    }}
                  >
                    <AccordionSummary
                      expandIcon={<ExpandMore sx={{ color: '#8B9DAF' }} />}
                      sx={{ color: '#fff' }}
                    >
                      <div className="flex items-center justify-between w-full mr-4">
                        <div>
                          <Typography variant="h6" sx={{ color: '#fff', fontWeight: 600 }}>
                            {milestone.name}
                          </Typography>
                          <Typography variant="body2" sx={{ color: '#8B9DAF' }}>
                            {milestone.modules.length} modules • {milestone.duration_weeks} weeks
                          </Typography>
                        </div>
                        <Badge variant="steel">
                          Order {milestone.order}
                        </Badge>
                      </div>
                    </AccordionSummary>
                    
                    <AccordionDetails sx={{ pt: 0 }}>
                      <div className="space-y-3">
                        {milestone.modules.map((module) => {
                          const isSelected = isModuleSelected(milestone.id, module.id)
                          const selectedData = getSelectedModuleData(milestone.id, module.id)
                          
                          return (
                            <div
                              key={module.id}
                              className={`p-4 rounded-lg border transition-all ${
                                isSelected
                                  ? 'border-och-defender/50 bg-och-defender/10'
                                  : 'border-och-steel/20 bg-och-midnight/30'
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <FormControlLabel
                                  control={
                                    <Checkbox
                                      checked={isSelected}
                                      onChange={() => handleModuleToggle(milestone, module)}
                                      sx={{ color: '#00D9FF' }}
                                    />
                                  }
                                  label=""
                                  sx={{ margin: 0 }}
                                />
                                
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-2">
                                    <div
                                      className="p-1 rounded"
                                      style={{ backgroundColor: getContentTypeColor(module.content_type) + '20' }}
                                    >
                                      {getContentTypeIcon(module.content_type)}
                                    </div>
                                    <h4 className="font-semibold text-white">{module.name}</h4>
                                    <Badge variant="steel" className="text-xs">
                                      {module.content_type}
                                    </Badge>
                                  </div>
                                  
                                  <p className="text-sm text-och-steel mb-2 line-clamp-2">
                                    {module.description}
                                  </p>
                                  
                                  <div className="flex items-center gap-4 text-xs text-och-steel">
                                    <span className="flex items-center gap-1">
                                      <Schedule fontSize="inherit" />
                                      {module.estimated_hours}h
                                    </span>
                                    <span>Order: {module.order}</span>
                                    {module.skills.length > 0 && (
                                      <div className="flex items-center gap-1">
                                        <span>Skills:</span>
                                        <div className="flex gap-1">
                                          {module.skills.slice(0, 2).map((skill, idx) => (
                                            <Chip
                                              key={idx}
                                              label={skill}
                                              size="small"
                                              sx={{
                                                height: '16px',
                                                fontSize: '10px',
                                                backgroundColor: 'rgba(0, 217, 255, 0.1)',
                                                color: '#00D9FF',
                                              }}
                                            />
                                          ))}
                                          {module.skills.length > 2 && (
                                            <Tooltip title={module.skills.slice(2).join(', ')}>
                                              <Chip
                                                label={`+${module.skills.length - 2}`}
                                                size="small"
                                                sx={{
                                                  height: '16px',
                                                  fontSize: '10px',
                                                  backgroundColor: 'rgba(139, 157, 175, 0.1)',
                                                  color: '#8B9DAF',
                                                }}
                                              />
                                            </Tooltip>
                                          )}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                  
                                  {/* Module customization options */}
                                  {isSelected && selectedData && (
                                    <div className="mt-3 pt-3 border-t border-och-steel/20 space-y-3">
                                      <div className="flex items-center gap-4">
                                        <FormControlLabel
                                          control={
                                            <Switch
                                              checked={selectedData.is_required}
                                              onChange={() => handleRequiredToggle(milestone.id, module.id)}
                                              sx={{
                                                '& .MuiSwitch-switchBase.Mui-checked': {
                                                  color: '#00D9FF',
                                                },
                                                '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                                                  backgroundColor: '#00D9FF',
                                                },
                                              }}
                                            />
                                          }
                                          label={
                                            <span className="text-sm text-white">
                                              Required for completion
                                            </span>
                                          }
                                        />
                                      </div>
                                      
                                      <div className="flex items-center gap-4">
                                        <TextField
                                          label="Custom Duration (hours)"
                                          type="number"
                                          size="small"
                                          value={selectedData.custom_duration_hours || ''}
                                          onChange={(e) => handleCustomDurationChange(
                                            milestone.id,
                                            module.id,
                                            parseFloat(e.target.value) || 0
                                          )}
                                          sx={{
                                            width: '150px',
                                            '& .MuiOutlinedInput-root': {
                                              backgroundColor: 'rgba(10, 22, 40, 0.5)',
                                              '& fieldset': { borderColor: 'rgba(139, 157, 175, 0.3)' },
                                              '&:hover fieldset': { borderColor: '#00D9FF' },
                                              '&.Mui-focused fieldset': { borderColor: '#00D9FF' },
                                            },
                                            '& .MuiInputLabel-root': { color: '#8B9DAF' },
                                            '& .MuiOutlinedInput-input': { color: '#fff' },
                                          }}
                                        />
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </div>
            </div>
          </Card>
        </div>

        {/* Selected Content Order */}
        <div>
          <Card>
            <div className="p-6">
              <h3 className="text-xl font-bold text-white mb-4">Learning Path Order</h3>
              
              {selectedContent.length === 0 ? (
                <div className="text-center py-8 text-och-steel">
                  <Info className="mx-auto mb-2" />
                  <p>No content selected yet.</p>
                  <p className="text-xs mt-1">Select modules from the left to build your learning path.</p>
                </div>
              ) : (
                <DragDropContext onDragEnd={handleDragEnd}>
                  <Droppable droppableId="selected-content">
                    {(provided) => (
                      <div
                        {...provided.droppableProps}
                        ref={provided.innerRef}
                        className="space-y-2"
                      >
                        {selectedContent
                          .sort((a, b) => a.custom_order - b.custom_order)
                          .map((item, index) => {
                            const milestone = availableContent.milestones.find(m => m.id === item.milestone_id)
                            const module = milestone?.modules.find(m => m.id === item.module_id)
                            
                            if (!milestone || !module) return null
                            
                            return (
                              <Draggable
                                key={`${item.milestone_id}-${item.module_id}`}
                                draggableId={`${item.milestone_id}-${item.module_id}`}
                                index={index}
                              >
                                {(provided, snapshot) => (
                                  <div
                                    ref={provided.innerRef}
                                    {...provided.draggableProps}
                                    className={`p-3 rounded-lg border transition-all ${
                                      snapshot.isDragging
                                        ? 'border-och-defender bg-och-defender/20 shadow-lg'
                                        : 'border-och-steel/20 bg-och-midnight/30'
                                    }`}
                                  >
                                    <div className="flex items-center gap-2">
                                      <div
                                        {...provided.dragHandleProps}
                                        className="text-och-steel hover:text-och-defender cursor-grab"
                                      >
                                        <DragIndicator fontSize="small" />
                                      </div>
                                      
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                          <Badge variant="steel" className="text-xs">
                                            {index + 1}
                                          </Badge>
                                          <div
                                            className="p-1 rounded"
                                            style={{ backgroundColor: getContentTypeColor(module.content_type) + '20' }}
                                          >
                                            {getContentTypeIcon(module.content_type)}
                                          </div>
                                        </div>
                                        
                                        <h5 className="font-medium text-white text-sm truncate">
                                          {module.name}
                                        </h5>
                                        <p className="text-xs text-och-steel truncate">
                                          {milestone.name}
                                        </p>
                                        
                                        <div className="flex items-center gap-2 mt-1">
                                          <Badge
                                            variant={item.is_required ? 'defender' : 'steel'}
                                            className="text-xs"
                                          >
                                            {item.is_required ? 'Required' : 'Optional'}
                                          </Badge>
                                          <span className="text-xs text-och-steel">
                                            {item.custom_duration_hours || module.estimated_hours}h
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </Draggable>
                            )
                          })}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </DragDropContext>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}