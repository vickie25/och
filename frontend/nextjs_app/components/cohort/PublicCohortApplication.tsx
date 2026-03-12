'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import {
  TextField,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Checkbox,
  Select,
  MenuItem,
  InputLabel,
  Chip,
  LinearProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  Person,
  Email,
  Phone,
  School,
  Work,
  Description,
  CheckCircle,
  Timer,
  Quiz,
} from '@mui/icons-material'

interface CohortInfo {
  id: string
  name: string
  track: {
    name: string
    description: string
  }
  start_date: string
  end_date: string
  mode: string
  seat_cap: number
  enrollment_count: number
  registration_form_fields: {
    student: FormField[]
    sponsor: FormField[]
  }
  review_cutoff_grade: number
  interview_cutoff_grade: number
}

interface FormField {
  key: string
  label: string
  type: string
  required: boolean
  options?: string[]
}

interface Question {
  id: string
  type: 'mcq' | 'scenario' | 'behavioral'
  difficulty: string
  topic: string
  question_text: string
  options: string[]
  scoring_weight: number
}

interface TestConfig {
  question_ids: string[]
  time_limit_minutes: number
  opens_at: string
  closes_at: string
}

const steps = ['Application', 'Assessment Test', 'Review Status']

export default function PublicCohortApplication({ cohortId }: { cohortId: string }) {
  const [cohortInfo, setCohortInfo] = useState<CohortInfo | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [applicantType, setApplicantType] = useState<'student' | 'sponsor'>('student')
  const [formData, setFormData] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [applicationId, setApplicationId] = useState<string | null>(null)
  
  // Test-related state
  const [testConfig, setTestConfig] = useState<TestConfig | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [testStarted, setTestStarted] = useState(false)
  const [testCompleted, setTestCompleted] = useState(false)
  const [testScore, setTestScore] = useState<number | null>(null)

  useEffect(() => {
    fetchCohortInfo()
  }, [cohortId])

  useEffect(() => {
    let timer: NodeJS.Timeout
    if (testStarted && timeRemaining > 0 && !testCompleted) {
      timer = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            handleTestSubmit()
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }
    return () => clearInterval(timer)
  }, [testStarted, timeRemaining, testCompleted])

  const fetchCohortInfo = async () => {
    try {
      setLoading(true)
      const response = await apiGateway.get(`/cohorts/${cohortId}/public-info/`)
      setCohortInfo(response.data)
    } catch (error) {
      console.error('Failed to fetch cohort info:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFormChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleApplicationSubmit = async () => {
    try {
      setSubmitting(true)
      const response = await apiGateway.post('/cohort-applications/', {
        cohort_id: cohortId,
        applicant_type: applicantType,
        form_data: formData,
      })
      
      setApplicationId(response.data.id)
      setCurrentStep(1)
      
      // Fetch test configuration
      await fetchTestConfig()
    } catch (error) {
      console.error('Failed to submit application:', error)
      alert('Failed to submit application. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const fetchTestConfig = async () => {
    try {
      const response = await apiGateway.get(`/cohorts/${cohortId}/test-config/`)
      setTestConfig(response.data)
    } catch (error) {
      console.error('Failed to fetch test config:', error)
    }
  }

  const startTest = async () => {
    if (!testConfig) return

    try {
      setLoading(true)
      const response = await apiGateway.get(`/application-test/questions/`, {
        params: { question_ids: testConfig.question_ids.join(',') }
      })
      
      setQuestions(response.data)
      setTimeRemaining(testConfig.time_limit_minutes * 60)
      setTestStarted(true)
      setCurrentQuestionIndex(0)
    } catch (error) {
      console.error('Failed to start test:', error)
      alert('Failed to start test. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswerSelect = (questionId: string, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }))
  }

  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1)
    }
  }

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1)
    }
  }

  const handleTestSubmit = async () => {
    try {
      setSubmitting(true)
      const response = await apiGateway.post('/application-test/submit/', {
        application_id: applicationId,
        answers: answers,
        time_taken_seconds: (testConfig!.time_limit_minutes * 60) - timeRemaining,
      })
      
      setTestScore(response.data.score)
      setTestCompleted(true)
      setCurrentStep(2)
    } catch (error) {
      console.error('Failed to submit test:', error)
      alert('Failed to submit test. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const renderFormField = (field: FormField) => {
    const value = formData[field.key] || ''

    switch (field.type) {
      case 'text':
      case 'email':
      case 'phone':
        return (
          <TextField
            key={field.key}
            label={field.label}
            type={field.type}
            required={field.required}
            value={value}
            onChange={(e) => handleFormChange(field.key, e.target.value)}
            fullWidth
            sx={{
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
        )

      case 'textarea':
        return (
          <TextField
            key={field.key}
            label={field.label}
            required={field.required}
            value={value}
            onChange={(e) => handleFormChange(field.key, e.target.value)}
            multiline
            rows={4}
            fullWidth
            sx={{
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
        )

      case 'select':
        return (
          <FormControl key={field.key} fullWidth required={field.required}>
            <InputLabel sx={{ color: '#8B9DAF' }}>{field.label}</InputLabel>
            <Select
              value={value}
              onChange={(e) => handleFormChange(field.key, e.target.value)}
              sx={{
                backgroundColor: 'rgba(10, 22, 40, 0.5)',
                '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(139, 157, 175, 0.3)' },
                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#00D9FF' },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#00D9FF' },
                '& .MuiSelect-select': { color: '#fff' },
              }}
            >
              {field.options?.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )

      case 'checkbox':
        return (
          <FormControlLabel
            key={field.key}
            control={
              <Checkbox
                checked={value || false}
                onChange={(e) => handleFormChange(field.key, e.target.checked)}
                sx={{ color: '#00D9FF' }}
              />
            }
            label={<span className="text-white">{field.label}</span>}
          />
        )

      default:
        return null
    }
  }

  if (loading && !cohortInfo) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-och-defender"></div>
      </div>
    )
  }

  if (!cohortInfo) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <Card className="p-8 text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Cohort Not Found</h1>
          <p className="text-och-steel">The requested cohort could not be found or is not accepting applications.</p>
        </Card>
      </div>
    )
  }

  const currentQuestion = questions[currentQuestionIndex]
  const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0

  return (
    <div className="min-h-screen bg-och-midnight py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <Card className="mb-8 border-och-defender/30">
          <div className="p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 bg-och-defender/20 rounded-lg flex items-center justify-center">
                <School className="w-8 h-8 text-och-defender" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">{cohortInfo.name}</h1>
                <p className="text-och-mint text-lg">{cohortInfo.track.name}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-och-steel">Start Date:</span>
                <span className="ml-2 text-white">{new Date(cohortInfo.start_date).toLocaleDateString()}</span>
              </div>
              <div>
                <span className="text-och-steel">Mode:</span>
                <span className="ml-2 text-white capitalize">{cohortInfo.mode}</span>
              </div>
              <div>
                <span className="text-och-steel">Seats Available:</span>
                <span className="ml-2 text-white">{cohortInfo.seat_cap - cohortInfo.enrollment_count}</span>
              </div>
              <div>
                <span className="text-och-steel">Duration:</span>
                <span className="ml-2 text-white">
                  {Math.ceil((new Date(cohortInfo.end_date).getTime() - new Date(cohortInfo.start_date).getTime()) / (1000 * 60 * 60 * 24 * 7))} weeks
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Progress Stepper */}
        <Card className="mb-8">
          <div className="p-6">
            <Stepper activeStep={currentStep} alternativeLabel>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel sx={{
                    '& .MuiStepLabel-label': { color: '#8B9DAF' },
                    '& .MuiStepLabel-label.Mui-active': { color: '#00D9FF' },
                    '& .MuiStepLabel-label.Mui-completed': { color: '#00D9FF' },
                  }}>
                    {label}
                  </StepLabel>
                </Step>
              ))}
            </Stepper>
          </div>
        </Card>

        {/* Step Content */}
        {currentStep === 0 && (
          <Card>
            <div className="p-6">
              <h2 className="text-2xl font-bold text-white mb-6">Application Form</h2>
              
              {/* Applicant Type Selection */}
              <div className="mb-6">
                <FormControl component="fieldset">
                  <FormLabel component="legend" sx={{ color: '#fff', mb: 2 }}>
                    I am applying as a:
                  </FormLabel>
                  <RadioGroup
                    value={applicantType}
                    onChange={(e) => setApplicantType(e.target.value as 'student' | 'sponsor')}
                    row
                  >
                    <FormControlLabel
                      value="student"
                      control={<Radio sx={{ color: '#00D9FF' }} />}
                      label={<span className="text-white">Student</span>}
                    />
                    <FormControlLabel
                      value="sponsor"
                      control={<Radio sx={{ color: '#00D9FF' }} />}
                      label={<span className="text-white">Sponsor/Organization</span>}
                    />
                  </RadioGroup>
                </FormControl>
              </div>

              {/* Dynamic Form Fields */}
              <div className="space-y-4">
                {cohortInfo.registration_form_fields[applicantType]?.map(renderFormField)}
              </div>

              {/* Terms and Conditions */}
              <div className="mt-6 p-4 bg-och-midnight/50 rounded-lg">
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.terms_accepted || false}
                      onChange={(e) => handleFormChange('terms_accepted', e.target.checked)}
                      sx={{ color: '#00D9FF' }}
                    />
                  }
                  label={
                    <span className="text-white text-sm">
                      I agree to the terms and conditions and understand that this application will be reviewed.
                      {cohortInfo.review_cutoff_grade && (
                        <span className="block text-och-steel mt-1">
                          Minimum review score required: {cohortInfo.review_cutoff_grade}%
                        </span>
                      )}
                    </span>
                  }
                />
              </div>

              <div className="flex justify-end mt-6">
                <Button
                  onClick={handleApplicationSubmit}
                  disabled={submitting || !formData.terms_accepted}
                  variant="defender"
                  size="lg"
                >
                  {submitting ? 'Submitting...' : 'Submit Application'}
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Assessment Test Step */}
        {currentStep === 1 && (
          <Card>
            <div className="p-6">
              {!testStarted ? (
                <div className="text-center">
                  <Quiz className="w-16 h-16 text-och-defender mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-white mb-4">Assessment Test</h2>
                  <p className="text-och-steel mb-6">
                    Complete the assessment test to proceed with your application.
                  </p>
                  
                  {testConfig && (
                    <div className="bg-och-midnight/50 p-4 rounded-lg mb-6 text-left max-w-md mx-auto">
                      <h3 className="font-semibold text-white mb-2">Test Information:</h3>
                      <ul className="text-sm text-och-steel space-y-1">
                        <li>• {testConfig.question_ids.length} questions</li>
                        <li>• {testConfig.time_limit_minutes} minutes time limit</li>
                        <li>• Multiple choice and scenario-based questions</li>
                        <li>• You can navigate between questions</li>
                      </ul>
                    </div>
                  )}
                  
                  <Button
                    onClick={startTest}
                    disabled={loading}
                    variant="defender"
                    size="lg"
                  >
                    {loading ? 'Loading Test...' : 'Start Assessment'}
                  </Button>
                </div>
              ) : testCompleted ? (
                <div className="text-center">
                  <CheckCircle className="w-16 h-16 text-och-mint mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-white mb-4">Test Completed!</h2>
                  <p className="text-och-steel mb-4">
                    Your assessment has been submitted successfully.
                  </p>
                  {testScore !== null && (
                    <div className="bg-och-midnight/50 p-4 rounded-lg mb-6 max-w-md mx-auto">
                      <p className="text-white">
                        Your Score: <span className="font-bold text-och-mint">{testScore}%</span>
                      </p>
                      {cohortInfo.review_cutoff_grade && (
                        <p className="text-sm text-och-steel mt-2">
                          Required minimum: {cohortInfo.review_cutoff_grade}%
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  {/* Test Header */}
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-bold text-white">
                        Question {currentQuestionIndex + 1} of {questions.length}
                      </h2>
                      <LinearProgress
                        variant="determinate"
                        value={progress}
                        sx={{
                          width: '200px',
                          mt: 1,
                          backgroundColor: 'rgba(139, 157, 175, 0.2)',
                          '& .MuiLinearProgress-bar': { backgroundColor: '#00D9FF' },
                        }}
                      />
                    </div>
                    
                    <div className="flex items-center gap-2 text-white">
                      <Timer />
                      <span className={`font-mono text-lg ${timeRemaining < 300 ? 'text-och-orange' : ''}`}>
                        {formatTime(timeRemaining)}
                      </span>
                    </div>
                  </div>

                  {/* Question */}
                  {currentQuestion && (
                    <div className="mb-6">
                      <div className="flex items-center gap-2 mb-4">
                        <Badge variant="defender">{currentQuestion.type.toUpperCase()}</Badge>
                        <Badge variant="steel">{currentQuestion.difficulty}</Badge>
                        <Badge variant="gold">{currentQuestion.topic}</Badge>
                      </div>
                      
                      <h3 className="text-lg font-semibold text-white mb-4">
                        {currentQuestion.question_text}
                      </h3>
                      
                      <div className="space-y-3">
                        {currentQuestion.options.map((option, index) => (
                          <FormControlLabel
                            key={index}
                            control={
                              <Radio
                                checked={answers[currentQuestion.id] === option}
                                onChange={() => handleAnswerSelect(currentQuestion.id, option)}
                                sx={{ color: '#00D9FF' }}
                              />
                            }
                            label={<span className="text-white">{option}</span>}
                            className="block p-3 rounded-lg border border-och-steel/20 hover:border-och-defender/50 transition-colors"
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Navigation */}
                  <div className="flex justify-between">
                    <Button
                      onClick={previousQuestion}
                      disabled={currentQuestionIndex === 0}
                      variant="outline"
                    >
                      Previous
                    </Button>
                    
                    <div className="flex gap-2">
                      {currentQuestionIndex === questions.length - 1 ? (
                        <Button
                          onClick={handleTestSubmit}
                          disabled={submitting}
                          variant="defender"
                        >
                          {submitting ? 'Submitting...' : 'Submit Test'}
                        </Button>
                      ) : (
                        <Button
                          onClick={nextQuestion}
                          variant="defender"
                        >
                          Next
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Review Status Step */}
        {currentStep === 2 && (
          <Card>
            <div className="p-6 text-center">
              <CheckCircle className="w-16 h-16 text-och-mint mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-4">Application Under Review</h2>
              <p className="text-och-steel mb-6">
                Thank you for completing your application and assessment. Our team will review your submission and contact you within 3-5 business days.
              </p>
              
              <div className="bg-och-midnight/50 p-4 rounded-lg max-w-md mx-auto">
                <h3 className="font-semibold text-white mb-2">Next Steps:</h3>
                <ul className="text-sm text-och-steel text-left space-y-1">
                  <li>1. Application review by our team</li>
                  <li>2. Interview invitation (if selected)</li>
                  <li>3. Final enrollment decision</li>
                  <li>4. Payment and onboarding (if accepted)</li>
                </ul>
              </div>
              
              <p className="text-xs text-och-steel mt-4">
                Application ID: {applicationId}
              </p>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}