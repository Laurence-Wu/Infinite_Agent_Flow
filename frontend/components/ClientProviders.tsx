'use client'

import { SettingsProvider } from '@/lib/context/SettingsContext'

export default function ClientProviders({ children }: { children: React.ReactNode }) {
  return <SettingsProvider>{children}</SettingsProvider>
}
