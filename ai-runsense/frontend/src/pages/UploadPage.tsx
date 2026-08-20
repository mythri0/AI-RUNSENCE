import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, Film, CheckCircle, AlertTriangle, ArrowRight, ArrowLeft, Info } from 'lucide-react'
import { createRun, uploadVideo, startAnalysis, type RunContext } from '../api/client'

const TIPS = [
  '📹 Keep your entire body visible throughout the recording',
  '📐 Side-view footage provides the best stride analysis',
  '💡 Use good lighting — avoid strong backlight',
  '🎥 A stable camera (tripod or fixed position) gives best results',
  '⏱ At least 15 seconds of continuous running is recommended',
]

export default function UploadPage() {
  const nav = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [stage, setStage] = useState<'idle' | 'uploading' | 'starting' | 'done' | 'error'>('idle')
  const [error, setError] = useState('')

  const onDrop = useCallback((accepted: File[]) => {
    if (!accepted[0]) return
    setFile(accepted[0])
    setPreviewUrl(URL.createObjectURL(accepted[0]))
    setStage('idle')
    setError('')
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.mov', '.avi', '.webm', '.mkv'] },
    maxFiles: 1,
  })

  const handleAnalyze = async () => {
    const runnerId = Number(localStorage.getItem('runner_id'))
    if (!runnerId) { setError('Runner profile not found. Please create a profile first.'); return }
    if (!file) { setError('Please select a video file.'); return }

    const ctx: RunContext = JSON.parse(localStorage.getItem('run_context') || '{}')

    setError('')
    setStage('uploading')
    setUploadProgress(0)

    try {
      // 1. Create session
      const runRes = await createRun({ runner_id: runnerId, ...ctx })
      const runId = (runRes.data as { id: number }).id
      localStorage.setItem('current_run_id', String(runId))

      // 2. Upload video
      await uploadVideo(runId, file, pct => setUploadProgress(pct))

      // 3. Start analysis
      setStage('starting')
      await startAnalysis(runId)

      setStage('done')
      setTimeout(() => nav(`/analysis/${runId}`), 800)
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Upload failed. Check that the backend is running.'
      setError(msg)
      setStage('error')
    }
  }

  const fmt = (bytes: number) => bytes > 1e6 ? `${(bytes / 1e6).toFixed(1)} MB` : `${(bytes / 1e3).toFixed(0)} KB`

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', background: 'var(--bg-primary)' }}>
      <div style={{ maxWidth: '640px', width: '100%' }}>
        <button onClick={() => nav('/context')} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '2rem', fontSize: '0.85rem' }}>
          <ArrowLeft size={16} /> Back
        </button>

        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>Upload Your Run Video</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>Step 3 of 3 — The analysis begins as soon as your video is uploaded</p>

        {/* Tips */}
        <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.25rem', borderColor: 'var(--accent-teal-border)', background: 'var(--accent-teal-bg)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <Info size={16} color="var(--accent-teal)" />
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--accent-teal-dark)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recording Tips</span>
          </div>
          {TIPS.map(t => <p key={t} style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>{t}</p>)}
        </div>

        {/* Drop zone */}
        <div {...getRootProps()} style={{ border: `2px dashed ${isDragActive ? 'var(--accent-teal)' : file ? 'var(--accent-green)' : 'var(--border-bright)'}`, borderRadius: '16px', padding: '2.5rem', textAlign: 'center', cursor: 'pointer', background: isDragActive ? 'var(--accent-teal-bg)' : file ? 'rgba(5,150,105,0.04)' : '#fff', transition: 'all 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
          <input {...getInputProps()} />
          {file ? (
            <div>
              <CheckCircle size={40} color="var(--accent-green)" style={{ margin: '0 auto 0.75rem' }} />
              <p style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>{file.name}</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{fmt(file.size)} · {file.type || 'video'}</p>
            </div>
          ) : (
            <div>
              <Upload size={40} color="var(--accent-teal)" style={{ margin: '0 auto 0.75rem' }} />
              <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>{isDragActive ? 'Drop your video here…' : 'Drag & drop or click to select'}</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>MP4, MOV, AVI, WebM, MKV · Max 500 MB</p>
            </div>
          )}
        </div>

        {/* Preview */}
        {previewUrl && (
          <div style={{ marginTop: '1rem' }}>
            <video src={previewUrl} controls style={{ width: '100%', borderRadius: '12px', maxHeight: '300px', background: '#000' }} />
          </div>
        )}

        {/* Progress */}
        {stage === 'uploading' && (
          <div style={{ marginTop: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              <span>Uploading video…</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="progress-bar"><div className="progress-fill" style={{ width: `${uploadProgress}%` }} /></div>
          </div>
        )}

        {stage === 'starting' && (
          <div style={{ marginTop: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            <div className="spinner" /> Starting analysis pipeline…
          </div>
        )}

        {stage === 'done' && (
          <div style={{ marginTop: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--accent-green)', fontSize: '0.9rem' }}>
            <CheckCircle size={20} /> Redirecting to analysis…
          </div>
        )}

        {error && (
          <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'flex-start', gap: '0.5rem', color: '#dc2626', fontSize: '0.85rem', background: 'rgba(220,38,38,0.06)', border: '1px solid rgba(220,38,38,0.15)', borderRadius: '8px', padding: '0.75rem 1rem' }}>
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '1px' }} /> {error}
          </div>
        )}

        <button className="btn-primary" onClick={handleAnalyze} disabled={!file || stage === 'uploading' || stage === 'starting' || stage === 'done'}
          style={{ width: '100%', marginTop: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '1rem' }}>
          {stage === 'idle' || stage === 'error' ? <><Film size={18} /> Analyze My Run <ArrowRight size={18} /></>
            : stage === 'uploading' ? <><div className="spinner" style={{ width: 18, height: 18 }} /> Uploading…</>
            : stage === 'starting' ? <><div className="spinner" style={{ width: 18, height: 18 }} /> Starting…</>
            : <><CheckCircle size={18} /> Done!</>}
        </button>
      </div>
    </div>
  )
}
