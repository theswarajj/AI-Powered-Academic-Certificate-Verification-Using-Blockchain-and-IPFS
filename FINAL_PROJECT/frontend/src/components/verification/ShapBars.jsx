import { motion } from 'framer-motion'

function ShapBarItem({ explanation, maxAbsShap, index, color, bgColor, barBg }) {
  const percentage = Math.min((Math.abs(explanation.shap_value) / maxAbsShap) * 100, 100)

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="rounded-xl p-3 border border-border-subtle bg-white"
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-text-secondary leading-snug flex-1">
          {explanation.message}
        </span>
        <span
          className="text-[10px] font-mono ml-2 whitespace-nowrap font-semibold"
          style={{ color }}
        >
          SHAP: {explanation.shap_value > 0 ? '+' : ''}
          {explanation.shap_value.toFixed(4)}
        </span>
      </div>

      <div className="h-2 w-full rounded-full overflow-hidden" style={{ background: barBg }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.6, delay: index * 0.05 + 0.2, ease: 'easeOut' }}
          className="h-full rounded-full"
          style={{ background: color }}
        />
      </div>

      <div className="flex items-center justify-between mt-1.5">
        <span className="text-[10px] font-mono text-text-tertiary">
          {explanation.feature}
        </span>
        <span className="text-[10px] font-mono text-text-tertiary">
          val: {typeof explanation.value === 'number' ? explanation.value.toFixed(2) : explanation.value}
        </span>
      </div>
    </motion.div>
  )
}

export default function ShapBars({ explanations = [] }) {
  if (!explanations.length) return null

  const maxAbsShap = Math.max(...explanations.map((e) => Math.abs(e.shap_value)), 0.01)
  const suspicious = explanations.filter((e) => e.pushes_toward === 'suspicious')
  const genuine = explanations.filter((e) => e.pushes_toward === 'genuine')

  return (
    <div className="space-y-6">
      {suspicious.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-red-600 mb-3 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
            Pushes Toward Suspicious ({suspicious.length})
          </h4>
          <div className="space-y-2">
            {suspicious.map((exp, idx) => (
              <ShapBarItem
                key={exp.feature}
                explanation={exp}
                maxAbsShap={maxAbsShap}
                index={idx}
                color="#DC2626"
                bgColor="rgba(254, 242, 242, 1)"
                barBg="rgba(254, 226, 226, 1)"
              />
            ))}
          </div>
        </div>
      )}

      {genuine.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-emerald-600 mb-3 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            Pushes Toward Genuine ({genuine.length})
          </h4>
          <div className="space-y-2">
            {genuine.map((exp, idx) => (
              <ShapBarItem
                key={exp.feature}
                explanation={exp}
                maxAbsShap={maxAbsShap}
                index={idx}
                color="#059669"
                bgColor="rgba(236, 253, 245, 1)"
                barBg="rgba(209, 250, 229, 1)"
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
