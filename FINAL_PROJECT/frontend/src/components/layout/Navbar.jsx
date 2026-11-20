import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldCheck, User, LogOut, Menu, X } from 'lucide-react'
import { useAuthStore } from '@/lib/store'

export default function Navbar() {
  const { pathname } = useLocation()
  const { user, isAuthenticated, logout } = useAuthStore()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navLinks = (() => {
    const base = [
      { path: '/', label: 'Home' },
      { path: '/verify', label: 'Verify' },
      { path: '/scan', label: 'QR Scan' },
    ]
    if (!isAuthenticated) return base

    if (user?.role === 'student') {
      return [
        ...base,
        { path: '/certificates', label: 'My Certificates' },
        { path: '/dashboard', label: 'Portal' },
      ]
    }

    if (user?.role === 'institution') {
      return [
        ...base,
        { path: '/dashboard', label: 'Dashboard' },
        { path: '/certificates', label: 'Certificates' },
        { path: '/students', label: 'Student Logins' },
        { path: '/issue', label: 'Issue' },
      ]
    }

    if (user?.role === 'admin') {
      return [
        ...base,
        { path: '/dashboard', label: 'Dashboard' },
        { path: '/admin', label: 'Admin' },
        { path: '/certificates', label: 'Certificates' },
        { path: '/students', label: 'Student Logins' },
      ]
    }

    return [
      ...base,
      { path: '/dashboard', label: 'Dashboard' },
      { path: '/certificates', label: 'Certificates' },
    ]
  })()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-border-subtle shadow-nav">
      <div className="section-container flex items-center justify-between h-16">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <motion.div
            whileHover={{ rotate: 15, scale: 1.05 }}
            className="w-9 h-9 rounded-xl gradient-blockchain flex items-center justify-center shadow-primary"
          >
            <ShieldCheck className="w-5 h-5 text-white" />
          </motion.div>
          <span className="text-lg font-bold tracking-tight text-text-primary">
            Cert<span className="text-primary">Verify</span>
          </span>
        </Link>

        {/* Desktop Nav Items */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => {
            const isActive = pathname === link.path
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`relative px-3.5 py-2 text-sm font-medium rounded-btn transition-all ${
                  isActive
                    ? 'text-primary'
                    : 'text-text-secondary hover:text-text-primary hover:bg-base-elevated'
                }`}
              >
                {link.label}
                {isActive && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="absolute bottom-0 left-3 right-3 h-0.5 bg-primary rounded-full"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
              </Link>
            )
          })}
        </div>

        {/* Right Action / Profile */}
        <div className="hidden md:flex items-center gap-3">
          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-pill bg-base-elevated border border-border-subtle">
                <div className="w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center">
                  <User className="w-3 h-3 text-primary" />
                </div>
                <span className="text-sm font-medium text-text-primary">
                  {user?.full_name || user?.username}
                </span>
                <span className="badge bg-primary-50 text-primary-600 text-[10px] border border-primary-200">
                  {user?.role}
                </span>
              </div>
              <button
                onClick={logout}
                className="btn-ghost text-sm text-text-tertiary hover:text-red-500"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link to="/auth" className="btn-primary text-sm">
              Sign In
            </Link>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden btn-ghost p-2"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle Menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="md:hidden glass-card mx-4 mt-2 p-4 space-y-1"
          >
            {navLinks.map((link) => {
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-4 py-2.5 rounded-btn text-sm font-medium transition-colors ${
                    pathname === link.path
                      ? 'bg-primary-50 text-primary'
                      : 'text-text-secondary hover:bg-base-elevated'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
            <div className="pt-2 border-t border-border-subtle mt-2">
              {isAuthenticated ? (
                <div className="flex items-center justify-between px-4 py-2">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-primary" />
                    <span className="text-sm font-medium">
                      {user?.full_name || user?.username}
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      logout()
                      setMobileMenuOpen(false)
                    }}
                    className="text-sm font-medium text-red-500"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <Link
                  to="/auth"
                  onClick={() => setMobileMenuOpen(false)}
                  className="btn-primary w-full text-sm mt-1"
                >
                  Sign In
                </Link>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
