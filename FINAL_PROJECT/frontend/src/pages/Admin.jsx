import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import {
  Sliders,
  Activity,
  Award,
  Search,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import { useAuthStore, apiFetch } from '@/lib/store'

const VERDICT_COLORS = {
  VERIFIED: '#059669',
  NOT_FOUND: '#6B7280',
  REVOKED: '#DC2626',
  HASH_MISMATCH: '#DC2626',
  CONTENT_MISMATCH: '#B91C1C',
  REQUIRES_INVESTIGATION: '#D97706',
  PARTIALLY_VERIFIED: '#2563EB',
}

function AdminStats() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => apiFetch('/admin/stats'),
    refetchInterval: 30000,
  })

  if (isLoading || !data) {
    return (
      <div className="grid md:grid-cols-3 gap-6 mb-10">
        {[1, 2, 3].map((i) => (
          <div key={i} className="glass-card p-6 animate-pulse">
            <div className="h-4 bg-base-elevated rounded w-1/2 mb-3" />
            <div className="h-8 bg-base-elevated rounded w-1/3" />
          </div>
        ))}
      </div>
    )
  }

  const verdictData = Object.entries(data.verdicts || {}).map(([key, val]) => ({
    name: key.replace(/_/g, ' '),
    value: val,
    color: VERDICT_COLORS[key] || '#6B7280',
  }))

  return (
    <div className="space-y-6 mb-10">
      <div className="grid md:grid-cols-3 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
              <Sliders className="w-5 h-5 text-primary" />
            </div>
            <p className="text-sm text-text-tertiary font-medium">Total Verifications</p>
          </div>
          <p className="text-3xl font-bold gradient-text">{data.total_verifications || 0}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center">
              <Activity className="w-5 h-5 text-amber-600" />
            </div>
            <p className="text-sm text-text-tertiary font-medium">Average Risk Score</p>
          </div>
          <p className="text-3xl font-bold">
            <span className={data.avg_risk <= 30 ? 'text-emerald-600' : 'text-amber-600'}>
              {data.avg_risk || 0}
            </span>
            <span className="text-base text-text-tertiary font-normal">/100</span>
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <Award className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-sm text-text-tertiary font-medium">Unique Verdicts</p>
          </div>
          <p className="text-3xl font-bold text-primary">
            {Object.keys(data.verdicts || {}).length}
          </p>
        </motion.div>
      </div>

      {verdictData.length > 0 && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Donut Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card p-6"
          >
            <h3 className="text-sm font-semibold text-text-primary mb-4">Verdict Distribution</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={verdictData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                  animationBegin={0}
                  animationDuration={1000}
                >
                  {verdictData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.color} stroke="white" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '12px',
                    color: '#111827',
                    fontSize: '12px',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap gap-3 justify-center mt-2">
              {verdictData.map((entry) => (
                <div key={entry.name} className="flex items-center gap-1.5 text-[10px] text-text-secondary font-medium">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: entry.color }} />
                  {entry.name} ({entry.value})
                </div>
              ))}
            </div>
          </motion.div>

          {/* Bar Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-card p-6"
          >
            <h3 className="text-sm font-semibold text-text-primary mb-4">Verdicts Breakdown</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={verdictData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis type="number" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#6B7280', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '12px',
                    color: '#111827',
                    fontSize: '12px',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
                  }}
                />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} animationDuration={1000}>
                  {verdictData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        </div>
      )}
    </div>
  )
}

function AuditLog() {
  const [page, setPage] = useState(1)
  const [filter, setFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['audit-log', page],
    queryFn: () => apiFetch(`/admin/audit-log?page=${page}&per_page=15`),
  })

  const entries = (data?.entries || []).filter(
    (item) => !filter || JSON.stringify(item).toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-text-primary">Verification Audit Log</h3>
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-tertiary" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter logs..."
            className="input-field text-xs py-2 pl-9"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 bg-base-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-text-tertiary text-sm">No audit log entries found</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="text-left py-2.5 px-3 text-text-tertiary font-semibold uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="text-left py-2.5 px-3 text-text-tertiary font-semibold uppercase tracking-wider">
                    Cert ID
                  </th>
                  <th className="text-left py-2.5 px-3 text-text-tertiary font-semibold uppercase tracking-wider">
                    Verdict
                  </th>
                  <th className="text-left py-2.5 px-3 text-text-tertiary font-semibold uppercase tracking-wider">
                    Risk
                  </th>
                  <th className="text-left py-2.5 px-3 text-text-tertiary font-semibold uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-border-subtle/50 hover:bg-base-elevated transition-colors"
                  >
                    <td className="py-2.5 px-3 font-mono text-text-tertiary whitespace-nowrap">
                      {entry.timestamp || '—'}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-primary font-semibold">
                      {entry.cert_id || '—'}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className="badge text-[10px] border"
                        style={{
                          background: `${VERDICT_COLORS[entry.verdict] || '#6B7280'}10`,
                          color: VERDICT_COLORS[entry.verdict] || '#6B7280',
                          borderColor: `${VERDICT_COLORS[entry.verdict] || '#6B7280'}30`,
                        }}
                      >
                        {entry.verdict || '—'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-text-primary">
                      {entry.risk || '—'}
                    </td>
                    <td className="py-2.5 px-3 text-text-tertiary max-w-xs truncate">
                      {entry.file || entry.raw?.split('|').pop() || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-4 pt-4 border-t border-border-subtle">
            <span className="text-xs text-text-tertiary font-medium">
              Page {data?.page || 1} — {data?.total || 0} total entries
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="btn-ghost text-xs disabled:opacity-30"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={entries.length < 15}
                className="btn-ghost text-xs disabled:opacity-30"
              >
                Next <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </>
      )}
    </motion.div>
  )
}

export default function Admin() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return (
      <div className="pt-24 pb-16 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-amber-50 flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-amber-600" />
          </div>
          <h2 className="text-xl font-bold mb-2 text-text-primary">Authentication Required</h2>
          <p className="text-text-secondary mb-6">Please sign in to access the admin panel.</p>
          <button onClick={() => navigate('/auth')} className="btn-primary">
            Sign In <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="section-container">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <span className="inline-block px-3 py-1 rounded-pill bg-primary-50 text-primary text-xs font-semibold mb-4 border border-primary-200">
            ADMIN PANEL
          </span>
          <h1 className="text-3xl font-bold mb-2 text-text-primary">System Analytics</h1>
          <p className="text-text-secondary mb-8">
            Verification statistics, audit logs, and monitoring
          </p>
        </motion.div>

        <AdminStats />
        <AuditLog />
      </div>
    </div>
  )
}