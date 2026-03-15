'use client'

import { useState, useEffect } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import {
  Terminal, Activity, FileCode2, Settings, LayoutDashboard,
  History, FileText, Menu, X,
} from 'lucide-react'
import { useWorkflows }  from '@/lib/hooks/useWorkflows'

export default function Sidebar() {
  const pathname = usePathname()
  const [isOpen, setIsOpen]     = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  const { workflows } = useWorkflows()

  // Detect mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024)
      if (window.innerWidth >= 1024) setIsOpen(false)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Close menu on route change
  useEffect(() => { setIsOpen(false) }, [pathname])

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    document.body.style.overflow = isOpen && isMobile ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [isOpen, isMobile])

  const navItems = [
    { href: '/',          icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { href: '/workflows', icon: <Activity        size={20} />, label: 'Workflows' },
    { href: '/files',     icon: <FileCode2       size={20} />, label: 'Files'     },
    { href: '/history',   icon: <History         size={20} />, label: 'History'   },
    { href: '/logs',      icon: <FileText        size={20} />, label: 'Logs'      },
    { href: '/settings',  icon: <Settings        size={20} />, label: 'Settings'  },
  ]

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-surface-hard/90
                   backdrop-blur-md border border-slate-700/50 shadow-lg
                   hover:bg-surface-light transition-colors touch-target"
        aria-label={isOpen ? 'Close menu' : 'Open menu'}
      >
        {isOpen
          ? <X    size={20} className="text-gruvbox-fg" />
          : <Menu size={20} className="text-gruvbox-fg" />
        }
      </button>

      {/* Overlay for mobile */}
      {isOpen && isMobile && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static top-0 left-0 h-screen
          w-64 lg:w-64
          bg-surface-hard border-r border-slate-700/50
          flex flex-col
          transition-transform duration-300 ease-in-out
          z-40
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo header */}
        <div className="h-16 flex items-center justify-center lg:justify-start lg:px-6 border-b border-slate-700/50 relative overflow-hidden safe-top">
          <div className="absolute inset-0 bg-accent/5 blur-xl" />
          <div className="w-8 h-8 rounded bg-gradient-to-br from-accent to-accent-dim
                          flex items-center justify-center
                          shadow-[0_0_15px_rgba(215,153,33,0.4)] relative z-10">
            <Terminal size={18} className="text-surface-hard" />
          </div>
          <span className="ml-3 font-mono font-bold text-gruvbox-fg hidden lg:block
                           tracking-wide relative z-10 drop-shadow-md">
            Card Dealer
          </span>
        </div>

        {/* Scrollable nav */}
        <nav className="flex-1 py-4 flex flex-col gap-1 px-3 overflow-y-auto custom-scrollbar">

          {/* Navigation links */}
          {navItems.map((item) => (
            <SidebarItem
              key={item.href}
              icon={item.icon}
              label={item.label}
              href={item.href}
              active={pathname === item.href}
            />
          ))}

          {/* ── Workflows ── */}
          <SectionLabel label="Workflows" />

          {workflows.length === 0 ? (
            <p className="px-3 py-2 text-xs text-slate-600 italic hidden lg:block">No workflows</p>
          ) : (
            workflows.map(wf => (
              <div
                key={`${wf.name}/${wf.version}`}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-500
                           hover:text-slate-400 hover:bg-surface-soft transition-colors"
              >
                <Activity className="w-3.5 h-3.5 shrink-0" />
                <span className="font-mono text-xs truncate hidden lg:block">
                  {wf.name}/{wf.version}
                </span>
              </div>
            ))
          )}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-slate-700/50 bg-surface-hard/80 backdrop-blur-sm safe-bottom">
          <div className="text-xs text-slate-600 text-center lg:text-left px-2">
            <span className="hidden lg:block">CardDealer v1.0</span>
            <span className="lg:hidden">v1.0</span>
          </div>
        </div>
      </aside>
    </>
  )
}

// ── Section divider label ──────────────────────────────────────────────────────
function SectionLabel({ label }: { label: string }) {
  return (
    <div className="mt-4 mb-0.5 px-2">
      <span className="text-[10px] uppercase tracking-widest text-slate-600 hidden lg:block">
        {label}
      </span>
      <div className="lg:hidden h-px bg-slate-700/40 my-2" />
    </div>
  )
}

// ── Page nav link ──────────────────────────────────────────────────────────────
function SidebarItem({
  icon, label, href, active = false,
}: {
  icon: React.ReactNode; label: string; href: string; active?: boolean
}) {
  return (
    <Link
      href={href}
      className={`flex items-center justify-center lg:justify-start px-3 py-3 rounded-lg
                  transition-all duration-300 group relative overflow-hidden touch-target
                  ${active
                    ? 'bg-surface-light text-accent shadow-[inset_3px_0_0_rgba(215,153,33,1)]'
                    : 'text-slate-400 hover:text-gruvbox-fg hover:bg-surface-soft'
                  }`}
    >
      {active && (
        <div className="absolute inset-0 bg-gradient-to-r from-accent/10 to-transparent pointer-events-none" />
      )}
      <div className={`relative z-10
                      ${active
                        ? 'animate-soft-pulse drop-shadow-[0_0_8px_rgba(215,153,33,0.6)]'
                        : 'group-hover:scale-110 transition-transform duration-200'}`}>
        {icon}
      </div>
      <span className="ml-3 font-medium text-sm hidden lg:block relative z-10">{label}</span>

      {/* Tooltip on icon-only mode */}
      <div className="absolute left-full ml-2 px-2 py-1 bg-surface-lighter text-xs rounded
                      opacity-0 pointer-events-none group-hover:opacity-100 lg:hidden z-50
                      whitespace-nowrap border border-slate-700 shadow-lg transition-opacity duration-200">
        {label}
      </div>
    </Link>
  )
}
