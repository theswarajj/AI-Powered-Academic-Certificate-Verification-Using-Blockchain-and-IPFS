import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  ArrowLeft,
  Download,
  FileText,
  Hash,
  Shield,
  Database,
  Cpu,
  Check,
  Copy,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { useVerificationStore } from '@/lib/store'
import VerdictBanner from '@/components/verification/VerdictBanner'
import RiskGauge from '@/components/verification/RiskGauge'
import ShapBars from '@/components/verification/ShapBars'

const ETHERSCAN_BASE = 'https://sepolia.etherscan.io/address/'
const PINATA_BASE = 'https://gateway.pinata.cloud/ipfs/'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button onClick={handleCopy} className="btn-ghost p-1.5" title="Copy">
      {copied ? (
        <Check className="w-3.5 h-3.5 text-emerald-600" />
      ) : (
        <Copy className="w-3.5 h-3.5 text-text-tertiary" />
      )}
    </button>
  )
}

function LayerSection({ title, icon: Icon, gradient, children, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card overflow-hidden"
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 p-4 hover:bg-base-elevated transition-colors"
      >
        <div className={`w-9 h-9 ${gradient} rounded-xl flex items-center justify-center shadow-sm`}>
          <Icon className="w-4.5 h-4.5 text-white" />
        </div>
        <span className="font-semibold text-sm flex-1 text-left text-text-primary">{title}</span>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-text-tertiary" />
        ) : (
          <ChevronDown className="w-4 h-4 text-text-tertiary" />
        )}
      </button>
      {isOpen && <div className="px-4 pb-4 border-t border-border-subtle pt-4">{children}</div>}
    </motion.div>
  )
}

function DetailRow({ label, value, mono = false, status, link }) {
  return (
    <div className="flex items-start justify-between py-2 border-b border-border-subtle/50 last:border-0">
      <span className="text-xs text-text-tertiary font-medium">{label}</span>
      <div className="flex items-center gap-1.5 max-w-[60%] justify-end">
        {status === true && <span className="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0" />}
        {status === false && <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />}
        <span
          className={`text-xs text-right ${
            mono ? 'font-mono text-text-secondary' : 'text-text-primary font-medium'
          } truncate`}
        >
          {value || '—'}
        </span>
        {mono && value && <CopyButton text={value} />}
        {link && (
          <a
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-ghost p-1.5 text-primary"
          >
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  )
}

export default function Results() {
  const navigate = useNavigate()
  const { result } = useVerificationStore()

  if (!result) {
    return (
      <div className="pt-24 pb-16 min-h-screen">
        <div className="section-container max-w-2xl text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-base-elevated flex items-center justify-center">
            <FileText className="w-8 h-8 text-text-tertiary" />
          </div>
          <h1 className="text-2xl font-bold mb-4 text-text-primary">No Verification Result</h1>
          <p className="text-text-secondary mb-8">Run a verification first to see results here.</p>
          <button onClick={() => navigate('/verify')} className="btn-primary">
            <ArrowLeft className="w-4 h-4" /> Go to Verify
          </button>
        </div>
      </div>
    )
  }

  const {
    verdict,
    risk_score,
    confidence_band,
    fields,
    hash,
    blockchain,
    ipfs,
    ai,
    cert_id,
    layers_checked,
    risk_breakdown,
  } = result

  const handleDownloadPdf = async () => {
    try {
      const html2pdfModule = await import('html2pdf.js')
      const html2pdf = html2pdfModule.default || html2pdfModule
      const element = document.getElementById('report-content')
      const opt = {
        margin: [0.5, 0.5],
        filename: `${cert_id}_verification_report.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
      }

      const buttons = element.querySelectorAll('button')
      buttons.forEach((btn) => (btn.style.display = 'none'))

      html2pdf()
        .set(opt)
        .from(element)
        .save()
        .then(() => {
          buttons.forEach((btn) => (btn.style.display = ''))
          toast.success('PDF Report downloaded')
        })
    } catch {
      toast.error('Failed to generate PDF')
    }
  }

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div id="report-content" className="section-container max-w-4xl">
        {/* Actions header */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/verify')} className="btn-ghost">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <div className="flex-1" />
          <button onClick={handleDownloadPdf} className="btn-outline text-sm">
            <Download className="w-4 h-4" /> Download Report
          </button>
        </motion.div>

        {/* Verdict Banner */}
        <VerdictBanner verdict={verdict} />

        {/* Risk Gauge & Meta Info */}
        <div className="grid lg:grid-cols-2 gap-6 mt-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6 flex flex-col items-center justify-center"
          >
            <RiskGauge score={risk_score} band={confidence_band} />
            <div className="mt-4 w-full grid grid-cols-4 gap-2">
              {risk_breakdown &&
                Object.entries(risk_breakdown).map(([layerName, data]) => (
                  <div
                    key={layerName}
                    className="text-center p-2 rounded-xl bg-base-elevated border border-border-subtle"
                  >
                    <span className="text-[10px] text-text-tertiary block capitalize font-medium">
                      {layerName}
                    </span>
                    <span
                      className={`text-xs font-bold ${
                        data.available
                          ? data.risk === 0
                            ? 'text-emerald-600'
                            : 'text-red-600'
                          : 'text-text-tertiary'
                      }`}
                    >
                      {data.available ? `${data.risk}/${data.max}` : 'N/A'}
                    </span>
                  </div>
                ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card p-6"
          >
            <h3 className="text-sm font-semibold mb-4 text-text-primary flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" /> Certificate Information
            </h3>
            <div className="space-y-0">
              <DetailRow label="Certificate ID" value={cert_id} mono={true} />
              <DetailRow label="Student Name" value={fields?.student_name} />
              <DetailRow label="Degree" value={fields?.degree} />
              <DetailRow label="Register No." value={fields?.register_number} mono={true} />
              <DetailRow label="Issue Date" value={fields?.issue_date} />
              <DetailRow
                label="OCR Confidence"
                value={result.ocr_confidence ? `${result.ocr_confidence}%` : '—'}
              />
              <DetailRow label="Layers Checked" value={`${layers_checked}/4`} />
            </div>
          </motion.div>
        </div>

        {/* Detailed 4-Layer Breakdown */}
        <div className="space-y-3 mt-8">
          {/* Layer 1: Hash */}
          <LayerSection title="Layer 1: Hash Verification" icon={Hash} gradient="gradient-hash" defaultOpen={true}>
            <div className="space-y-0">
              <DetailRow
                label="Certificate Information vs Blockchain"
                value={
                  hash?.layer_available
                    ? hash.content_hash_match
                      ? 'PERFECT MATCH'
                      : 'MISMATCH'
                    : 'Unavailable'
                }
                status={hash?.layer_available ? hash.content_hash_match : undefined}
              />
              <DetailRow
                label="Original File Match"
                value={
                  hash?.layer_available
                    ? hash.file_hash_match
                      ? 'PERFECT MATCH'
                      : 'MISMATCH'
                    : 'Unavailable'
                }
                status={hash?.file_hash_match}
              />
              <DetailRow label="Computed File Hash" value={hash?.file_hash_computed} mono={true} />
              <DetailRow label="On-Chain File Hash" value={hash?.onchain_file_hash} mono={true} />
              <DetailRow label="Computed Content Hash" value={hash?.content_hash_computed} mono={true} />
              <DetailRow label="On-Chain Content Hash" value={hash?.onchain_content_hash} mono={true} />
            </div>
          </LayerSection>

          {/* Layer 2: Blockchain */}
          <LayerSection
            title="Layer 2: Blockchain Verification"
            icon={Shield}
            gradient="gradient-blockchain"
            defaultOpen={true}
          >
            <div className="space-y-0">
              <DetailRow
                label="Record Exists"
                value={blockchain?.record_exists ? 'Yes' : 'No'}
                status={blockchain?.record_exists}
              />
              <DetailRow
                label="Revoked"
                value={blockchain?.revoked ? 'REVOKED' : 'Not Revoked'}
                status={blockchain?.revoked === false}
              />
              <DetailRow
                label="Issuer Address"
                value={blockchain?.issuer_address}
                mono={true}
                link={blockchain?.issuer_address ? `${ETHERSCAN_BASE}${blockchain.issuer_address}` : null}
              />
              <DetailRow label="On-Chain Date" value={blockchain?.issuance_date} />
              <DetailRow
                label="Timestamp Coherent"
                value={
                  blockchain?.timestamp_coherent === true
                    ? 'Aligned'
                    : blockchain?.timestamp_coherent === false
                    ? 'Misaligned'
                    : '—'
                }
                status={blockchain?.timestamp_coherent}
              />
              {blockchain?.warnings?.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  {blockchain.warnings.map((warn, i) => (
                    <div
                      key={i}
                      className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 px-3 py-2 rounded-xl"
                    >
                      ⚠ {warn}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </LayerSection>

          {/* Layer 3: IPFS */}
          <LayerSection title="Layer 3: IPFS Storage" icon={Database} gradient="gradient-ipfs">
            <div className="space-y-0">
              <DetailRow
                label="Available"
                value={ipfs?.file_available ? 'Yes' : 'No'}
                status={ipfs?.file_available}
              />
              <DetailRow
                label="Content Integrity"
                value={
                  ipfs?.content_integrity === true
                    ? 'Verified'
                    : ipfs?.content_integrity === false
                    ? 'Mismatch'
                    : '—'
                }
                status={ipfs?.content_integrity}
              />
              <DetailRow
                label="IPFS CID"
                value={ipfs?.cid}
                mono={true}
                link={ipfs?.cid ? `${PINATA_BASE}${ipfs.cid}` : null}
              />
              {ipfs?.warnings?.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  {ipfs.warnings.map((warn, i) => (
                    <div
                      key={i}
                      className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 px-3 py-2 rounded-xl"
                    >
                      ⚠ {warn}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </LayerSection>

          {/* Layer 4: AI Fraud Detection */}
          <LayerSection title="Layer 4: AI Fraud Detection" icon={Cpu} gradient="gradient-ai" defaultOpen={true}>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-base-elevated rounded-xl border border-border-subtle text-center">
                  <span className="text-[10px] text-text-tertiary block font-medium">ML Prediction</span>
                  <span
                    className={`text-sm font-bold ${
                      ai?.ml_prediction === 'LIKELY_GENUINE' ? 'text-emerald-600' : 'text-amber-600'
                    }`}
                  >
                    {ai?.ml_prediction?.replace('_', ' ')}
                  </span>
                </div>
                <div className="p-3 bg-base-elevated rounded-xl border border-border-subtle text-center">
                  <span className="text-[10px] text-text-tertiary block font-medium">Fraud Probability</span>
                  <span
                    className={`text-sm font-bold ${
                      (ai?.fraud_probability_pct || 0) < 30 ? 'text-emerald-600' : 'text-red-600'
                    }`}
                  >
                    {ai?.fraud_probability_pct}%
                  </span>
                </div>
                <div className="p-3 bg-base-elevated rounded-xl border border-border-subtle text-center">
                  <span className="text-[10px] text-text-tertiary block font-medium">AI Verdict</span>
                  <span
                    className={`text-sm font-bold ${
                      ai?.final_ai_verdict === 'LIKELY_GENUINE' ? 'text-emerald-600' : 'text-amber-600'
                    }`}
                  >
                    {ai?.final_ai_verdict?.replace('_', ' ')}
                  </span>
                </div>
              </div>

              {ai?.hard_rule_failures?.length > 0 && (
                <div className="space-y-1.5">
                  <h4 className="text-xs font-semibold text-red-600">Hard Rule Failures</h4>
                  {ai.hard_rule_failures.map((fail, i) => (
                    <div
                      key={i}
                      className="text-xs text-red-700 bg-red-50 border border-red-200 px-3 py-2 rounded-xl"
                    >
                      ✗ {fail}
                    </div>
                  ))}
                </div>
              )}

              {/* Signature Analysis */}
              {ai?.signature_analysis ? (
                <div className="space-y-2 mt-4 pt-4 border-t border-border-subtle">
                  <div className="flex justify-between items-center">
                    <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                      Signature & Seal Analysis
                    </h4>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        ai.signature_analysis.detected
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      {ai.signature_analysis.detected ? 'DETECTED' : 'MISSING'} (Confidence:{' '}
                      {ai.signature_analysis.confidence.toFixed(2)})
                    </span>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    {ai.signature_analysis.findings.map((item, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-xl border flex gap-3 ${
                          item.result === 'passed'
                            ? 'bg-emerald-50/50 border-emerald-200'
                            : item.result === 'partial'
                            ? 'bg-blue-50/50 border-blue-200'
                            : 'bg-amber-50/50 border-amber-200'
                        }`}
                      >
                        <div
                          className={`mt-0.5 flex-shrink-0 ${
                            item.result === 'passed'
                              ? 'text-emerald-500'
                              : item.result === 'partial'
                              ? 'text-blue-500'
                              : 'text-amber-500'
                          }`}
                        >
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <div
                            className={`text-[11px] font-bold ${
                              item.result === 'passed'
                                ? 'text-emerald-700'
                                : item.result === 'partial'
                                ? 'text-blue-700'
                                : 'text-amber-700'
                            }`}
                          >
                            {item.check}
                          </div>
                          <div className="text-[11px] text-text-secondary mt-0.5">{item.detail}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                ai?.signature_detected !== undefined && (
                  <div
                    className={`p-3 rounded-xl border flex gap-3 ${
                      ai.signature_detected
                        ? 'bg-emerald-50/50 border-emerald-200'
                        : 'bg-amber-50/50 border-amber-200'
                    }`}
                  >
                    <div
                      className={`mt-0.5 flex-shrink-0 ${
                        ai.signature_detected ? 'text-emerald-500' : 'text-amber-500'
                      }`}
                    >
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <div
                        className={`text-[11px] font-bold ${
                          ai.signature_detected ? 'text-emerald-700' : 'text-amber-700'
                        }`}
                      >
                        {ai.signature_detected ? 'Signature Detected' : 'No Signature Detected'}
                      </div>
                      <div className="text-[11px] text-text-secondary mt-0.5">
                        {ai.signature_detected
                          ? "A signature or seal was found, increasing confidence in the certificate's authenticity."
                          : 'No signature or seal was detected, significantly increasing the fraud probability.'}
                      </div>
                    </div>
                  </div>
                )
              )}

              {/* Advanced Image Forensics */}
              {ai?.forensics?.findings && ai.forensics.findings.length > 0 && (
                <div className="space-y-2 mt-4 pt-4 border-t border-border-subtle">
                  <div className="flex justify-between items-center">
                    <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                      Advanced Image Forensics
                    </h4>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        ai.forensics.forensic_verdict === 'TAMPERING_LIKELY'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      {ai.forensics.forensic_verdict?.replace('_', ' ')} (Score:{' '}
                      {ai.forensics.forensic_score}/100)
                    </span>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    {ai.forensics.findings.map((finding, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-xl border flex gap-3 ${
                          finding.severity === 'high'
                            ? 'bg-red-50/50 border-red-200'
                            : 'bg-amber-50/50 border-amber-200'
                        }`}
                      >
                        <div
                          className={`mt-0.5 flex-shrink-0 ${
                            finding.severity === 'high' ? 'text-red-500' : 'text-amber-500'
                          }`}
                        >
                          <Cpu className="w-4 h-4" />
                        </div>
                        <div>
                          <div
                            className={`text-[11px] font-bold ${
                              finding.severity === 'high' ? 'text-red-700' : 'text-amber-700'
                            }`}
                          >
                            {finding.test}{' '}
                            <span className="opacity-75 font-normal ml-1">
                              (Score: {finding.score}/100)
                            </span>
                          </div>
                          <div className="text-[11px] text-text-secondary mt-0.5">{finding.message}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SHAP Values Explanation */}
              <ShapBars explanations={ai?.explanations || []} />
            </div>
          </LayerSection>
        </div>
      </div>
    </div>
  )
}