import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion, useMotionValue, useTransform, useSpring, useMotionTemplate } from 'framer-motion'
import {
  ShieldCheck,
  Hash,
  Shield,
  Database,
  Cpu,
  ArrowRight,
  Sparkles,
  Award,
  CheckCircle2,
  FileCheck,
  Lock,
  Layers,
  ChevronRight,
  Building2,
  ScanLine,
  Zap,
} from 'lucide-react'

const layersInfo = [
  {
    icon: Hash,
    gradient: 'gradient-hash',
    title: 'Cryptographic Hashing',
    desc: 'SHA-256 dual-hash verification ensures even a single byte change is detected instantly.',
    tag: 'Layer 1',
    metric: 'Bit-level Exact',
  },
  {
    icon: Shield,
    gradient: 'gradient-blockchain',
    title: 'Blockchain Immutability',
    desc: 'Every certificate is recorded on Ethereum Sepolia — tamper-proof and permanently verifiable.',
    tag: 'Layer 2',
    metric: 'Sepolia Block',
  },
  {
    icon: Database,
    gradient: 'gradient-ipfs',
    title: 'Decentralized Storage',
    desc: 'IPFS/Pinata ensures certificates survive permanently even if an issuing server goes offline.',
    tag: 'Layer 3',
    metric: 'Content Pinned',
  },
  {
    icon: Cpu,
    gradient: 'gradient-ai',
    title: 'AI Fraud Detection',
    desc: '20-feature ensemble ML with SHAP explainability — the AI tells you exactly WHY it decided.',
    tag: 'Layer 4',
    metric: 'Explainable XAI',
  },
]

const statsInfo = [
  { value: 4, label: 'Verification Layers', icon: ShieldCheck, suffix: '' },
  { value: 20, label: 'AI Features Analyzed', icon: Cpu, suffix: '' },
  { value: 7, label: 'Distinct Verdicts', icon: Award, suffix: '' },
  { value: 100, label: 'Explainable AI', icon: FileCheck, suffix: '%' },
]

const stepsInfo = [
  {
    step: '01',
    title: 'Upload Certificate',
    desc: 'Upload your academic certificate file (PNG, JPG, or PDF) and enter its unique Certificate ID.',
  },
  {
    step: '02',
    title: 'Multi-Layer Analysis',
    desc: 'Our system runs hash matching, blockchain verification, IPFS integrity check, and AI fraud detection simultaneously.',
  },
  {
    step: '03',
    title: 'Get Verdict & Report',
    desc: 'Receive a comprehensive verification report with an authentic risk score, confidence band, and full SHAP explanation.',
  },
]

function AnimatedCounter({ value, suffix = '' }) {
  const [isInView, setIsInView] = useState(false)
  const ref = useRef(null)
  const springVal = useSpring(0, { bounce: 0, duration: 2500 })
  const displayVal = useTransform(springVal, (current) => Math.floor(current))

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          springVal.set(value)
        }
      },
      { threshold: 0.5 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [value, springVal])

  return (
    <motion.span
      ref={ref}
      initial={{ opacity: 0, y: 10 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      className="text-4xl lg:text-5xl font-black text-slate-900 flex items-center justify-center tracking-tight"
    >
      <motion.span className="text-gradient-animated">{displayVal}</motion.span>
      <span className="text-indigo-600 ml-0.5">{suffix}</span>
    </motion.span>
  )
}

function SpotlightCard({ children, className = '' }) {
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  function handleMouseMove({ currentTarget, clientX, clientY }) {
    const { left, top } = currentTarget.getBoundingClientRect()
    mouseX.set(clientX - left)
    mouseY.set(clientY - top)
  }

  const spotlightBg = useMotionTemplate`
    radial-gradient(
      650px circle at ${mouseX}px ${mouseY}px,
      rgba(99, 102, 241, 0.08),
      transparent 80%
    )
  `

  return (
    <motion.div
      className={`relative overflow-hidden group bg-white border border-slate-200/90 rounded-2xl transition-all duration-300 hover:border-indigo-400 hover:shadow-[0_12px_32px_rgba(99,102,241,0.09)] hover:-translate-y-1 ${className}`}
      onMouseMove={handleMouseMove}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
    >
      <motion.div
        className="pointer-events-none absolute -inset-px rounded-2xl opacity-0 transition duration-300 group-hover:opacity-100"
        style={{ background: spotlightBg }}
      />
      <div className="relative z-10 p-6">{children}</div>
    </motion.div>
  )
}

export default function Landing() {
  return (
    <div className="pt-16 overflow-hidden">
      {/* Hero Section */}
      <section className="min-h-[92vh] pt-12 pb-24 flex items-center relative overflow-hidden">
        {/* Floating Ambient Glowing Light Orbs */}
        <motion.div
          animate={{
            x: [0, 25, 0],
            y: [0, -30, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{ repeat: Infinity, duration: 12, ease: 'easeInOut' }}
          className="absolute -top-10 -right-10 w-[550px] h-[550px] bg-gradient-to-br from-indigo-100/70 via-purple-100/50 to-transparent rounded-full blur-[100px] pointer-events-none -z-10"
        />
        <motion.div
          animate={{
            x: [0, -25, 0],
            y: [0, 30, 0],
            scale: [1, 1.08, 1],
          }}
          transition={{ repeat: Infinity, duration: 14, ease: 'easeInOut' }}
          className="absolute -bottom-20 -left-10 w-[450px] h-[450px] bg-gradient-to-tr from-cyan-100/60 via-blue-100/50 to-transparent rounded-full blur-[90px] pointer-events-none -z-10"
        />

        <div className="section-container relative z-10 w-full">
          <div className="max-w-4xl mx-auto text-center">
            {/* Live Trust Protocol Badge */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-[0_2px_12px_rgba(15,23,42,0.05)] mb-8 hover:border-indigo-300 transition-colors"
            >
              <span className="flex h-2.5 w-2.5 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
              </span>
              <span className="text-xs font-bold text-slate-800 tracking-wider uppercase">
                Institutional Trust
              </span>
              <span className="h-3 w-px bg-slate-200" />
              <span className="text-xs font-semibold text-indigo-600 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                4-Layer Verification Protocol
              </span>
            </motion.div>

            {/* Hero Main Heading */}
            <motion.h1
              initial={{ opacity: 0, y: 25 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[1.08] mb-6 text-slate-900"
            >
              Verify Certificates with{' '}
              <span className="text-gradient-animated block mt-2 font-black">
                Blockchain & AI
              </span>
            </motion.h1>

            {/* Subheading / Description */}
            <motion.p
              initial={{ opacity: 0, y: 25 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-lg lg:text-xl text-slate-600 max-w-2xl mx-auto mb-10 text-balance leading-relaxed font-normal"
            >
              Four independent verification layers — cryptographic hashing, blockchain records, decentralized storage, and explainable AI fraud detection — unite into one definitive verdict.
            </motion.p>

            {/* Hero Action Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 25 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              {/* Primary CTA */}
              <Link
                to="/verify"
                id="hero-verify-btn"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-xl text-base font-semibold text-white bg-gradient-to-r from-indigo-600 via-indigo-600 to-indigo-700 shadow-[0_10px_25px_-5px_rgba(99,102,241,0.4)] hover:shadow-[0_14px_30px_-5px_rgba(99,102,241,0.55)] hover:scale-[1.03] active:scale-[0.99] transition-all duration-300 group btn-shimmer"
              >
                <span>Verify a Certificate</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>

              {/* Secondary CTA: For Institutions - Prominently Visible & Styled */}
              <Link
                to="/auth"
                id="hero-institutions-btn"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-xl text-base font-semibold text-slate-900 bg-white border-2 border-slate-300/90 hover:border-indigo-500 hover:text-indigo-600 hover:bg-indigo-50/60 shadow-[0_2px_10px_rgba(15,23,42,0.04)] hover:shadow-[0_6px_20px_rgba(99,102,241,0.12)] hover:scale-[1.03] active:scale-[0.99] transition-all duration-300 group"
              >
                <Building2 className="w-4 h-4 text-indigo-600 group-hover:scale-110 transition-transform" />
                <span>For Institutions</span>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 group-hover:text-indigo-600 transition-all" />
              </Link>
            </motion.div>

            {/* Architecture Tech Pills */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.45 }}
              className="flex flex-wrap items-center justify-center gap-2.5 sm:gap-3.5 mt-10 text-slate-700"
            >
              {[
                { name: 'Ethereum Sepolia', icon: Lock, status: 'On-Chain' },
                { name: 'IPFS Pinata', icon: Database, status: 'Decentralized' },
                { name: 'EasyOCR Vision', icon: ScanLine, status: 'Automated' },
                { name: 'SHAP Explainable AI', icon: Sparkles, status: 'Transparent' },
              ].map((tech) => (
                <div
                  key={tech.name}
                  className="flex items-center gap-2 text-xs font-semibold bg-white/95 backdrop-blur-sm px-3.5 py-1.5 rounded-full border border-slate-200 shadow-[0_1px_4px_rgba(0,0,0,0.03)] hover:border-indigo-300 transition-colors"
                >
                  <tech.icon className="w-3.5 h-3.5 text-indigo-600" />
                  <span>{tech.name}</span>
                  <span className="text-[10px] text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded-full font-medium">
                    {tech.status}
                  </span>
                </div>
              ))}
            </motion.div>

            {/* Live Interactive Verification Preview Showcase */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.55 }}
              className="mt-16 max-w-4xl mx-auto relative text-left"
            >
              {/* Ambient Glow Halo */}
              <div className="absolute -inset-1.5 bg-gradient-to-r from-indigo-500/15 via-purple-500/15 to-cyan-500/15 rounded-[28px] blur-2xl opacity-75 -z-10" />

              {/* Floating Mini Badge Left */}
              <motion.div
                animate={{ y: [0, -6, 0] }}
                transition={{ repeat: Infinity, duration: 4, ease: 'easeInOut' }}
                className="hidden xl:flex items-center gap-2.5 absolute -left-12 top-16 bg-white/95 backdrop-blur-md border border-slate-200/90 px-4 py-2.5 rounded-2xl shadow-[0_10px_25px_rgba(15,23,42,0.08)] z-20"
              >
                <div className="w-8 h-8 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-900">Zero Tampering</p>
                  <p className="text-[10px] text-slate-500 font-medium">SHA-256 Bit-by-Bit Validated</p>
                </div>
              </motion.div>

              {/* Floating Mini Badge Right */}
              <motion.div
                animate={{ y: [0, 6, 0] }}
                transition={{ repeat: Infinity, duration: 4.5, ease: 'easeInOut', delay: 1 }}
                className="hidden xl:flex items-center gap-2.5 absolute -right-12 bottom-16 bg-white/95 backdrop-blur-md border border-slate-200/90 px-4 py-2.5 rounded-2xl shadow-[0_10px_25px_rgba(15,23,42,0.08)] z-20"
              >
                <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
                  <Shield className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-900">Sepolia Block #6.4M</p>
                  <p className="text-[10px] text-slate-500 font-medium">Permanent Blockchain Record</p>
                </div>
              </motion.div>

              {/* Main Simulation Window Card */}
              <div className="luxury-card overflow-hidden relative border-slate-200/90 shadow-[0_20px_50px_rgba(15,23,42,0.07)]">
                {/* Laser Sweep Effect */}
                <div className="laser-beam" />

                {/* Window Chrome Header */}
                <div className="px-6 py-3.5 bg-slate-50/90 border-b border-slate-200/80 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-rose-400" />
                    <div className="w-3 h-3 rounded-full bg-amber-400" />
                    <div className="w-3 h-3 rounded-full bg-emerald-400" />
                    <span className="ml-3 text-xs font-mono font-medium text-slate-500">
                      certverify://live-protocol-audit/CERT-2026-ETH-9842
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    All 4 Layers Verified
                  </div>
                </div>

                {/* Inner Mock Certificate Details */}
                <div className="p-6 lg:p-8">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center flex-shrink-0 text-indigo-600 shadow-sm">
                        <Award className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="text-base font-bold text-slate-900">
                            Bachelor of Science in Computer Science
                          </h4>
                          <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                            Verified Genuine
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                          Issued to <strong className="text-slate-800">Sarah Jenkins</strong> • Certificate ID: <span className="font-mono text-indigo-600 font-semibold">CERT-2026-ETH-9842</span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="px-3.5 py-1.5 bg-slate-50 rounded-xl border border-slate-200 text-right">
                        <span className="text-[10px] text-slate-400 block font-mono font-semibold">CONFIDENCE</span>
                        <span className="text-sm font-black font-mono text-emerald-600">99.8%</span>
                      </div>
                      <div className="px-3.5 py-1.5 bg-slate-50 rounded-xl border border-slate-200 text-right">
                        <span className="text-[10px] text-slate-400 block font-mono font-semibold">LATENCY</span>
                        <span className="text-sm font-black font-mono text-indigo-600">420ms</span>
                      </div>
                    </div>
                  </div>

                  {/* 4 Multi-Layer Checkpoint Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mt-6">
                    {/* Layer 1 */}
                    <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/90 hover:bg-white hover:border-indigo-200 hover:shadow-sm transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono font-bold text-indigo-600 uppercase">Layer 01</span>
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      </div>
                      <p className="text-xs font-bold text-slate-900">SHA-256 Digest</p>
                      <p className="text-[11px] font-mono text-slate-500 mt-1 truncate">0x7f83b1657ff1...</p>
                      <span className="mt-2.5 inline-block text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full">
                        Exact Byte Match
                      </span>
                    </div>

                    {/* Layer 2 */}
                    <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/90 hover:bg-white hover:border-blue-200 hover:shadow-sm transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono font-bold text-blue-600 uppercase">Layer 02</span>
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      </div>
                      <p className="text-xs font-bold text-slate-900">Ethereum Sepolia</p>
                      <p className="text-[11px] font-mono text-slate-500 mt-1 truncate">Block #6,419,203</p>
                      <span className="mt-2.5 inline-block text-[10px] font-semibold text-blue-700 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full">
                        On-Chain Confirmed
                      </span>
                    </div>

                    {/* Layer 3 */}
                    <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/90 hover:bg-white hover:border-cyan-200 hover:shadow-sm transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono font-bold text-cyan-600 uppercase">Layer 03</span>
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      </div>
                      <p className="text-xs font-bold text-slate-900">IPFS Pinata</p>
                      <p className="text-[11px] font-mono text-slate-500 mt-1 truncate">QmXoypizjW3Wkn...</p>
                      <span className="mt-2.5 inline-block text-[10px] font-semibold text-cyan-700 bg-cyan-50 border border-cyan-100 px-2 py-0.5 rounded-full">
                        Decentralized Pin
                      </span>
                    </div>

                    {/* Layer 4 */}
                    <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/90 hover:bg-white hover:border-purple-200 hover:shadow-sm transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono font-bold text-purple-600 uppercase">Layer 04</span>
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      </div>
                      <p className="text-xs font-bold text-slate-900">AI Fraud Engine</p>
                      <p className="text-[11px] font-mono text-slate-500 mt-1">Anomaly: 0.02%</p>
                      <span className="mt-2.5 inline-block text-[10px] font-semibold text-purple-700 bg-purple-50 border border-purple-100 px-2 py-0.5 rounded-full">
                        Genuine Geometry
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Three Simple Steps Section */}
      <section className="py-24 relative">
        <div className="section-container">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="inline-block px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-bold tracking-wider uppercase mb-4">
              HOW IT WORKS
            </span>
            <h2 className="text-3xl lg:text-5xl font-black mb-4 text-slate-900 tracking-tight">
              Three Simple Steps
            </h2>
            <p className="text-slate-600 max-w-xl mx-auto text-base lg:text-lg">
              From upload to verdict — the entire process is transparent, instantaneous, and explainable.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {stepsInfo.map((item, idx) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ delay: idx * 0.15, type: 'spring', stiffness: 50 }}
                className="luxury-card luxury-card-hover p-8 relative group bg-white border border-slate-200/90 text-left"
              >
                <div className="w-14 h-14 mb-6 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center transition-transform duration-500 group-hover:scale-110 group-hover:bg-indigo-100/70 group-hover:shadow-md">
                  <span className="text-xl font-black text-indigo-600">{item.step}</span>
                </div>
                <h3 className="text-lg font-bold mb-2.5 text-slate-900">{item.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-normal">{item.desc}</p>
                {idx < 2 && (
                  <div className="hidden md:block absolute top-10 -right-5 w-8 text-slate-300 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all duration-300 z-10">
                    <ArrowRight className="w-6 h-6" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Four Layers of Trust Section */}
      <section className="py-24 bg-slate-50/60 relative overflow-hidden border-y border-slate-200/60">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 60, repeat: Infinity, ease: 'linear' }}
          className="absolute -top-[25%] -right-[10%] w-[650px] h-[650px] rounded-full bg-gradient-to-l from-indigo-100/40 via-purple-100/20 to-transparent blur-[110px] pointer-events-none"
        />
        <div className="section-container relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="inline-block px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-bold tracking-wider uppercase mb-4">
              VERIFICATION LAYERS
            </span>
            <h2 className="text-3xl lg:text-5xl font-black mb-4 text-slate-900 tracking-tight">
              Four Layers of Trust
            </h2>
            <p className="text-slate-600 max-w-xl mx-auto text-base lg:text-lg">
              Each layer operates independently. All four must pass for a certificate to receive a verified verdict.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {layersInfo.map((layer) => (
              <SpotlightCard key={layer.title} className="p-7">
                <div className="flex items-center justify-between mb-5 relative z-10">
                  <div
                    className={`w-13 h-13 ${layer.gradient} rounded-2xl flex items-center justify-center shadow-md p-3`}
                  >
                    <layer.icon className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-[11px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-100 px-2.5 py-0.5 rounded-full shadow-sm">
                    {layer.tag}
                  </span>
                </div>
                <h3 className="text-base font-bold mb-2 text-slate-900 relative z-10">
                  {layer.title}
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed relative z-10">
                  {layer.desc}
                </p>
                <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-medium">
                  <span>Standard</span>
                  <span className="font-semibold text-indigo-600">{layer.metric}</span>
                </div>
              </SpotlightCard>
            ))}
          </div>
        </div>
      </section>

      {/* Numbers / Stats Section */}
      <section className="py-20 bg-white border-b border-slate-200/80">
        <div className="section-container">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
            {statsInfo.map((stat, idx) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1, type: 'spring' }}
                className="luxury-card luxury-card-hover text-center p-7 bg-white border border-slate-200/90 group"
              >
                <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center group-hover:scale-110 group-hover:bg-indigo-100/70 transition-all duration-300">
                  <stat.icon className="w-6 h-6 text-indigo-600" />
                </div>
                <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                <p className="text-sm text-slate-500 mt-2 font-semibold">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Explainable AI Showcase Section */}
      <section className="py-24 bg-slate-50/60 relative overflow-hidden">
        <div className="section-container relative z-10">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <span className="inline-block px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-bold tracking-wider uppercase mb-4">
                EXPLAINABLE AI
              </span>
              <h2 className="text-3xl lg:text-5xl font-black mb-6 text-slate-900 tracking-tight">
                Why <span className="text-gradient-animated">Explainable AI</span> Matters
              </h2>
              <p className="text-slate-600 mb-8 leading-relaxed text-lg">
                Our system doesn't just say "suspicious" — it shows you{' '}
                <strong className="text-slate-900 font-bold">
                  exactly which features
                </strong>{' '}
                triggered the decision and by how much. SHAP values decompose every prediction into human-readable, auditable explanations.
              </p>

              <div className="space-y-4">
                {[
                  { icon: Lock, text: 'Cryptographic proof — mathematical certainty, zero guesswork' },
                  { icon: FileCheck, text: 'Full transparency — inspect every factor behind the verdict' },
                  { icon: ShieldCheck, text: 'Multi-layer redundancy — no single point of failure' },
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.15 + i * 0.1 }}
                    className="flex items-start gap-4 p-3 rounded-xl bg-white border border-slate-200/80 shadow-sm"
                  >
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center flex-shrink-0">
                      <item.icon className="w-5 h-5 text-indigo-600" />
                    </div>
                    <span className="text-sm text-slate-700 leading-relaxed pt-2 font-medium">
                      {item.text}
                    </span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Model Output / SHAP Preview */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="luxury-card p-7 space-y-3 bg-white border border-slate-200/90 shadow-[0_20px_50px_rgba(15,23,42,0.07)] relative"
            >
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
                <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <span className="text-xs text-slate-500 block font-medium">
                    Model Output
                  </span>
                  <span className="text-sm text-slate-900 font-mono font-bold tracking-tight">
                    SHAP EXPLANATION AUDIT
                  </span>
                </div>
              </div>

              <div className="space-y-2.5">
                {[
                  { msg: 'Document structure matches accredited university template', val: -0.1175, dir: 'genuine' },
                  { msg: 'Institution cryptographic identifier matches authoritative registry', val: -0.102, dir: 'genuine' },
                  { msg: 'Font baseline variance within expected digital press tolerances', val: -0.071, dir: 'genuine' },
                  { msg: 'Compression artifact matrix indicates uniform camera sensor capture', val: -0.058, dir: 'genuine' },
                  { msg: 'Minor spatial displacement in secondary signature block', val: 0.0103, dir: 'suspicious' },
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 + i * 0.08, type: 'spring' }}
                    className="flex items-center gap-3 p-3 rounded-xl bg-slate-50/70 border border-slate-200/80 hover:bg-white hover:border-indigo-100 transition-colors"
                  >
                    <div
                      className={`w-1.5 h-8 rounded-full flex-shrink-0 ${
                        item.dir === 'genuine' ? 'bg-emerald-500' : 'bg-amber-500'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs text-slate-700 truncate block font-medium">
                        {item.msg}
                      </span>
                    </div>
                    <span
                      className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                        item.val < 0 ? 'text-emerald-700 bg-emerald-50' : 'text-amber-700 bg-amber-50'
                      }`}
                    >
                      {item.val > 0 ? '+' : ''}
                      {item.val.toFixed(4)}
                    </span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-white">
        <div className="section-container">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rounded-3xl p-12 md:p-16 text-center relative overflow-hidden bg-gradient-to-br from-indigo-600 via-indigo-600 to-violet-700 shadow-[0_25px_60px_-15px_rgba(99,102,241,0.45)]"
          >
            {/* Shimmer sheen */}
            <div className="absolute inset-0 bg-white/10 opacity-30 bg-grid-pattern pointer-events-none" />
            <div className="relative z-10 max-w-2xl mx-auto">
              <h2 className="text-3xl lg:text-5xl font-black mb-4 text-white drop-shadow-sm tracking-tight">
                Ready to Verify Any Certificate?
              </h2>
              <p className="text-indigo-100 mb-8 max-w-md mx-auto text-base lg:text-lg leading-relaxed">
                Upload any academic certificate and watch our 4-layer system analyze it in real-time.
              </p>
              <Link
                to="/verify"
                className="inline-flex items-center gap-2.5 px-10 py-4 bg-white text-indigo-600 font-bold rounded-xl text-base group hover:scale-105 active:scale-95 transition-all shadow-[0_10px_25px_rgba(0,0,0,0.15)] hover:shadow-2xl"
              >
                <span>Start Free Verification</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200/90 py-12 bg-slate-50/50">
        <div className="section-container">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl gradient-blockchain flex items-center justify-center shadow-sm">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <span className="font-extrabold text-slate-900 text-lg">
                Cert<span className="text-indigo-600">Verify</span>
              </span>
            </div>
            <div className="text-center md:text-right">
              <p className="text-sm text-slate-600 font-semibold">
                AI-Powered Academic Certificate Verification Protocol
              </p>
              <p className="text-xs text-slate-500 mt-1 font-medium">
                Built with Ethereum Sepolia • IPFS Pinata • 20-Feature Ensemble ML • SHAP Explainable XAI
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
