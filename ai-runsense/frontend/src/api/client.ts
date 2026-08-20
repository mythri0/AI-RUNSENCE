// Central API client — all calls go through here
import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Types ──────────────────────────────────────────────────────────────────

export interface RunnerProfile {
  id?: number
  email?: string
  name?: string
  age?: number
  weight_kg?: number
  height_cm?: number
  gender?: string
  experience_level?: string
  primary_goal?: string
  bmi?: number
}

export interface RunContext {
  distance_type?: string
  environment?: string
  session_goal?: string
}

export interface RunStatus {
  id: number
  status: string
  processing_stage?: string
  processing_progress: number
  error_message?: string
}

export interface MetricValue {
  value: number | null
  unit: string
  label: string
  estimated: boolean
  confidence: number
  note?: string
}

export interface WindowData {
  window_index: number
  time_pct_start: number
  time_pct_end: number
  time_s_start: number
  time_s_end: number
  cadence_spm?: number
  symmetry_index?: number
  vertical_oscillation_norm?: number
  stride_consistency?: number
  trunk_lean_mean?: number
  arm_swing_mean?: number
}

export interface Metrics {
  cadence?: MetricValue
  stride_normalized?: MetricValue
  vertical_oscillation?: MetricValue
  symmetry_index?: MetricValue
  trunk_lean?: MetricValue
  knee_angle_left?: MetricValue
  knee_angle_right?: MetricValue
  arm_swing?: MetricValue
  ground_contact_estimate?: MetricValue
  foot_strike?: { classification?: string; label?: string; confidence?: number; note?: string }
  pelvic_stability?: MetricValue
  rhythm_score?: MetricValue
  windows?: WindowData[]
}

export interface Mistake {
  id: string
  name: string
  severity: 'high' | 'medium' | 'low'
  confidence: number
  evidence: string
  timestamp_s?: number
  frame_number?: number
  relevant_metrics: Record<string, unknown>
  possible_effect: string
  suggested_correction: string
  highlight_joints: string[]
}

export interface Priority {
  rank: number
  name: string
  severity: string
  confidence: number
  priority_score: number
  evidence: string
  timestamp_s?: number
  frame_number?: number
  relevant_metrics: Record<string, unknown>
  possible_effect: string
  suggested_correction: string
  selected_reason: string
  focus_tip: string
  highlight_joints: string[]
  id: string
}

export interface TimelinePoint {
  window_index: number
  time_pct: number
  timestamp_s: number
  form_quality: 'good' | 'fair' | 'poor' | 'degrading'
  color: 'green' | 'yellow' | 'orange' | 'red'
  notes: string[]
  is_baseline: boolean
}

export interface StyleDNA {
  cadence: number
  stride: number
  posture: number
  symmetry: number
  arm_swing: number
  pelvic_stability: number
  rhythm: number
  vertical: number
  primary_style: string
  secondary_style?: string
  evidence: string[]
  confidence: number
}

export interface FatigueReport {
  detected: boolean
  confidence: number
  onset_time_s?: number
  onset_window_index?: number
  drifting_metrics: Array<{ name: string; direction: string; slope_pct_per_window: number; early_value?: number; late_value?: number; significance: number }>
  stable_metrics: Array<{ name: string; direction: string }>
  summary: string
  notes: string[]
}

export interface LoadingIndex {
  index: number
  level: string
  contributors: Array<{ name: string; contribution: number; explanation: string }>
  mass_included: boolean
  disclaimer: string
}

export interface EfficiencyScore {
  overall: number
  components: Record<string, number>
}

export interface Coach {
  doing_well: string[]
  what_changed: string[]
  why_it_matters: string[]
  top_priority: string
  focus_next: string[]
  context_recommendation: string
  generated_by: string
}

export interface GaitCycle {
  index: number
  start_frame: number
  end_frame: number
  start_time_s: number
  end_time_s: number
  duration_s: number
  confidence: number
}

export interface FullAnalysis {
  run_id: number
  status: string
  processing_stage?: string
  processing_progress: number
  error_message?: string
  created_at?: string
  video_duration_s?: number
  video_fps?: number
  distance_type?: string
  environment?: string
  session_goal?: string
  metrics: Metrics
  baseline: Record<string, unknown>
  mistakes: Mistake[]
  fatigue: FatigueReport
  style: StyleDNA
  priorities: Priority[]
  coach: Coach
  timeline: TimelinePoint[]
  loading_index: LoadingIndex
  efficiency: EfficiencyScore
  gait_cycles: GaitCycle[]
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const createProfile = (data: RunnerProfile) => api.post<RunnerProfile>('/profile', data)
export const updateProfile = (runnerId: string | number, data: RunnerProfile) => api.put<RunnerProfile>(`/profile/${runnerId}`, data)
export const getProfile = (runnerId: string | number) => api.get<RunnerProfile>(`/profile/${runnerId}`)

export const createRun = (data: { runner_id: number } & RunContext) => api.post<{ id: number }>('/runs', data)
export const uploadVideo = (runId: number, file: File, onProgress?: (pct: number) => void) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/runs/${runId}/video`, form, {
    onUploadProgress: (e) => { if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100)) },
    timeout: 300000,
  })
}
export const startAnalysis = (runId: number) => api.post(`/runs/${runId}/analyze`)
export const getRunStatus = (runId: number) => api.get<RunStatus>(`/runs/${runId}/status`)
export const getFullAnalysis = (runId: number) => api.get<FullAnalysis>(`/runs/${runId}/full`)
export const getRunnerRuns = (runnerId: number) => api.get(`/runner/${runnerId}/runs`)
export const getEvolution = (runnerId: number) => api.get(`/runner/${runnerId}/evolution`)

export const videoUrl = (runId: number, mode: 'original' | 'pose' | 'analysis') => {
  return `/api/runs/${runId}/video?mode=${mode}`
}

export default api
