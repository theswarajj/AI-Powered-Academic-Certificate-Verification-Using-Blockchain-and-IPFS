import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  ArrowLeft,
  Hash,
  User,
  UploadCloud,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCw,
  Sparkles,
  Key,
  Copy,
  Check,
  Eye,
  EyeOff,
  Database,
  Shield,
  Loader2,
  X,
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'

function CopyCredentialButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = (e) => {
    e.stopPropagation()
    navigator.clipboard.writeText(text)
    setCopied(true)
    toast.success('Copied to clipboard!')
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button
      type="button"
      onClick={handleCopy}
      className="btn-ghost p-1.5 text-text-tertiary hover:text-primary rounded-lg transition-colors"
      title="Copy"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  )
}

const issuanceSteps = [
  { icon: Hash, label: 'Computing Hashes', desc: 'SHA-256 file + content hash' },
  { icon: Database, label: 'Uploading to IPFS', desc: 'Pinning on Pinata gateway' },
  { icon: Shield, label: 'Recording on Blockchain', desc: 'Sepolia smart contract TX' },
  { icon: CheckCircle2, label: 'Complete', desc: 'Certificate issued successfully' },
]

export default function IssueCertificate() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const fileInputRef = useRef(null)

  const [form, setForm] = useState({
    cert_id: '',
    student_name: '',
    degree: '',
    register_number: '',
    issue_date: '',
  })
  const [file, setFile] = useState(null)
  const [isIssuing, setIsIssuing] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [step, setStep] = useState(-1)
  const [issuedCert, setIssuedCert] = useState(null)
  const [generatedCreds, setGeneratedCreds] = useState(null)
  const [showCredPassword, setShowCredPassword] = useState(false)
  const [error, setError] = useState(null)
  const [validationResult, setValidationResult] = useState(null)
  const [mismatchOverridden, setMismatchOverridden] = useState(false)

  if (!isAuthenticated || user?.role !== 'institution') {
    return (
      <div className="pt-24 pb-16 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-amber-50 flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-amber-600" />
          </div>
          <h2 className="text-xl font-bold mb-2 text-text-primary">Access Denied</h2>
          <p className="text-text-secondary mb-6">Only institutions can issue certificates.</p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary">
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setValidationResult(null)
    setMismatchOverridden(false)
  }

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
      setValidationResult(null)
      setMismatchOverridden(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) {
      setFile(dropped)
      setValidationResult(null)
      setMismatchOverridden(false)
    }
  }

  const generateId = () => {
    const year = new Date().getFullYear()
    const rand = String(Math.floor(Math.random() * 99999) + 1).padStart(5, '0')
    setForm({ ...form, cert_id: `CERT-${year}-${rand}` })
  }

  const validateFile = async () => {
    if (!file) return toast.error('Please upload a certificate file')
    if (!form.student_name) return toast.error('Student name is required')

    setIsValidating(true)
    setValidationResult(null)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('student_name', form.student_name)
    formData.append('register_number', form.register_number)
    formData.append('degree', form.degree)
    formData.append('cert_id', form.cert_id)
    formData.append('issue_date', form.issue_date)

    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/certificates/validate-file', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Validation failed')

      setValidationResult(data)
      if (data.valid) {
        toast.success('Certificate content matches form inputs!')
        setMismatchOverridden(true)
      } else {
        toast.error(`${data.mismatches?.length || 0} field mismatch(es) found!`)
      }
    } catch (err) {
      setError(err.message)
      toast.error(err.message)
    } finally {
      setIsValidating(false)
    }
  }

  const handleIssue = async (e) => {
    e.preventDefault()
    if (!file) return toast.error('Please upload a certificate file')
    if (!form.cert_id) return toast.error('Certificate ID is required')
    if (!form.student_name) return toast.error('Student name is required')

    if (!validationResult) {
      await validateFile()
      return
    }

    if (!validationResult.valid && !mismatchOverridden) {
      toast.error('Please confirm or fix the mismatches before issuing')
      return
    }

    setIsIssuing(true)
    setStep(0)
    setError(null)
    setIssuedCert(null)

    const formData = new FormData()
    formData.append('file', file)
    Object.entries(form).forEach(([k, v]) => formData.append(k, v))

    const interval = setInterval(() => {
      setStep((s) => (s < 2 ? s + 1 : s))
    }, 3000)

    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/certificates/issue', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      clearInterval(interval)
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Issuance failed')

      setStep(3)
      setIssuedCert(data.certificate)
      setGeneratedCreds(data.student_credentials || null)
      if (data.student_credentials?.is_new) {
        toast.success(`Certificate issued & Student login created: ${data.student_credentials.username}`)
      } else {
        toast.success('Certificate issued successfully!')
      }
    } catch (err) {
      clearInterval(interval)
      setError(err.message)
      toast.error(err.message)
    } finally {
      setIsIssuing(false)
    }
  }

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="section-container max-w-3xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 mb-8">
          <button onClick={() => navigate('/dashboard')} className="btn-ghost">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <span className="inline-block px-3 py-1 rounded-pill bg-primary-50 text-primary text-xs font-semibold mb-4 border border-primary-200">
            ISSUE CERTIFICATE
          </span>
          <h1 className="text-3xl font-bold mb-2 text-text-primary">
            Issue <span className="gradient-text">Certificate</span>
          </h1>
          <p className="text-text-secondary mb-8">
            Fill in the certificate details, upload the file, and it will be hashed, stored on IPFS, and recorded on the blockchain.
          </p>
        </motion.div>

        {/* Issued Success Card */}
        <AnimatePresence>
          {issuedCert && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-card p-6 mb-8 border-2 border-emerald-200 bg-emerald-50/30"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <h3 className="font-bold text-emerald-700">Certificate Issued Successfully</h3>
                  <p className="text-xs text-text-secondary">Recorded on-chain and stored on IPFS</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-white rounded-xl p-3 border border-border-subtle">
                  <span className="text-text-tertiary text-xs block mb-1">Certificate ID</span>
                  <span className="font-mono text-primary font-semibold">{issuedCert.cert_id}</span>
                </div>
                <div className="bg-white rounded-xl p-3 border border-border-subtle">
                  <span className="text-text-tertiary text-xs block mb-1">Student</span>
                  <span className="font-medium">{issuedCert.student_name}</span>
                </div>
                <div className="bg-white rounded-xl p-3 border border-border-subtle">
                  <span className="text-text-tertiary text-xs block mb-1">File Hash</span>
                  <span className="font-mono text-xs truncate block">{issuedCert.file_hash}</span>
                </div>
                <div className="bg-white rounded-xl p-3 border border-border-subtle">
                  <span className="text-text-tertiary text-xs block mb-1">IPFS CID</span>
                  <span className="font-mono text-xs truncate block">{issuedCert.ipfs_cid || 'N/A'}</span>
                </div>
                {issuedCert.tx_hash && !issuedCert.tx_hash.startsWith('FAILED') && (
                  <div className="col-span-2 bg-white rounded-xl p-3 border border-border-subtle">
                    <span className="text-text-tertiary text-xs block mb-1">Blockchain TX</span>
                    <a
                      href={`https://sepolia.etherscan.io/tx/${issuedCert.tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-xs text-primary hover:underline truncate block"
                    >
                      {issuedCert.tx_hash}
                    </a>
                  </div>
                )}
              </div>

              {/* Student Login Credentials Generated Box */}
              {generatedCreds && (
                <div className="mt-4 p-4 rounded-xl border border-indigo-200/80 bg-gradient-to-br from-indigo-50/90 via-violet-50/50 to-white shadow-sm">
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
                        <Key className="w-4 h-4 text-indigo-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-xs text-indigo-950 uppercase tracking-wider">
                            Student Login Credentials
                          </h4>
                          {generatedCreds.is_new ? (
                            <span className="bg-emerald-100 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-full text-[10px] font-bold">
                              ✨ Auto-Generated
                            </span>
                          ) : (
                            <span className="bg-blue-100 text-blue-800 border border-blue-200 px-2 py-0.5 rounded-full text-[10px] font-bold">
                              Linked to Existing Student
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-text-secondary mt-0.5">
                          The student can sign in with these credentials to view & download this certificate.
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => navigate('/students')}
                      className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold underline shrink-0 whitespace-nowrap"
                    >
                      View in Student Logins ↗
                    </button>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-2.5">
                    <div className="bg-white p-3 rounded-lg border border-indigo-100 flex items-center justify-between">
                      <div className="min-w-0 pr-2">
                        <span className="text-[10px] text-text-tertiary block font-semibold uppercase tracking-wider">
                          Student User ID / Username
                        </span>
                        <span className="font-mono text-sm font-bold text-indigo-950 truncate block">
                          {generatedCreds.username}
                        </span>
                      </div>
                      <CopyCredentialButton text={generatedCreds.username} />
                    </div>

                    <div className="bg-white p-3 rounded-lg border border-indigo-100 flex items-center justify-between">
                      <div className="min-w-0 pr-2">
                        <span className="text-[10px] text-text-tertiary block font-semibold uppercase tracking-wider">
                          Password
                        </span>
                        <span className="font-mono text-sm font-bold text-slate-800 select-all">
                          {showCredPassword ? generatedCreds.password : '••••••••'}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => setShowCredPassword(!showCredPassword)}
                          className="btn-ghost p-1.5 text-text-tertiary hover:text-text-primary rounded-lg transition-colors"
                          title={showCredPassword ? 'Hide password' : 'Show password'}
                        >
                          {showCredPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                        <CopyCredentialButton text={generatedCreds.password} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-3 mt-4">
                <button onClick={() => navigate('/certificates')} className="btn-primary text-sm">
                  View All Certificates
                </button>
                <button
                  onClick={() => {
                    setIssuedCert(null)
                    setGeneratedCreds(null)
                    setShowCredPassword(false)
                    setForm({ cert_id: '', student_name: '', degree: '', register_number: '', issue_date: '' })
                    setFile(null)
                    setStep(-1)
                  }}
                  className="btn-outline text-sm"
                >
                  Issue Another
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Issuance Stepper */}
        <AnimatePresence>
          {isIssuing && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="glass-card p-6 mb-8"
            >
              <h3 className="text-sm font-semibold mb-4 text-text-primary">Issuance Progress</h3>
              <div className="space-y-3">
                {issuanceSteps.slice(0, 3).map((s, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div
                      className={`w-8 h-8 rounded-xl flex items-center justify-center transition-all ${
                        idx < step
                          ? 'bg-emerald-100'
                          : idx === step
                          ? 'bg-primary-100 animate-pulse'
                          : 'bg-base-elevated'
                      }`}
                    >
                      {idx < step ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : idx === step ? (
                        <Loader2 className="w-4 h-4 text-primary animate-spin" />
                      ) : (
                        <s.icon className="w-4 h-4 text-text-tertiary" />
                      )}
                    </div>
                    <div>
                      <span className={`text-sm font-medium ${idx <= step ? 'text-text-primary' : 'text-text-tertiary'}`}>
                        {s.label}
                      </span>
                      <span className="text-xs text-text-tertiary block">{s.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-4 mb-6 border-2 border-red-200 bg-red-50">
            <div className="flex items-center gap-2 text-red-700">
              <XCircle className="w-4 h-4" />
              <span className="text-sm font-medium">{error}</span>
            </div>
          </motion.div>
        )}

        {/* Form */}
        {!issuedCert && (
          <motion.form
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            onSubmit={handleIssue}
            className="space-y-6"
          >
            {/* Certificate Identity */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold mb-4 text-text-primary flex items-center gap-2">
                <Hash className="w-4 h-4 text-primary" /> Certificate Identity
              </h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Certificate ID *</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      name="cert_id"
                      value={form.cert_id}
                      onChange={handleChange}
                      placeholder="e.g. CERT-2026-00891"
                      className="input-field flex-1 font-mono"
                      required
                    />
                    <button
                      type="button"
                      onClick={generateId}
                      className="btn-outline text-xs whitespace-nowrap gap-1"
                    >
                      <Sparkles className="w-3.5 h-3.5" /> Generate
                    </button>
                  </div>
                </div>
                <div>
                  <label className="label">Issue Date</label>
                  <input
                    type="date"
                    name="issue_date"
                    value={form.issue_date}
                    onChange={handleChange}
                    className="input-field"
                  />
                </div>
              </div>
            </div>

            {/* Student Info */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold mb-4 text-text-primary flex items-center gap-2">
                <User className="w-4 h-4 text-primary" /> Student Information
              </h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Student Name *</label>
                  <input
                    type="text"
                    name="student_name"
                    value={form.student_name}
                    onChange={handleChange}
                    placeholder="Full name"
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="label">Register Number</label>
                  <input
                    type="text"
                    name="register_number"
                    value={form.register_number}
                    onChange={handleChange}
                    placeholder="e.g. 22c568234"
                    className="input-field font-mono"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="label">Degree / Program</label>
                  <input
                    type="text"
                    name="degree"
                    value={form.degree}
                    onChange={handleChange}
                    placeholder="e.g. B.Tech Computer Science"
                    className="input-field"
                  />
                </div>
                <div className="md:col-span-2 mt-1 p-3 rounded-xl bg-indigo-50/70 border border-indigo-200/60 flex items-start gap-2.5">
                  <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <div className="text-xs text-slate-700 leading-relaxed">
                    <strong className="text-indigo-900 font-semibold">Automatic Student Credential Generation:</strong> Student User ID and password will be generated automatically when this certificate is issued. The student can immediately use them to log in, view, and download their certificate.
                  </div>
                </div>
              </div>
            </div>

            {/* Certificate File Dropzone */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold mb-4 text-text-primary flex items-center gap-2">
                <UploadCloud className="w-4 h-4 text-primary" /> Certificate File
              </h3>
              <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-card p-8 text-center cursor-pointer transition-all ${
                  file
                    ? 'border-primary/50 bg-primary-50'
                    : 'border-border-subtle hover:border-primary/30 hover:bg-base-elevated'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".png,.jpg,.jpeg,.pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <FileText className="w-8 h-8 text-primary" />
                    <div className="text-left">
                      <p className="font-semibold text-sm text-text-primary">{file.name}</p>
                      <p className="text-xs text-text-tertiary">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        setFile(null)
                      }}
                      className="btn-ghost p-1.5 ml-2 text-text-tertiary hover:text-red-500"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-base-elevated flex items-center justify-center">
                      <UploadCloud className="w-6 h-6 text-text-tertiary" />
                    </div>
                    <p className="text-text-secondary text-sm font-medium">
                      Drag & drop certificate file, or click to browse
                    </p>
                    <p className="text-text-tertiary text-xs mt-1">PNG, JPG, or PDF — max 16MB</p>
                  </>
                )}
              </div>
            </div>

            {/* Validation Feedback */}
            <AnimatePresence>
              {validationResult && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={`glass-card p-6 border-2 ${
                    validationResult.valid
                      ? 'border-emerald-200 bg-emerald-50/30'
                      : 'border-amber-200 bg-amber-50/30'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        validationResult.valid ? 'bg-emerald-100' : 'bg-amber-100'
                      }`}
                    >
                      {validationResult.valid ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-amber-600" />
                      )}
                    </div>
                    <div>
                      <h3
                        className={`font-bold ${
                          validationResult.valid ? 'text-emerald-700' : 'text-amber-700'
                        }`}
                      >
                        {validationResult.valid
                          ? 'Certificate Content Verified ✓'
                          : `${validationResult.mismatches?.length} Field Mismatch${
                              validationResult.mismatches?.length > 1 ? 'es' : ''
                            } Detected`}
                      </h3>
                      <p className="text-xs text-text-secondary">
                        OCR Confidence: {validationResult.ocr_confidence}%
                      </p>
                    </div>
                  </div>

                  {validationResult.matches?.length > 0 && (
                    <div className="space-y-1.5 mb-3">
                      {validationResult.matches.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-2 rounded-xl"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                          <span className="font-medium">{item.field}:</span>
                          <span>"{item.form_value}" matches certificate</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {validationResult.mismatches?.length > 0 && (
                    <div className="space-y-1.5 mb-4">
                      {validationResult.mismatches.map((item, idx) => (
                        <div
                          key={idx}
                          className="text-xs text-red-700 bg-red-50 border border-red-200 px-3 py-2.5 rounded-xl"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <XCircle className="w-3.5 h-3.5 flex-shrink-0" />
                            <span className="font-bold">{item.field} — MISMATCH</span>
                          </div>
                          <div className="ml-5 space-y-0.5 text-[11px]">
                            <p>
                              Form input:{' '}
                              <span className="font-mono font-semibold">"{item.form_value}"</span>
                            </p>
                            <p>
                              Certificate:{' '}
                              <span className="font-mono font-semibold">"{item.ocr_value}"</span>
                            </p>
                          </div>
                        </div>
                      ))}

                      {!mismatchOverridden && (
                        <div className="flex gap-3 mt-4">
                          <button
                            type="button"
                            onClick={() => setMismatchOverridden(true)}
                            className="btn-outline text-sm border-amber-300 text-amber-700 hover:bg-amber-50"
                          >
                            <AlertTriangle className="w-4 h-4" /> Issue Anyway
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setValidationResult(null)
                              setMismatchOverridden(false)
                            }}
                            className="btn-outline text-sm"
                          >
                            Fix Inputs
                          </button>
                        </div>
                      )}

                      {mismatchOverridden && (
                        <div className="text-xs text-amber-700 bg-amber-100 border border-amber-300 px-3 py-2 rounded-xl mt-3 flex items-center gap-2">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          Mismatch acknowledged — you can now proceed to issue.
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Action Button */}
            <motion.button
              type="submit"
              disabled={isIssuing || isValidating}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="btn-primary w-full py-3.5 text-base disabled:opacity-50"
            >
              {isValidating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" /> Validating Certificate Content...
                </>
              ) : isIssuing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" /> Issuing Certificate...
                </>
              ) : validationResult ? (
                validationResult.valid || mismatchOverridden ? (
                  <>
                    <UploadCloud className="w-5 h-5" /> Confirm & Issue on Blockchain
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-5 h-5" /> Fix Mismatches or Issue Anyway
                  </>
                )
              ) : (
                <>
                  <UploadCloud className="w-5 h-5" /> Validate & Issue Certificate
                </>
              )}
            </motion.button>
          </motion.form>
        )}
      </div>
    </div>
  )
}