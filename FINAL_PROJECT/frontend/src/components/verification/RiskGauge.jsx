import { useEffect, useRef } from 'react'
import { motion, useMotionValue, useTransform, animate } from 'framer-motion'

const CONFIDENCE_BANDS = {
  HIGH_CONFIDENCE_GENUINE: { label: 'High Confidence', color: '#059669' },
  MODERATE_CONFIDENCE: { label: 'Moderate Confidence', color: '#D97706' },
  ELEVATED_RISK: { label: 'Elevated Risk', color: '#DC2626' },
  HIGH_RISK: { label: 'High Risk', color: '#B91C1C' },
}

export default function RiskGauge({ score = 0, band = 'HIGH_CONFIDENCE_GENUINE', size = 220 }) {
  const progress = useMotionValue(0)
  const displayScore = useMotionValue(0)
  const scoreRef = useRef(null)

  const config = CONFIDENCE_BANDS[band] || CONFIDENCE_BANDS.MODERATE_CONFIDENCE
  const cx = size / 2
  const cy = size / 2
  const radius = (size - 30) / 2
  const circumference = Math.PI * radius
  const gradientId = `risk-gradient-${score}`

  useEffect(() => {
    const controls = animate(displayScore, score, {
      duration: 1.2,
      ease: 'easeInOut',
      onUpdate: (latest) => {
        if (scoreRef.current) {
          scoreRef.current.textContent = Math.round(latest)
        }
      },
    })
    const strokeAnim = animate(progress, score / 100, {
      duration: 1.2,
      ease: 'easeInOut',
    })
    return () => {
      controls.stop()
      strokeAnim.stop()
    }
  }, [score, progress, displayScore])

  const polarToCartesian = (angle) => {
    return {
      x: cx + radius * Math.cos(angle),
      y: cy - radius * Math.sin(angle),
    }
  }

  const describeArc = (startAngle, endAngle) => {
    const start = polarToCartesian(startAngle)
    const end = polarToCartesian(endAngle)
    const largeArcFlag = endAngle - startAngle > Math.PI ? 1 : 0
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`
  }

  const strokeDashoffset = useTransform(progress, [0, 1], [circumference, 0])
  const needleRotation = useTransform(progress, [0, 1], [-90, 90])

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center"
    >
      <svg width={size} height={size / 2 + 60} viewBox={`0 0 ${size} ${size / 2 + 60}`}>
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#059669" />
            <stop offset="40%" stopColor="#D97706" />
            <stop offset="70%" stopColor="#DC2626" />
            <stop offset="100%" stopColor="#B91C1C" />
          </linearGradient>
        </defs>

        {/* Track */}
        <path d={describeArc(Math.PI, 0)} className="risk-gauge-track" />

        {/* Animated fill */}
        <motion.path
          d={describeArc(Math.PI, 0)}
          stroke={`url(#${gradientId})`}
          className="risk-gauge-fill"
          strokeDasharray={circumference}
          style={{ strokeDashoffset }}
        />

        {/* Scale labels */}
        <text x="10" y={cy + 15} style={{ fontSize: '10px', fill: '#9CA3AF', fontFamily: 'Inter' }}>
          0
        </text>
        <text x={size - 20} y={cy + 15} style={{ fontSize: '10px', fill: '#9CA3AF', fontFamily: 'Inter' }}>
          100
        </text>

        {/* Needle */}
        <motion.g style={{ originX: '50%', originY: '50%', rotate: needleRotation }}>
          <circle cx={cx} cy={cy} r={radius} fill="none" stroke="none" />
          <polygon
            points={`${cx - 4},${cy} ${cx + 4},${cy} ${cx},${cy - radius + 15}`}
            fill={config.color}
          />
          <circle cx={cx} cy={cy} r="7" fill={config.color} />
          <circle cx={cx} cy={cy} r="3" fill="white" />
        </motion.g>

        {/* Central Score */}
        <text
          x={cx}
          y={cy + 36}
          textAnchor="middle"
          style={{ fontSize: '36px', fontWeight: 700, fontFamily: 'Inter', fill: '#111827' }}
        >
          <tspan ref={scoreRef}>0</tspan>
        </text>
        <text
          x={cx}
          y={cy + 52}
          textAnchor="middle"
          style={{ fontSize: '11px', fontWeight: 500, fontFamily: 'Inter', fill: '#9CA3AF' }}
        >
          / 100 RISK
        </text>
      </svg>

      {/* Confidence Pill */}
      <div
        className="flex items-center gap-2 mt-1 px-3 py-1.5 rounded-pill"
        style={{ background: `${config.color}10` }}
      >
        <div className="w-2.5 h-2.5 rounded-full" style={{ background: config.color }} />
        <span className="text-sm font-semibold" style={{ color: config.color }}>
          {config.label}
        </span>
      </div>
    </motion.div>
  )
}
