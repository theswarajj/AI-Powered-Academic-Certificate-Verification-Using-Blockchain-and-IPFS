import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { io } from 'socket.io-client'
import toast from 'react-hot-toast'
import {
  ShieldCheck,
  QrCode,
  Loader2,
  FileText,
  UploadCloud,
  X,
  ArrowRight,
  Search,
} from 'lucide-react'
import { useVerificationStore } from '@/lib/store'
import LayerProgress from '@/components/verification/LayerProgress'

export default function Verify() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [certId, setCertId] = useState(searchParams.get('cert_id') || '')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)

  const {
    isVerifying,
    layerProgress,
    startVerification,
    setLayerProgress,
    setResult,
    setError,
  } = useVerificationStore()

  useEffect(() => {
    const paramId = searchParams.get('cert_id')
    if (paramId) {
      setCertId(paramId)
    }
  }, [searchParams])

  const onDrop = useCallback((acceptedFiles) => {
    const selectedFile = acceptedFiles[0]
    if (selectedFile) {
      setFile(selectedFile)
      const reader = new FileReader()
      reader.onload = (e) => setPreview(e.target.result)
      reader.readAsDataURL(selectedFile)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 16 * 1024 * 1024,
  })

  const removeFile = () => {
    setFile(null)
    setPreview(null)
  }

  const fallbackHttpVerify = async (id, fileToUpload) => {
    try {
      const formData = new FormData()
      formData.append('cert_id', id)
      formData.append('file', fileToUpload)

      const res = await fetch('/api/verify', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Verification failed')

      setResult(data)
      toast.success('Verification complete!')
      navigate('/results')
    } catch (err) {
      setError(err.message)
      toast.error(err.message)
    }
  }

  const handleVerify = async () => {
    if (!certId.trim()) {
      toast.error('Please enter a Certificate ID')
      return
    }
    if (!file) {
      toast.error('Please upload a certificate file')
      return
    }

    startVerification()

    const reader = new FileReader()
    reader.onload = (event) => {
      const base64Data = event.target.result.split(',')[1]
      const socket = io(window.location.origin, {
        transports: ['polling', 'websocket'],
      })

      socket.on('connect', () => {
        socket.emit('start_verification', {
          cert_id: certId.trim(),
          file: base64Data,
          filename: file.name,
        })
      })

      socket.on('layer_progress', (data) => {
        setLayerProgress(data.layer, data)
      })

      socket.on('verification_complete', (data) => {
        setResult(data)
        socket.disconnect()
        toast.success('Verification complete!')
        navigate('/results')
      })

      socket.on('verification_error', (data) => {
        setError(data.error)
        socket.disconnect()
        toast.error(data.error || 'Verification failed')
      })

      socket.on('connect_error', () => {
        socket.disconnect()
        fallbackHttpVerify(certId.trim(), file)
      })
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="pt-24 pb-16 min-h-screen relative">
      <div className="absolute top-20 right-0 w-[400px] h-[400px] bg-gradient-to-bl from-primary-50 to-transparent rounded-full blur-[80px] opacity-40 pointer-events-none" />

      <div className="section-container max-w-3xl relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl gradient-hash flex items-center justify-center shadow-md">
            <ShieldCheck className="w-7 h-7 text-white" />
          </div>
          <div className="flex items-center justify-center gap-4 mb-3">
            <h1 className="text-3xl lg:text-4xl font-bold text-text-primary">
              Verify a Certificate
            </h1>
          </div>
          <p className="text-text-secondary max-w-md mx-auto">
            Upload the certificate file and enter its ID to run the full 4-layer verification.
          </p>
          <button
            onClick={() => navigate('/scan')}
            className="mt-4 inline-flex items-center gap-2 text-sm text-primary font-medium hover:underline"
          >
            <QrCode className="w-4 h-4" /> Or scan a QR code instead
          </button>
        </motion.div>

        {isVerifying ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary-50 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              </div>
              <h2 className="text-xl font-semibold mb-1 text-text-primary">
                Verifying Certificate
              </h2>
              <p className="text-sm text-text-secondary">
                Running all four verification layers on{' '}
                <span className="font-mono text-primary font-semibold">{certId}</span>
              </p>
            </div>
            <LayerProgress progress={layerProgress} />
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card p-8 space-y-6"
          >
            {/* Cert ID Input */}
            <div>
              <label className="label">Certificate ID</label>
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
                <input
                  type="text"
                  value={certId}
                  onChange={(e) => setCertId(e.target.value)}
                  placeholder="e.g. CERT-2026-00891"
                  className="input-field pl-10 font-mono"
                />
              </div>
            </div>

            {/* File Dropzone */}
            <div>
              <label className="label">Certificate File</label>
              <AnimatePresence mode="wait">
                {file ? (
                  <motion.div
                    key="preview"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="border border-border-subtle rounded-card p-4 bg-base-elevated"
                  >
                    <div className="flex items-start gap-4">
                      {preview && preview.startsWith('data:image') ? (
                        <img
                          src={preview}
                          alt="Certificate preview"
                          className="w-32 h-24 object-cover rounded-xl border border-border-subtle shadow-sm"
                        />
                      ) : (
                        <div className="w-32 h-24 rounded-xl bg-white border border-border-subtle flex items-center justify-center">
                          <FileText className="w-8 h-8 text-text-tertiary" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-text-primary truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-text-tertiary mt-1">
                          {(file.size / 1024).toFixed(1)} KB — {file.type || 'unknown'}
                        </p>
                      </div>
                      <button
                        onClick={removeFile}
                        className="btn-ghost p-2 text-text-tertiary hover:text-red-500"
                        title="Remove file"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="dropzone"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <div
                      {...getRootProps()}
                      className={`border-2 border-dashed rounded-card p-10 text-center cursor-pointer transition-all duration-300 ${
                        isDragActive
                          ? 'border-primary bg-primary-50 animate-pulse-glow'
                          : 'border-border-subtle hover:border-primary/50 hover:bg-base-elevated'
                      }`}
                    >
                      <input {...getInputProps()} />
                      <div
                        className={`w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center ${
                          isDragActive ? 'bg-primary-100' : 'bg-base-elevated'
                        }`}
                      >
                        <UploadCloud
                          className={`w-6 h-6 ${
                            isDragActive ? 'text-primary' : 'text-text-tertiary'
                          }`}
                        />
                      </div>
                      <p className="text-sm text-text-secondary mb-1 font-medium">
                        {isDragActive
                          ? 'Drop the file here'
                          : 'Drag & drop a certificate, or click to browse'}
                      </p>
                      <p className="text-xs text-text-tertiary">
                        PNG, JPG, or PDF — max 16MB
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Submit Button */}
            <button
              onClick={handleVerify}
              disabled={!certId.trim() || !file}
              className={`btn-primary w-full py-3.5 text-base ${
                !certId.trim() || !file ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              Run 4-Layer Verification
              <ArrowRight className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </div>
    </div>
  )
}
