import { motion, AnimatePresence } from 'framer-motion'
import { Hash, Shield, Database, Cpu, Loader2, Check, X } from 'lucide-react'

const layers = [
  { id: 1, name: 'Hash', icon: Hash, gradient: 'gradient-hash', desc: 'Cryptographic Verification' },
  { id: 2, name: 'Blockchain', icon: Shield, gradient: 'gradient-blockchain', desc: 'On-Chain Record Check' },
  { id: 3, name: 'IPFS', icon: Database, gradient: 'gradient-ipfs', desc: 'Storage Integrity' },
  { id: 4, name: 'AI', icon: Cpu, gradient: 'gradient-ai', desc: 'Fraud Detection & XAI' },
]

function StatusIcon({ status }) {
  if (status === 'running') {
    return <Loader2 className="w-5 h-5 text-white animate-spin" />
  }
  if (status === 'done') {
    return (
      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 400 }}>
        <Check className="w-5 h-5 text-white" />
      </motion.div>
    )
  }
  if (status === 'error') {
    return <X className="w-5 h-5 text-white" />
  }
  return null
}

export default function LayerProgress({ progress = {} }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {layers.map((layer, index) => {
        const layerData = progress[layer.id] || {}
        const status = layerData.status || 'waiting'
        const isRunning = status === 'running'
        const isDone = status === 'done'
        const isError = status === 'error'

        return (
          <motion.div
            key={layer.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1, duration: 0.4 }}
            className={`glass-card p-5 text-center transition-all duration-500 ${
              isRunning ? 'ring-2 ring-primary/30 shadow-primary' : ''
            } ${isDone ? 'border-emerald-200' : ''} ${isError ? 'border-red-200' : ''}`}
          >
            <div
              className={`w-14 h-14 mx-auto mb-3 rounded-xl ${layer.gradient} 
              flex items-center justify-center transition-all duration-300 shadow-md
              ${isRunning ? 'scale-110 shadow-lg' : ''} ${isDone ? 'opacity-100' : 'opacity-70'}
              ${status === 'waiting' ? 'grayscale opacity-30' : ''}`}
            >
              {status === 'waiting' ? (
                <layer.icon className="w-6 h-6 text-white/70" />
              ) : (
                <StatusIcon status={status} />
              )}
            </div>

            <h3
              className={`font-semibold text-sm mb-0.5 ${
                isDone
                  ? 'text-text-primary'
                  : status === 'waiting'
                  ? 'text-text-tertiary'
                  : 'text-text-primary'
              }`}
            >
              {layer.name}
            </h3>
            <p className="text-[11px] text-text-tertiary">{layer.desc}</p>

            <AnimatePresence mode="wait">
              <motion.div
                key={status}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className="mt-3"
              >
                {status === 'waiting' && (
                  <span className="badge bg-base-elevated text-text-tertiary border border-border-subtle">
                    Pending
                  </span>
                )}
                {status === 'running' && (
                  <span className="badge bg-primary-50 text-primary border border-primary-200">
                    Processing...
                  </span>
                )}
                {status === 'done' && (
                  <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Complete
                  </span>
                )}
                {status === 'error' && (
                  <span className="badge bg-red-50 text-red-700 border border-red-200">
                    Failed
                  </span>
                )}
              </motion.div>
            </AnimatePresence>

            {isDone && layerData.data && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-2 text-[10px] text-text-tertiary space-y-0.5 font-medium"
              >
                {layer.id === 1 && layerData.data.layer_available && (
                  <div className={layerData.data.file_hash_match ? 'text-emerald-600' : 'text-red-600'}>
                    {layerData.data.file_hash_match ? '✓ Hash matches' : '✗ Hash mismatch'}
                  </div>
                )}
                {layer.id === 2 && (
                  <div className={layerData.data.record_exists ? 'text-emerald-600' : 'text-text-tertiary'}>
                    {layerData.data.record_exists ? '✓ Record found' : '✗ Not found'}
                  </div>
                )}
                {layer.id === 3 && (
                  <div className={layerData.data.file_available ? 'text-emerald-600' : 'text-text-tertiary'}>
                    {layerData.data.file_available ? '✓ Available' : '— Unavailable'}
                  </div>
                )}
                {layer.id === 4 && (
                  <div
                    className={
                      layerData.data.final_ai_verdict === 'LIKELY_GENUINE'
                        ? 'text-emerald-600'
                        : 'text-amber-600'
                    }
                  >
                    {layerData.data.fraud_probability_pct}% fraud probability
                  </div>
                )}
              </motion.div>
            )}
          </motion.div>
        )
      })}
    </div>
  )
}
