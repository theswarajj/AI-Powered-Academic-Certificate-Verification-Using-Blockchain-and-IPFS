import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  ShieldCheck,
  FilePlus,
  FileText,
  QrCode,
  Sliders,
  AlertTriangle,
  ArrowRight,
  GraduationCap,
  Users,
  KeyRound,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  X,
  Sparkles,
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'

const quickActions = [
  {
    title: 'My Certificates',
    desc: 'View and download your official academic certificates',
    icon: FileText,
    gradient: 'gradient-blockchain',
    path: '/certificates',
    roles: ['student'],
  },
  {
    title: 'Verify Certificate',
    desc: 'Run 4-layer verification on any certificate',
    icon: ShieldCheck,
    gradient: 'gradient-hash',
    path: '/verify',
    roles: ['verifier', 'institution', 'admin', 'student'],
  },
  {
    title: 'Student Credentials',
    desc: 'Provide, control, and manage student login accounts',
    icon: Users,
    gradient: 'gradient-ai',
    path: '/students',
    roles: ['institution', 'admin'],
  },
  {
    title: 'Issue Certificate',
    desc: 'Issue a new certificate on Ethereum & IPFS',
    icon: FilePlus,
    gradient: 'gradient-blockchain',
    path: '/issue',
    roles: ['institution'],
  },
  {
    title: 'View Certificates',
    desc: 'Browse and manage issued certificates',
    icon: FileText,
    gradient: 'gradient-ipfs',
    path: '/certificates',
    roles: ['verifier', 'institution', 'admin'],
  },
  {
    title: 'Scan QR Code',
    desc: 'Quickly verify via QR code scan',
    icon: QrCode,
    gradient: 'gradient-ai',
    path: '/scan',
    roles: ['verifier', 'institution', 'admin', 'student'],
  },
  {
    title: 'Admin Panel',
    desc: 'View analytics and audit logs',
    icon: Sliders,
    gradient: 'bg-gradient-to-br from-gray-600 to-gray-800',
    path: '/admin',
    roles: ['admin', 'institution', 'verifier'],
  },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()

  // Change Password Modal
  const [changePwOpen, setChangePwOpen] = useState(false)
  const [pwLoading, setPwLoading] = useState(false)
  const [showCurrentPw, setShowCurrentPw] = useState(false)
  const [showNewPw, setShowNewPw] = useState(false)
  const [pwForm, setPwForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })

  if (!isAuthenticated) {
    return (
      <div className="pt-24 pb-16 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-amber-50 flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-amber-600" />
          </div>
          <h2 className="text-xl font-bold mb-2 text-text-primary">Authentication Required</h2>
          <p className="text-text-secondary mb-6">Please sign in to access the dashboard.</p>
          <button onClick={() => navigate('/auth')} className="btn-primary">
            Sign In <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    )
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    if (pwForm.new_password !== pwForm.confirm_password) {
      return toast.error('New passwords do not match')
    }
    if (pwForm.new_password.length < 6) {
      return toast.error('New password must be at least 6 characters')
    }

    setPwLoading(true)
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: pwForm.current_password,
          new_password: pwForm.new_password,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Password update failed')

      toast.success('Password changed successfully! Updated across the system.')
      setChangePwOpen(false)
      setPwForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      toast.error(err.message)
    } finally {
      setPwLoading(false)
    }
  }

  const allowedActions = quickActions.filter((action) =>
    action.roles.includes(user?.role || 'verifier')
  )

  const isStudent = user?.role === 'student'

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="section-container">
        {/* Profile Card / Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8"
        >
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-block px-3 py-1 rounded-pill bg-primary-50 text-primary text-xs font-semibold border border-primary-200">
                {isStudent ? 'STUDENT PORTAL' : 'DASHBOARD'}
              </span>
              <span className="badge bg-base-elevated border border-border-subtle text-text-tertiary uppercase text-[10px]">
                {user?.role}
              </span>
            </div>
            <h1 className="text-3xl font-bold text-text-primary">
              Welcome, <span className="gradient-text">{user?.full_name || user?.username}</span>
            </h1>
            {isStudent && user?.register_number && (
              <p className="text-text-secondary text-sm mt-1 font-mono">
                University Register No: <span className="text-primary font-bold">{user.register_number}</span>
              </p>
            )}
          </div>

          {/* User actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setChangePwOpen(true)}
              className="btn-outline text-xs gap-1.5 py-2 px-3.5 shadow-sm"
            >
              <KeyRound className="w-3.5 h-3.5 text-primary" /> Change Password
            </button>
          </div>
        </motion.div>

        {/* Student Special Notice */}
        {isStudent && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-5 mb-8 border-l-4 border-l-primary bg-primary-50/30 flex items-start gap-4"
          >
            <div className="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center flex-shrink-0">
              <GraduationCap className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-text-primary text-sm">
                Your Academic Certificate Access
              </h3>
              <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                You are securely logged into your student portal. You can view and download only your official academic certificates verified on the blockchain. If you update your password, your university record will synchronize automatically.
              </p>
            </div>
          </motion.div>
        )}

        {/* Action Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {allowedActions.map((action, idx) => (
            <motion.div
              key={action.path + action.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + idx * 0.05 }}
              onClick={() => navigate(action.path)}
              className="glass-card-hover p-6 cursor-pointer group"
            >
              <div
                className={`w-12 h-12 ${action.gradient} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-md`}
              >
                <action.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-semibold mb-1 text-text-primary flex items-center justify-between">
                {action.title}
                <ArrowRight className="w-4 h-4 text-text-tertiary group-hover:text-primary group-hover:translate-x-1 transition-all" />
              </h3>
              <p className="text-sm text-text-secondary">{action.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* Change Password Modal */}
        <AnimatePresence>
          {changePwOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="glass-card max-w-md w-full p-6 shadow-2xl relative"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center">
                      <Lock className="w-4 h-4 text-primary" />
                    </div>
                    <h3 className="font-bold text-lg text-text-primary">Change Your Password</h3>
                  </div>
                  <button
                    onClick={() => setChangePwOpen(false)}
                    className="btn-ghost p-1 text-text-tertiary hover:text-text-primary"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <p className="text-xs text-text-secondary mb-4">
                  {isStudent
                    ? 'Updating your password will immediately reflect in your university administration section.'
                    : 'Enter your current password and choose a secure new password.'}
                </p>

                <form onSubmit={handleChangePassword} className="space-y-4">
                  <div>
                    <label className="label">Current Password</label>
                    <div className="relative">
                      <input
                        type={showCurrentPw ? 'text' : 'password'}
                        value={pwForm.current_password}
                        onChange={(e) =>
                          setPwForm({ ...pwForm, current_password: e.target.value })
                        }
                        placeholder="Current password"
                        className="input-field pr-10 font-mono text-xs"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPw(!showCurrentPw)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary"
                      >
                        {showCurrentPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="label">New Password</label>
                    <div className="relative">
                      <input
                        type={showNewPw ? 'text' : 'password'}
                        value={pwForm.new_password}
                        onChange={(e) =>
                          setPwForm({ ...pwForm, new_password: e.target.value })
                        }
                        placeholder="New password (min 6 characters)"
                        className="input-field pr-10 font-mono text-xs"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPw(!showNewPw)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary"
                      >
                        {showNewPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="label">Confirm New Password</label>
                    <input
                      type="password"
                      value={pwForm.confirm_password}
                      onChange={(e) =>
                        setPwForm({ ...pwForm, confirm_password: e.target.value })
                      }
                      placeholder="Repeat new password"
                      className="input-field font-mono text-xs"
                      required
                    />
                  </div>

                  <div className="flex gap-3 pt-3 border-t border-border-subtle">
                    <button
                      type="button"
                      onClick={() => setChangePwOpen(false)}
                      className="btn-outline flex-1 text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={pwLoading}
                      className="btn-primary flex-1 text-sm"
                    >
                      {pwLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Update Password'}
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}