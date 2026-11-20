import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { useAuthStore } from '@/lib/store'
import Navbar from '@/components/layout/Navbar'
import Landing from '@/pages/Landing'
import Verify from '@/pages/Verify'
import Results from '@/pages/Results'
import Auth from '@/pages/Auth'
import Dashboard from '@/pages/Dashboard'
import Admin from '@/pages/Admin'
import IssueCertificate from '@/pages/IssueCertificate'
import ViewCertificates from '@/pages/ViewCertificates'
import QRScanner from '@/pages/QRScanner'
import ManageStudents from '@/pages/ManageStudents'

export default function App() {
  const fetchMe = useAuthStore((state) => state.fetchMe)

  useEffect(() => {
    fetchMe()
  }, [fetchMe])

  return (
    <div className="min-h-screen bg-white text-text-primary">
      <div className="particle-bg" />
      <Navbar />
      <main className="relative z-10">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/verify" element={<Verify />} />
          <Route path="/results" element={<Results />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/issue" element={<IssueCertificate />} />
          <Route path="/certificates" element={<ViewCertificates />} />
          <Route path="/students" element={<ManageStudents />} />
          <Route path="/scan" element={<QRScanner />} />
        </Routes>
      </main>
    </div>
  )
}
