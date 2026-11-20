import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, QrCode } from 'lucide-react'
import { Html5QrcodeScanner } from 'html5-qrcode'

export default function QRScanner() {
  const navigate = useNavigate()
  const [scanError, setScanError] = useState('')

  useEffect(() => {
    const scanner = new Html5QrcodeScanner('reader', {
      qrbox: { width: 250, height: 250 },
      fps: 5,
    })

    scanner.render(
      (decodedText) => {
        scanner.clear()
        try {
          const url = new URL(decodedText)
          const certId = url.searchParams.get('cert_id')
          navigate(certId ? `/verify?cert_id=${certId}` : `/verify?cert_id=${decodedText}`)
        } catch {
          navigate(`/verify?cert_id=${decodedText}`)
        }
      },
      (err) => {
        setScanError(err?.message || 'Scanning...')
      }
    )

    return () => {
      scanner.clear().catch(console.error)
    }
  }, [navigate])

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="section-container max-w-lg">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 mb-8">
          <button onClick={() => navigate(-1)} className="btn-ghost">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6"
        >
          <div className="text-center mb-6">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl gradient-ai flex items-center justify-center shadow-md">
              <QrCode className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-text-primary">Scan Certificate QR</h2>
            <p className="text-text-secondary text-sm mt-1">
              Point your camera at the certificate's QR code to verify instantly.
            </p>
          </div>

          <div className="overflow-hidden rounded-card border border-border-subtle bg-base-elevated">
            <div
              id="reader"
              className="w-full text-text-primary [&>div]:!border-0 [&_a]:hidden [&_button]:!btn-outline [&_button]:!my-2"
            />
          </div>

          <p className="text-xs text-text-tertiary text-center mt-4 truncate px-4">{scanError}</p>
        </motion.div>
      </div>
    </div>
  )
}