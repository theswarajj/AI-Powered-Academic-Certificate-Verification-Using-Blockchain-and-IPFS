import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  ArrowLeft,
  Search,
  CheckCircle2,
  XCircle,
  Copy,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  FileText,
  UploadCloud,
  AlertTriangle,
  Check,
  Download,
  Loader2,
  Eye,
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'

const SEPOLIA_BASE = 'https://sepolia.etherscan.io/tx/'
const IPFS_BASE = 'https://gateway.pinata.cloud/ipfs/'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    toast.success('Copied')
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <button onClick={handleCopy} className="btn-ghost p-1" title="Copy">
      {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
    </button>
  )
}

export default function ViewCertificates() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()

  const [certificates, setCertificates] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [selectedCert, setSelectedCert] = useState(null)
  const [downloadingId, setDownloadingId] = useState(null)

  const handleDownload = async (cert, e) => {
    if (e) e.stopPropagation()
    setDownloadingId(cert.cert_id)
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/certificates/${cert.cert_id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.error || 'Failed to download certificate')
      }

      // Extract real filename and extension from Content-Disposition header
      const disposition = res.headers.get('content-disposition') || ''
      let filename = ''
      const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match && match[1]) {
        filename = match[1].replace(/['"]/g, '').trim()
      }

      const blob = await res.blob()
      if (!filename) {
        let ext = '.png'
        if (blob.type.includes('pdf')) ext = '.pdf'
        else if (blob.type.includes('jpeg') || blob.type.includes('jpg')) ext = '.jpg'
        else if (blob.type.includes('png')) ext = '.png'
        else if (cert.file_name && cert.file_name.includes('.')) {
          ext = cert.file_name.slice(cert.file_name.lastIndexOf('.'))
        }
        const safeName = (cert.student_name || 'Certificate').replace(/[^a-zA-Z0-9_-]/g, '_')
        filename = `${safeName}_${cert.cert_id}${ext}`
      }

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => window.URL.revokeObjectURL(url), 1000)
      toast.success(`Downloaded ${filename}`)
    } catch (err) {
      toast.error(err.message || 'Error downloading certificate')
    } finally {
      setDownloadingId(null)
    }
  }

  const handlePreview = async (cert, e) => {
    if (e) e.stopPropagation()
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/certificates/${cert.cert_id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to load certificate preview')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      window.open(url, '_blank')
    } catch (err) {
      toast.error(err.message || 'Error previewing certificate')
    }
  }

  const fetchCertificates = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('token')
      const params = new URLSearchParams({ page, per_page: 10 })
      if (search) params.set('search', search)

      const res = await fetch(`/api/certificates?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to fetch')
      const data = await res.json()
      setCertificates(data.certificates || [])
      setTotal(data.total || 0)
    } catch {
      toast.error('Failed to load certificates')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchCertificates()
    }
  }, [page, search, isAuthenticated])

  if (!isAuthenticated) {
    return (
      <div className="pt-24 pb-16 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-amber-50 flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-amber-600" />
          </div>
          <h2 className="text-xl font-bold mb-2 text-text-primary">Authentication Required</h2>
          <p className="text-text-secondary mb-6">Please sign in to view certificates.</p>
          <button onClick={() => navigate('/auth')} className="btn-primary">
            Sign In
          </button>
        </div>
      </div>
    )
  }

  const totalPages = Math.ceil(total / 10)

  const handleRevoke = async (certId) => {
    if (!confirm('Are you sure you want to revoke this certificate? This action cannot be undone.')) {
      return
    }

    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/certificates/${certId}/revoke`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to revoke')

      toast.success('Certificate revoked successfully')
      setSelectedCert((prev) => (prev ? { ...prev, status: 'revoked' } : null))
      fetchCertificates()
    } catch (err) {
      toast.error(err.message)
    }
  }

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="section-container max-w-5xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/dashboard')} className="btn-ghost">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <span className="inline-block px-3 py-1 rounded-pill bg-primary-50 text-primary text-xs font-semibold mb-4 border border-primary-200">
            {user?.role === 'student' ? 'STUDENT VAULT' : 'CERTIFICATES'}
          </span>
          <h1 className="text-3xl font-bold mb-2 text-text-primary">
            <span className="gradient-text">
              {user?.role === 'student' ? 'My Certificates' : 'Certificates'}
            </span>
          </h1>
          <p className="text-text-secondary">
            {user?.role === 'student'
              ? `Official academic credentials registered to your student profile (${user?.register_number || user?.username})`
              : user?.role === 'institution'
              ? 'Certificates issued and managed by your institution'
              : 'Browse all issued certificates recorded in the ledger'}
          </p>
        </motion.div>

        {user?.role === 'student' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-xl bg-primary-50/70 border border-primary-200/60 mb-6 flex items-start gap-3"
          >
            <ShieldCheck className="w-5 h-5 text-primary shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold text-text-primary">
                Protected Student Vault • {user?.full_name || user?.username} ({user?.register_number || 'Enrolled Student'})
              </p>
              <p className="text-text-secondary text-xs mt-0.5">
                You have secure access to view and download only your authentic certificates issued by {user?.institution || 'your University'}.
              </p>
            </div>
          </motion.div>
        )}

        {/* Search */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-4 mb-6"
        >
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
              placeholder="Search by Certificate ID, student name, or register number..."
              className="input-field pl-10"
            />
          </div>
        </motion.div>

        {/* Certificate Details Card */}
        {selectedCert && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-6 mb-6 border-2 border-primary-200"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg text-text-primary">{selectedCert.cert_id}</h3>
              <button
                onClick={() => setSelectedCert(null)}
                className="btn-ghost p-1.5 text-text-tertiary hover:text-text-primary"
              >
                ✕
              </button>
            </div>

            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-3">
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">Student Name</span>
                  <span className="font-semibold text-text-primary">{selectedCert.student_name}</span>
                </div>
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">Degree</span>
                  <span className="text-text-primary">{selectedCert.degree || '—'}</span>
                </div>
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">Register Number</span>
                  <span className="font-mono text-text-primary">{selectedCert.register_number || '—'}</span>
                </div>
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">Issue Date</span>
                  <span className="text-text-primary">{selectedCert.issue_date || '—'}</span>
                </div>
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">Issued By</span>
                  <span className="text-text-primary">{selectedCert.issued_by}</span>
                </div>
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">Status</span>
                  <span
                    className={`badge border ${
                      selectedCert.status === 'active'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-red-50 text-red-700 border-red-200'
                    }`}
                  >
                    {selectedCert.status}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">File Hash</span>
                  <div className="flex items-center gap-1">
                    <span className="font-mono text-xs truncate text-text-secondary">
                      {selectedCert.file_hash}
                    </span>
                    <CopyButton text={selectedCert.file_hash} />
                  </div>
                </div>
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">Content Hash</span>
                  <div className="flex items-center gap-1">
                    <span className="font-mono text-xs truncate text-text-secondary">
                      {selectedCert.content_hash}
                    </span>
                    <CopyButton text={selectedCert.content_hash} />
                  </div>
                </div>
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">IPFS CID</span>
                  {selectedCert.ipfs_cid ? (
                    <a
                      href={`${IPFS_BASE}${selectedCert.ipfs_cid}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-xs text-primary hover:underline flex items-center gap-1"
                    >
                      {selectedCert.ipfs_cid.slice(0, 20)}... <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-text-tertiary text-xs">Not uploaded</span>
                  )}
                </div>
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">Blockchain TX</span>
                  {selectedCert.tx_hash && !selectedCert.tx_hash.startsWith('FAILED') ? (
                    <a
                      href={`${SEPOLIA_BASE}${selectedCert.tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-xs text-primary hover:underline flex items-center gap-1"
                    >
                      {selectedCert.tx_hash.slice(0, 20)}... <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-text-tertiary text-xs">{selectedCert.tx_hash || 'Not recorded'}</span>
                  )}
                </div>
                <div>
                  <span className="text-text-tertiary text-xs block font-medium">Issued At</span>
                  <span className="text-xs text-text-primary">
                    {new Date(selectedCert.issued_at).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 mt-5">
              <button
                onClick={(e) => handleDownload(selectedCert, e)}
                disabled={downloadingId === selectedCert.cert_id}
                className="btn-primary text-sm flex items-center gap-2"
              >
                {downloadingId === selectedCert.cert_id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                Download Certificate
              </button>
              <button
                onClick={(e) => handlePreview(selectedCert, e)}
                className="btn-outline text-sm flex items-center gap-2"
                title="Preview original uploaded certificate"
              >
                <Eye className="w-4 h-4" /> Preview
              </button>
              <button
                onClick={() => navigate(`/verify?cert_id=${selectedCert.cert_id}`)}
                className="btn-outline text-sm flex items-center gap-2"
              >
                <ShieldCheck className="w-4 h-4" /> Verify On-Chain
              </button>
              {(user?.role === 'institution' || user?.role === 'admin') &&
                selectedCert.status !== 'revoked' && (
                  <button
                    onClick={() => handleRevoke(selectedCert.cert_id)}
                    className="btn-outline text-sm text-red-600 border-red-200 hover:bg-red-50 sm:ml-auto"
                  >
                    <XCircle className="w-4 h-4" /> Revoke
                  </button>
                )}
            </div>
          </motion.div>
        )}

        {/* Certificate List */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card overflow-hidden"
        >
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <span className="text-text-secondary text-sm">Loading certificates...</span>
            </div>
          ) : certificates.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-base-elevated flex items-center justify-center">
                <FileText className="w-7 h-7 text-text-tertiary" />
              </div>
              <h3 className="font-semibold mb-1 text-text-primary">No Certificates Found</h3>
              <p className="text-text-secondary text-sm mb-4">
                {search
                  ? 'No certificates match your search.'
                  : user?.role === 'student'
                  ? `No certificates have been issued to ${user?.register_number || user?.full_name || 'your profile'} yet. When your university issues your certificate, it will appear here.`
                  : 'No certificates have been issued yet.'}
              </p>
              {user?.role === 'institution' && (
                <button onClick={() => navigate('/issue')} className="btn-primary text-sm">
                  <UploadCloud className="w-4 h-4" /> Issue Your First Certificate
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="grid grid-cols-12 gap-2 px-4 py-3 bg-base-elevated text-xs font-semibold text-text-tertiary uppercase tracking-wider border-b border-border-subtle">
                <span className="col-span-2">Cert ID</span>
                <span className="col-span-3">Student</span>
                <span className="col-span-2">Degree</span>
                <span className="col-span-2">Date</span>
                <span className="col-span-1">Status</span>
                <span className="col-span-2 text-right">Actions</span>
              </div>

              {certificates.map((cert, idx) => (
                <motion.div
                  key={cert.cert_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.03 }}
                  onClick={() => setSelectedCert(cert)}
                  className="grid grid-cols-12 gap-2 px-4 py-3 items-center hover:bg-base-elevated cursor-pointer transition-colors border-b border-border-subtle last:border-0"
                >
                  <span className="col-span-2 font-mono text-xs text-primary font-semibold truncate">
                    {cert.cert_id}
                  </span>
                  <span className="col-span-3 text-sm truncate text-text-primary">
                    <span className="font-medium">{cert.student_name}</span>
                    {cert.register_number && (
                      <span className="block text-[11px] font-mono text-text-tertiary">
                        {cert.register_number}
                      </span>
                    )}
                  </span>
                  <span className="col-span-2 text-xs text-text-secondary truncate">
                    {cert.degree || '—'}
                  </span>
                  <span className="col-span-2 text-xs text-text-secondary">
                    {cert.issue_date || '—'}
                  </span>
                  <span className="col-span-1">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                        cert.status === 'active'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-red-50 text-red-700 border-red-200'
                      }`}
                    >
                      {cert.status}
                    </span>
                  </span>
                  <span className="col-span-2 flex items-center justify-end gap-1">
                    <button
                      onClick={(e) => handlePreview(cert, e)}
                      className="btn-ghost p-1.5 text-text-secondary hover:text-primary transition-colors"
                      title="Preview Certificate"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={(e) => handleDownload(cert, e)}
                      disabled={downloadingId === cert.cert_id}
                      className="btn-ghost p-1.5 text-text-secondary hover:text-primary transition-colors"
                      title="Download Certificate"
                    >
                      {downloadingId === cert.cert_id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                      ) : (
                        <Download className="w-3.5 h-3.5" />
                      )}
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedCert(cert)
                      }}
                      className="btn-ghost p-1.5 text-text-tertiary hover:text-text-primary"
                      title="View Details"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  </span>
                </motion.div>
              ))}
            </>
          )}
        </motion.div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <span className="text-xs text-text-tertiary font-medium">
              Showing {(page - 1) * 10 + 1}–{Math.min(page * 10, total)} of {total}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-ghost p-2 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm text-text-secondary px-3 py-1 bg-base-elevated rounded-btn border border-border-subtle font-medium">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-ghost p-2 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}