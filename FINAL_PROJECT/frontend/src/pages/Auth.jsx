import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  ShieldCheck,
  User,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  Wallet,
  Building,
  GraduationCap,
  Loader2,
  Info,
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'

const registrationRoles = [
  { id: 'verifier', label: 'Verifier', desc: 'Verify certificates', icon: ShieldCheck, color: 'text-primary' },
  { id: 'institution', label: 'Institution', desc: 'Issue & manage', icon: Building, color: 'text-accent-purple' },
]

export default function Auth() {
  const navigate = useNavigate()
  const { login, register } = useAuthStore()
  const [isLogin, setIsLogin] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    full_name: '',
    role: 'verifier',
    wallet_address: '',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      if (isLogin) {
        await login(formData.username, formData.password)
        toast.success('Welcome back!')
      } else {
        await register(formData)
        toast.success('Account created!')
      }
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const updateField = (field, val) => {
    setFormData((prev) => ({ ...prev, [field]: val }))
  }

  return (
    <div className="pt-24 pb-16 min-h-screen flex items-center relative">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-bl from-primary-50 to-transparent rounded-full blur-[80px] opacity-40 pointer-events-none" />

      <div className="section-container max-w-lg w-full relative z-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl gradient-blockchain flex items-center justify-center shadow-primary">
            <ShieldCheck className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-text-primary">
            {isLogin ? 'Welcome Back' : 'Create Organization Account'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isLogin
              ? 'Sign in to access your certificates and dashboard'
              : 'Register your institution or verification organization'}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-8"
        >
          {/* Switch tabs */}
          <div className="flex rounded-btn bg-base-elevated p-1 mb-8">
            {['Sign In', 'Register'].map((tab, idx) => {
              const active = idx === 0 ? isLogin : !isLogin
              return (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setIsLogin(idx === 0)}
                  className={`flex-1 py-2.5 text-sm font-semibold rounded-btn transition-all ${
                    active
                      ? 'bg-white text-text-primary shadow-sm border border-border-subtle'
                      : 'text-text-tertiary hover:text-text-secondary'
                  }`}
                >
                  {tab}
                </button>
              )
            })}
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Student Note when on Login */}
            {isLogin && (
              <div className="p-3 bg-base-elevated rounded-xl border border-border-subtle text-xs text-text-secondary flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-primary flex-shrink-0" />
                <span>
                  Students: Please log in using the credentials provided by your university.
                </span>
              </div>
            )}

            {/* Registration note & role selection */}
            <AnimatePresence>
              {!isLogin && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-4 overflow-hidden"
                >
                  {/* Callout: No student registration */}
                  <div className="p-3.5 bg-primary-50/70 rounded-xl border border-primary-200 text-xs text-text-secondary flex items-start gap-2.5">
                    <Info className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-semibold text-text-primary block mb-0.5">
                        Student Registration Notice
                      </span>
                      Students cannot self-register. Student credentials are created and managed directly by your university/institution.
                    </div>
                  </div>

                  <div>
                    <label className="label">Select Account Type</label>
                    <div className="grid grid-cols-2 gap-2">
                      {registrationRoles.map((r) => (
                        <button
                          key={r.id}
                          type="button"
                          onClick={() => updateField('role', r.id)}
                          className={`p-3 rounded-btn border text-center transition-all ${
                            formData.role === r.id
                              ? 'border-primary bg-primary-50 ring-1 ring-primary/20'
                              : 'border-border-subtle hover:border-border-strong bg-white'
                          }`}
                        >
                          <r.icon
                            className={`w-5 h-5 mx-auto mb-1.5 ${
                              formData.role === r.id ? 'text-primary' : 'text-text-tertiary'
                            }`}
                          />
                          <span
                            className={`text-xs font-semibold block ${
                              formData.role === r.id ? 'text-primary' : 'text-text-primary'
                            }`}
                          >
                            {r.label}
                          </span>
                          <span className="text-[10px] text-text-tertiary">{r.desc}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Full Name for register */}
            <AnimatePresence>
              {!isLogin && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <label className="label">Full Name / Organization Name</label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
                    <input
                      type="text"
                      value={formData.full_name}
                      onChange={(e) => updateField('full_name', e.target.value)}
                      placeholder="e.g. SIMAT University or Verifier Org"
                      className="input-field pl-10"
                      required
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Username */}
            <div>
              <label className="label">Username</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => updateField('username', e.target.value)}
                  placeholder={isLogin ? 'Enter your username' : 'Choose a unique username'}
                  className="input-field pl-10"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => updateField('password', e.target.value)}
                  placeholder="Password"
                  className="input-field pl-10 pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Wallet Address if institution */}
            <AnimatePresence>
              {!isLogin && formData.role === 'institution' && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <label className="label">Institution Wallet Address</label>
                  <div className="relative">
                    <Wallet className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
                    <input
                      type="text"
                      value={formData.wallet_address}
                      onChange={(e) => updateField('wallet_address', e.target.value)}
                      placeholder="0x..."
                      className="input-field pl-10 font-mono"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-3.5 text-base"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  {isLogin ? 'Sign In' : 'Create Organization Account'}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </motion.div>
      </div>
    </div>
  )
}