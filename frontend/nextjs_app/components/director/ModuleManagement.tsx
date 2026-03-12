'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Edit3, 
  Trash2, 
  Save, 
  X, 
  GripVertical,
  Upload,
  Calendar,
  Clock,
  BookOpen,
  Video,
  FileText,
  Target,
  Lab,
  Award
} from 'lucide-react';
import { apiGateway } from '@/services/apiGateway';

interface ModuleManagementProps {
  cohortId: string;
  cohortName: string;
  onClose: () => void;
}

interface Module {
  id: string;
  day_number: number;
  title: string;
  description: string;
  material_type: 'video' | 'article' | 'quiz' | 'assignment' | 'lab' | 'workshop';
  content_url: string;
  content_text: string;
  order: number;
  estimated_minutes: number;
  is_required: boolean;
  unlock_date?: string;
  created_at: string;
  updated_at: string;
}

interface ModuleFormData {
  day_number: number;
  title: string;
  description: string;
  material_type: string;
  content_url: string;
  content_text: string;
  estimated_minutes: number;
  is_required: boolean;
  unlock_date: string;
}

const MATERIAL_TYPES = [
  { value: 'video', label: 'Video', icon: Video },
  { value: 'article', label: 'Article', icon: FileText },
  { value: 'quiz', label: 'Quiz', icon: Target },
  { value: 'assignment', label: 'Assignment', icon: BookOpen },
  { value: 'lab', label: 'Lab', icon: Lab },
  { value: 'workshop', label: 'Workshop', icon: Award }
];

export function ModuleManagement({ cohortId, cohortName, onClose }: ModuleManagementProps) {
  const [modules, setModules] = useState<Module[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingModule, setEditingModule] = useState<Module | null>(null);
  const [selectedDay, setSelectedDay] = useState<number>(1);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState<ModuleFormData>({
    day_number: 1,
    title: '',
    description: '',
    material_type: 'video',
    content_url: '',
    content_text: '',
    estimated_minutes: 30,
    is_required: true,
    unlock_date: ''
  });

  useEffect(() => {
    fetchModules();
  }, [cohortId]);

  const fetchModules = async () => {
    try {
      setIsLoading(true);
      const response = await apiGateway.get(`/cohorts/${cohortId}/modules/`);
      setModules(response.modules || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load modules');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddModule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiGateway.post(`/cohorts/${cohortId}/modules/`, formData);
      setSuccess('Module added successfully!');
      setShowAddForm(false);
      resetForm();
      fetchModules();
    } catch (err: any) {
      setError(err.message || 'Failed to add module');
    }
  };

  const handleUpdateModule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingModule) return;

    try {
      await apiGateway.put(`/cohorts/${cohortId}/modules/${editingModule.id}/`, formData);
      setSuccess('Module updated successfully!');
      setEditingModule(null);
      resetForm();
      fetchModules();
    } catch (err: any) {
      setError(err.message || 'Failed to update module');
    }
  };

  const handleDeleteModule = async (moduleId: string) => {
    if (!confirm('Are you sure you want to delete this module?')) return;

    try {
      await apiGateway.delete(`/cohorts/${cohortId}/modules/${moduleId}/`);
      setSuccess('Module deleted successfully!');
      fetchModules();
    } catch (err: any) {
      setError(err.message || 'Failed to delete module');
    }
  };

  const handleImportFromTrack = async () => {
    try {
      const response = await apiGateway.post(`/cohorts/${cohortId}/modules/import-track/`, {
        start_day: selectedDay
      });
      setSuccess(`Imported ${response.imported_count} modules from track!`);
      fetchModules();
    } catch (err: any) {
      setError(err.message || 'Failed to import modules');
    }
  };

  const resetForm = () => {
    setFormData({
      day_number: selectedDay,
      title: '',
      description: '',
      material_type: 'video',
      content_url: '',
      content_text: '',
      estimated_minutes: 30,
      is_required: true,
      unlock_date: ''
    });
  };

  const startEdit = (module: Module) => {
    setEditingModule(module);
    setFormData({
      day_number: module.day_number,
      title: module.title,
      description: module.description,
      material_type: module.material_type,
      content_url: module.content_url,
      content_text: module.content_text,
      estimated_minutes: module.estimated_minutes,
      is_required: module.is_required,
      unlock_date: module.unlock_date || ''
    });
    setShowAddForm(true);
  };

  const cancelEdit = () => {
    setEditingModule(null);
    setShowAddForm(false);
    resetForm();
  };

  const getMaterialIcon = (type: string) => {
    const materialType = MATERIAL_TYPES.find(t => t.value === type);
    const Icon = materialType?.icon || BookOpen;
    return <Icon className="w-5 h-5" />;
  };

  // Group modules by day
  const modulesByDay = modules.reduce((acc, module) => {
    if (!acc[module.day_number]) {
      acc[module.day_number] = [];
    }
    acc[module.day_number].push(module);
    return acc;
  }, {} as Record<number, Module[]>);

  const dayNumbers = Object.keys(modulesByDay).map(Number).sort((a, b) => a - b);

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-och-midnight border border-och-steel/20 rounded-2xl p-8 text-center">
          <div className="w-16 h-16 border-4 border-och-gold/30 border-t-och-gold rounded-full animate-spin mx-auto mb-4" />
          <p className="text-och-steel font-black uppercase tracking-widest text-sm">Loading Modules...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 overflow-y-auto">
      <div className="min-h-screen p-4 flex items-start justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="w-full max-w-6xl bg-och-midnight border border-och-steel/20 rounded-2xl shadow-2xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-och-steel/10">
            <div>
              <h2 className="text-2xl font-black text-white uppercase tracking-tighter">
                Module Management
              </h2>
              <p className="text-och-steel">{cohortName}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-och-steel hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Alerts */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mx-6 mt-4 p-4 bg-red-500/10 border border-red-400/30 rounded-xl text-red-300"
              >
                {error}
                <button onClick={() => setError(null)} className="float-right">
                  <X className="w-4 h-4" />
                </button>
              </motion.div>
            )}
            {success && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mx-6 mt-4 p-4 bg-emerald-500/10 border border-emerald-400/30 rounded-xl text-emerald-300"
              >
                {success}
                <button onClick={() => setSuccess(null)} className="float-right">
                  <X className="w-4 h-4" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="p-6">
            {/* Action Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setShowAddForm(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-och-gold text-black font-black uppercase tracking-widest rounded-xl hover:bg-och-gold/90 transition-all"
                >
                  <Plus className="w-4 h-4" />
                  Add Module
                </button>
                
                <button
                  onClick={handleImportFromTrack}
                  className="flex items-center gap-2 px-4 py-2 bg-och-mint/20 text-och-mint border border-och-mint/30 font-bold rounded-xl hover:bg-och-mint/30 transition-all"
                >
                  <Upload className="w-4 h-4" />
                  Import from Track
                </button>
              </div>

              <div className="flex items-center gap-2">
                <label className="text-sm font-bold text-och-steel">Day:</label>
                <select
                  value={selectedDay}
                  onChange={(e) => setSelectedDay(Number(e.target.value))}
                  className="px-3 py-2 bg-och-midnight/80 border border-och-steel/20 rounded-lg text-white"
                >
                  {Array.from({ length: 30 }, (_, i) => i + 1).map(day => (
                    <option key={day} value={day}>Day {day}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Add/Edit Form */}
            <AnimatePresence>
              {showAddForm && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-6 p-6 bg-och-midnight/60 border border-och-steel/10 rounded-2xl"
                >
                  <h3 className="text-lg font-black text-white uppercase tracking-tighter mb-4">
                    {editingModule ? 'Edit Module' : 'Add New Module'}
                  </h3>
                  
                  <form onSubmit={editingModule ? handleUpdateModule : handleAddModule} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-bold text-white mb-2">Day Number</label>
                        <input
                          type="number"
                          min="1"
                          max="365"
                          value={formData.day_number}
                          onChange={(e) => setFormData(prev => ({ ...prev, day_number: Number(e.target.value) }))}
                          className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-white mb-2">Material Type</label>
                        <select
                          value={formData.material_type}
                          onChange={(e) => setFormData(prev => ({ ...prev, material_type: e.target.value }))}
                          className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white"
                        >
                          {MATERIAL_TYPES.map(type => (
                            <option key={type.value} value={type.value}>{type.label}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">Title</label>
                      <input
                        type="text"
                        value={formData.title}
                        onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">Description</label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        rows={3}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-bold text-white mb-2">Content URL</label>
                        <input
                          type="url"
                          value={formData.content_url}
                          onChange={(e) => setFormData(prev => ({ ...prev, content_url: e.target.value }))}
                          className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white"
                          placeholder="https://..."
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-white mb-2">Estimated Minutes</label>
                        <input
                          type="number"
                          min="1"
                          value={formData.estimated_minutes}
                          onChange={(e) => setFormData(prev => ({ ...prev, estimated_minutes: Number(e.target.value) }))}
                          className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-bold text-white mb-2">Unlock Date (Optional)</label>
                        <input
                          type="date"
                          value={formData.unlock_date}
                          onChange={(e) => setFormData(prev => ({ ...prev, unlock_date: e.target.value }))}
                          className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white"
                        />
                      </div>

                      <div className="flex items-center gap-4 pt-8">
                        <label className="flex items-center gap-2 text-white">
                          <input
                            type="checkbox"
                            checked={formData.is_required}
                            onChange={(e) => setFormData(prev => ({ ...prev, is_required: e.target.checked }))}
                            className="w-4 h-4 text-och-gold bg-och-midnight border-och-steel/20 rounded focus:ring-och-gold"
                          />
                          Required Module
                        </label>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 pt-4">
                      <button
                        type="submit"
                        className="flex items-center gap-2 px-6 py-3 bg-och-gold text-black font-black uppercase tracking-widest rounded-xl hover:bg-och-gold/90 transition-all"
                      >
                        <Save className="w-4 h-4" />
                        {editingModule ? 'Update Module' : 'Add Module'}
                      </button>
                      
                      <button
                        type="button"
                        onClick={cancelEdit}
                        className="px-6 py-3 bg-och-steel/20 text-och-steel font-bold rounded-xl hover:bg-och-steel/30 transition-all"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Modules List */}
            <div className="space-y-6">
              {dayNumbers.length === 0 ? (
                <div className="text-center py-12">
                  <BookOpen className="w-16 h-16 text-och-steel/30 mx-auto mb-4" />
                  <h3 className="text-xl font-black text-white uppercase tracking-tighter mb-2">
                    No Modules Yet
                  </h3>
                  <p className="text-och-steel mb-6">Start by adding your first module or importing from track.</p>
                </div>
              ) : (
                dayNumbers.map(dayNumber => (
                  <div key={dayNumber} className="bg-och-midnight/60 border border-och-steel/10 rounded-2xl p-6">
                    <h3 className="text-lg font-black text-white uppercase tracking-tighter mb-4 flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-och-gold" />
                      Day {dayNumber}
                      <span className="text-sm font-normal text-och-steel">
                        ({modulesByDay[dayNumber].length} modules)
                      </span>
                    </h3>
                    
                    <div className="space-y-3">
                      {modulesByDay[dayNumber]
                        .sort((a, b) => a.order - b.order)
                        .map((module) => (
                          <motion.div
                            key={module.id}
                            layout
                            className="flex items-center gap-4 p-4 bg-och-steel/5 border border-och-steel/10 rounded-xl hover:bg-och-steel/10 transition-all"
                          >
                            <div className="cursor-move text-och-steel">
                              <GripVertical className="w-5 h-5" />
                            </div>
                            
                            <div className="flex items-center gap-3 text-och-gold">
                              {getMaterialIcon(module.material_type)}
                            </div>
                            
                            <div className="flex-1">
                              <h4 className="font-bold text-white">{module.title}</h4>
                              <div className="flex items-center gap-4 text-sm text-och-steel">
                                <span className="flex items-center gap-1">
                                  <Clock className="w-4 h-4" />
                                  {module.estimated_minutes}min
                                </span>
                                <span className="capitalize">{module.material_type}</span>
                                {module.is_required && (
                                  <span className="px-2 py-1 bg-och-defender/20 text-och-defender text-xs rounded-lg font-bold">
                                    Required
                                  </span>
                                )}
                                {module.unlock_date && (
                                  <span className="px-2 py-1 bg-och-mint/20 text-och-mint text-xs rounded-lg font-bold">
                                    Unlocks: {new Date(module.unlock_date).toLocaleDateString()}
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => startEdit(module)}
                                className="p-2 text-och-steel hover:text-och-gold transition-colors"
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteModule(module.id)}
                                className="p-2 text-och-steel hover:text-red-400 transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </motion.div>
                        ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}