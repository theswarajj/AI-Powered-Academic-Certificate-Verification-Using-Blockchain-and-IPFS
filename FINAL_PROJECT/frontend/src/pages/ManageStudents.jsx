import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  Users,
  UserPlus,
  Search,
  Key,
  Copy,
  Check,
  Eye,
  EyeOff,
  Edit2,
  Trash2,
  ArrowLeft,
  GraduationCap,
  Sparkles,
  ShieldAlert,
  Loader2,
  X,
  FileCheck,
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'

function PasswordCell({ password }) {
  const [show, setShow] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(password)
    setCopied(true)
    toast.success('Password copied!')
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="flex items-center gap-1.5 font-mono text-xs">
      <span className="bg-base-elevated px-2 py-1 rounded border border-border-subtle min-w-[90px] text-center select-all">
        {show ? password : '••••••••'}
      </span>
      <button
        type="button"
        onClick={() => setShow(!show)}
        className="btn-ghost p-1 text-text-tertiary hover:text-text-primary"
        title={show ? 'Hide password' : 'Show password'}
      >
        {show ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
      </button>
      <button
        type="button"
        onClick={handleCopy}
        className="btn-ghost p-1 text-text-tertiary hover:text-emerald-600"
        title="Copy credential"
      >
        {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
      </button>
    </div>
  )
}

export default function ManageStudents() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()

  const [students, setStudents] = useState([])
  const [search, setSearch] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  // Create Modal
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [newStudent, setNewStudent] = useState({
    username: '',
    password: '',
    full_name: '',
    register_number: '',
  })

  // Edit Modal
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editLoading, setEditLoading] = useState(false)
  const [editingStudent, setEditingStudent] = useState(null)

  const fetchStudents = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/institution/students', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to fetch students')
      const data = await res.json()
      setStudents(data.students || [])
    } catch (err) {
      toast.error(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchStudents()
    }
  }, [isAuthenticated])

  if (!isAuthenticated || (user?.role !== 'institution' && user?.role !== 'admin')) {
    return (
      <div className="pt-24 pb-16 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-amber-50 flex items-center justify-center">
            <ShieldAlert className="w-7 h-7 text-amber-600" />
          </div>
          <h2 className="text-xl font-bold mb-2 text-text-primary">Access Denied</h2>
          <p className="text-text-secondary mb-6">
            Only university administrators can manage student login credentials.
          </p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary">
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const generateRandomPassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789'
    let pwd = ''
    for (let i = 0; i < 8; i++) {
      pwd += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return `Std@${pwd}`
  }

  const handleCreateStudent = async (e) => {
    e.preventDefault()
    if (!newStudent.username.trim() || !newStudent.password.trim()) {
      return toast.error('Username and password are required')
    }

    setCreateLoading(true)
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/institution/students', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newStudent),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to create student account')

      toast.success('Student account created successfully!')
      setCreateModalOpen(false)
      setNewStudent({ username: '', password: '', full_name: '', register_number: '' })
      fetchStudents()
    } catch (err) {
      toast.error(err.message)
    } finally {
      setCreateLoading(false)
    }
  }

  const handleUpdateStudent = async (e) => {
    e.preventDefault()
    if (!editingStudent) return

    setEditLoading(true)
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/institution/students/${editingStudent.username}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          password: editingStudent.new_password || editingStudent.current_password,
          full_name: editingStudent.full_name,
          register_number: editingStudent.register_number,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to update student')

      toast.success('Student credentials updated!')
      setEditModalOpen(false)
      setEditingStudent(null)
      fetchStudents()
    } catch (err) {
      toast.error(err.message)
    } finally {
      setEditLoading(false)
    }
  }

  const handleDeleteStudent = async (uname) => {
    if (!confirm(`Are you sure you want to delete student account "${uname}"?`)) return

    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/institution/students/${uname}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to delete')

      toast.success('Student account deleted')
      fetchStudents()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const filteredStudents = students.filter(
    (s) =>
      !search ||
      s.username?.toLowerCase().includes(search.toLowerCase()) ||
      s.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      s.register_number?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="section-container max-w-6xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/dashboard')} className="btn-ghost">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </button>
        </motion.div>

        {/* Title Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <span className="inline-block px-3 py-1 rounded-pill bg-primary-50 text-primary text-xs font-semibold mb-2 border border-primary-200">
              UNIVERSITY PORTAL
            </span>
            <h1 className="text-3xl font-bold text-text-primary">
              Student <span className="gradient-text">Login Credentials</span>
            </h1>
            <p className="text-text-secondary text-sm mt-1">
              Provide and control student login access. If a student changes their password, it updates here automatically.
            </p>
          </div>
          <button
            onClick={() => {
              setNewStudent({
                username: '',
                password: generateRandomPassword(),
                full_name: '',
                register_number: '',
              })
              setCreateModalOpen(true)
            }}
            className="btn-primary text-sm whitespace-nowrap gap-2 self-start md:self-auto"
          >
            <UserPlus className="w-4 h-4" /> Issue Student Credential
          </button>
        </div>

        {/* Auto-Generation Info Banner */}
        <div className="mb-6 p-4 rounded-2xl border border-indigo-200/80 bg-gradient-to-r from-indigo-50/70 via-purple-50/40 to-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-100 flex items-center justify-center shrink-0">
              <Sparkles className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-indigo-950 uppercase tracking-wide flex items-center gap-2">
                Automatic Credential Generation Active
                <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-200">
                  Live
                </span>
              </h4>
              <p className="text-xs text-text-secondary mt-0.5">
                Whenever you issue a certificate, student login User ID and temporary Password are generated automatically.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/issue')}
            className="btn-outline text-xs whitespace-nowrap shrink-0 border-indigo-200 hover:border-indigo-300 text-indigo-700 hover:bg-indigo-50"
          >
            Issue New Certificate
          </button>
        </div>

        {/* Search Bar */}
        <div className="glass-card p-4 mb-6 flex items-center justify-between gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by student name, register number, or login username..."
              className="input-field pl-10"
            />
          </div>
          <span className="text-xs text-text-tertiary font-medium whitespace-nowrap">
            {filteredStudents.length} Student Account{filteredStudents.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Students Table */}
        <div className="glass-card overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center">
              <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
              <p className="text-sm text-text-secondary">Loading student accounts...</p>
            </div>
          ) : filteredStudents.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-base-elevated flex items-center justify-center">
                <Users className="w-7 h-7 text-text-tertiary" />
              </div>
              <h3 className="font-semibold mb-1 text-text-primary">No Student Credentials Found</h3>
              <p className="text-text-secondary text-sm mb-4">
                {search
                  ? 'No students matched your search criteria.'
                  : 'You have not created any student login credentials yet.'}
              </p>
              <button
                onClick={() => {
                  setNewStudent({
                    username: '',
                    password: generateRandomPassword(),
                    full_name: '',
                    register_number: '',
                  })
                  setCreateModalOpen(true)
                }}
                className="btn-primary text-sm"
              >
                <UserPlus className="w-4 h-4" /> Issue First Student Credential
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border-subtle bg-base-elevated text-text-tertiary uppercase tracking-wider font-semibold">
                    <th className="py-3 px-4 text-left">Student</th>
                    <th className="py-3 px-4 text-left">Register Number</th>
                    <th className="py-3 px-4 text-left">Login Username</th>
                    <th className="py-3 px-4 text-left">Current Password</th>
                    <th className="py-3 px-4 text-center">Certificates</th>
                    <th className="py-3 px-4 text-left">Last Updated</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.map((s, idx) => (
                    <tr
                      key={s.username}
                      className="border-b border-border-subtle/50 hover:bg-base-elevated/70 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center font-bold text-primary">
                            {s.full_name?.charAt(0) || s.username?.charAt(0) || 'S'}
                          </div>
                          <div>
                            <span className="font-semibold text-text-primary text-sm block">
                              {s.full_name || '—'}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono font-medium text-text-secondary">
                        {s.register_number || '—'}
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold text-primary">
                        {s.username}
                      </td>
                      <td className="py-3 px-4">
                        <PasswordCell password={s.current_password} />
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {s.certificates_count} Cert{s.certificates_count !== 1 ? 's' : ''}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-text-tertiary">
                        {s.updated_at ? new Date(s.updated_at).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => {
                              setEditingStudent({ ...s, new_password: '' })
                              setEditModalOpen(true)
                            }}
                            className="btn-ghost p-1.5 text-text-tertiary hover:text-primary"
                            title="Edit or Reset Password"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteStudent(s.username)}
                            className="btn-ghost p-1.5 text-text-tertiary hover:text-red-500"
                            title="Delete Account"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal: Create Student */}
        <AnimatePresence>
          {createModalOpen && (
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
                      <GraduationCap className="w-4 h-4 text-primary" />
                    </div>
                    <h3 className="font-bold text-lg text-text-primary">Issue Student Credential</h3>
                  </div>
                  <button
                    onClick={() => setCreateModalOpen(false)}
                    className="btn-ghost p-1 text-text-tertiary hover:text-text-primary"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <form onSubmit={handleCreateStudent} className="space-y-4">
                  <div>
                    <label className="label">Student Full Name *</label>
                    <input
                      type="text"
                      value={newStudent.full_name}
                      onChange={(e) =>
                        setNewStudent({ ...newStudent, full_name: e.target.value })
                      }
                      placeholder="e.g. PRIYA RAMESH NAIR"
                      className="input-field"
                      required
                    />
                  </div>

                  <div>
                    <label className="label">University Register Number *</label>
                    <input
                      type="text"
                      value={newStudent.register_number}
                      onChange={(e) =>
                        setNewStudent({ ...newStudent, register_number: e.target.value })
                      }
                      placeholder="e.g. SPT22CS054"
                      className="input-field font-mono"
                      required
                    />
                    <p className="text-[11px] text-text-tertiary mt-1">
                      Certificates matching this register number will automatically appear in this student's portal.
                    </p>
                  </div>

                  <div>
                    <label className="label">Login Username *</label>
                    <input
                      type="text"
                      value={newStudent.username}
                      onChange={(e) =>
                        setNewStudent({ ...newStudent, username: e.target.value })
                      }
                      placeholder="e.g. priya_spt22"
                      className="input-field font-mono"
                      required
                    />
                  </div>

                  <div>
                    <label className="label">Initial Password *</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={newStudent.password}
                        onChange={(e) =>
                          setNewStudent({ ...newStudent, password: e.target.value })
                        }
                        placeholder="Password (min 6 chars)"
                        className="input-field font-mono flex-1"
                        required
                      />
                      <button
                        type="button"
                        onClick={() =>
                          setNewStudent({ ...newStudent, password: generateRandomPassword() })
                        }
                        className="btn-outline text-xs whitespace-nowrap gap-1"
                        title="Generate random password"
                      >
                        <Sparkles className="w-3.5 h-3.5" /> Random
                      </button>
                    </div>
                  </div>

                  <div className="flex gap-3 pt-4 border-t border-border-subtle">
                    <button
                      type="button"
                      onClick={() => setCreateModalOpen(false)}
                      className="btn-outline flex-1 text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={createLoading}
                      className="btn-primary flex-1 text-sm"
                    >
                      {createLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Account'}
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* Modal: Edit Student / Reset Password */}
        <AnimatePresence>
          {editModalOpen && editingStudent && (
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
                      <Key className="w-4 h-4 text-primary" />
                    </div>
                    <h3 className="font-bold text-lg text-text-primary">
                      Edit Student Credentials
                    </h3>
                  </div>
                  <button
                    onClick={() => setEditModalOpen(false)}
                    className="btn-ghost p-1 text-text-tertiary hover:text-text-primary"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <form onSubmit={handleUpdateStudent} className="space-y-4">
                  <div>
                    <label className="label">Login Username (Immutable)</label>
                    <input
                      type="text"
                      value={editingStudent.username}
                      disabled
                      className="input-field font-mono bg-base-elevated cursor-not-allowed opacity-75"
                    />
                  </div>

                  <div>
                    <label className="label">Student Full Name</label>
                    <input
                      type="text"
                      value={editingStudent.full_name}
                      onChange={(e) =>
                        setEditingStudent({ ...editingStudent, full_name: e.target.value })
                      }
                      className="input-field"
                    />
                  </div>

                  <div>
                    <label className="label">Register Number</label>
                    <input
                      type="text"
                      value={editingStudent.register_number}
                      onChange={(e) =>
                        setEditingStudent({
                          ...editingStudent,
                          register_number: e.target.value,
                        })
                      }
                      className="input-field font-mono"
                    />
                  </div>

                  <div>
                    <label className="label">Reset / Change Password</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={editingStudent.new_password}
                        onChange={(e) =>
                          setEditingStudent({
                            ...editingStudent,
                            new_password: e.target.value,
                          })
                        }
                        placeholder={editingStudent.current_password || 'Enter new password'}
                        className="input-field font-mono flex-1"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          setEditingStudent({
                            ...editingStudent,
                            new_password: generateRandomPassword(),
                          })
                        }
                        className="btn-outline text-xs whitespace-nowrap gap-1"
                      >
                        <Sparkles className="w-3.5 h-3.5" /> Random
                      </button>
                    </div>
                    <p className="text-[11px] text-text-tertiary mt-1">
                      Leave blank to keep the current password:{' '}
                      <span className="font-mono text-text-primary font-semibold">
                        {editingStudent.current_password}
                      </span>
                    </p>
                  </div>

                  <div className="flex gap-3 pt-4 border-t border-border-subtle">
                    <button
                      type="button"
                      onClick={() => setEditModalOpen(false)}
                      className="btn-outline flex-1 text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={editLoading}
                      className="btn-primary flex-1 text-sm"
                    >
                      {editLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Changes'}
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
