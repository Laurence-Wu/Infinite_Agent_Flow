'use client'

import { createContext, useContext, useEffect, useState, useCallback } from 'react'

export interface AppSettings {
  autoExpandCards: boolean      // DealerPanel cards start expanded
  compactLogs: boolean          // LogTerminal uses compact 140px height
  notificationsEnabled: boolean // Browser push notifications on task complete
}

const DEFAULTS: AppSettings = {
  autoExpandCards: false,
  compactLogs: true,
  notificationsEnabled: false,
}

const STORAGE_KEY = 'iaf_settings'

function load(): AppSettings {
  if (typeof window === 'undefined') return DEFAULTS
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : DEFAULTS
  } catch {
    return DEFAULTS
  }
}

function save(s: AppSettings) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)) } catch { /* ignore */ }
}

interface SettingsCtx {
  settings: AppSettings
  set: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => void
}

const Ctx = createContext<SettingsCtx>({
  settings: DEFAULTS,
  set: () => {},
})

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(DEFAULTS)

  // Hydrate from localStorage after mount (avoids SSR mismatch)
  useEffect(() => { setSettings(load()) }, [])

  const set = useCallback(<K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings(prev => {
      const next = { ...prev, [key]: value }
      save(next)
      return next
    })
  }, [])

  return <Ctx.Provider value={{ settings, set }}>{children}</Ctx.Provider>
}

export function useSettings() {
  return useContext(Ctx)
}
