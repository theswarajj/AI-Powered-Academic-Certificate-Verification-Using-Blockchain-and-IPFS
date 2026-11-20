import { motion } from 'framer-motion'
import {
  CheckCircle2,
  HelpCircle,
  XCircle,
  FileX,
  FileWarning,
  AlertTriangle,
  Info,
} from 'lucide-react'

const VERDICT_CONFIG = {
  VERIFIED: {
    icon: CheckCircle2,
    label: 'VERIFIED & PERFECT',
    subtitle: 'All checks passed — uploaded certificate information perfectly matches blockchain record',
    className: 'verdict-verified',
    color: '#059669',
    bgFrom: '#ECFDF5',
  },
  NOT_FOUND: {
    icon: HelpCircle,
    label: 'NOT FOUND',
    subtitle: 'No blockchain record exists for this certificate',
    className: 'verdict-not_found',
    color: '#6B7280',
    bgFrom: '#F9FAFB',
  },
  REVOKED: {
    icon: XCircle,
    label: 'REVOKED',
    subtitle: 'This certificate was revoked by the issuing institution',
    className: 'verdict-revoked',
    color: '#DC2626',
    bgFrom: '#FEF2F2',
  },
  HASH_MISMATCH: {
    icon: FileX,
    label: 'HASH MISMATCH',
    subtitle: 'The file has been modified since it was originally issued',
    className: 'verdict-hash_mismatch',
    color: '#DC2626',
    bgFrom: '#FEF2F2',
  },
  CONTENT_MISMATCH: {
    icon: FileWarning,
    label: 'CONTENT MISMATCH',
    subtitle: 'Certificate content was altered — data has been changed',
    className: 'verdict-content_mismatch',
    color: '#B91C1C',
    bgFrom: '#FEF2F2',
  },
  REQUIRES_INVESTIGATION: {
    icon: AlertTriangle,
    label: 'REQUIRES INVESTIGATION',
    subtitle: 'AI analysis flagged potential issues — manual review recommended',
    className: 'verdict-requires_investigation',
    color: '#D97706',
    bgFrom: '#FFFBEB',
  },
  PARTIALLY_VERIFIED: {
    icon: Info,
    label: 'PARTIALLY VERIFIED',
    subtitle: 'Some verification layers were unavailable',
    className: 'verdict-partially_verified',
    color: '#2563EB',
    bgFrom: '#EFF6FF',
  },
}

export default function VerdictBanner({ verdict }) {
  const config = VERDICT_CONFIG[verdict] || VERDICT_CONFIG.NOT_FOUND
  const Icon = config.icon

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: -10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.5, type: 'spring', stiffness: 200 }}
      className={`verdict-banner ${config.className} relative overflow-hidden`}
    >
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(${config.color} 1px, transparent 1px)`,
          backgroundSize: '16px 16px',
        }}
      />
      <div className="relative z-10 text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 300 }}
          className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center"
          style={{ background: `${config.color}15` }}
        >
          <Icon className="w-8 h-8" style={{ color: config.color }} />
        </motion.div>
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-2xl font-bold tracking-tight mb-2"
        >
          {config.label}
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-sm opacity-80 max-w-md mx-auto"
        >
          {config.subtitle}
        </motion.p>
      </div>
    </motion.div>
  )
}
