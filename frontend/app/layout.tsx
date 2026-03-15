import type { Metadata } from 'next'
import './globals.css'
import Sidebar from '@/components/Sidebar'
import ClientProviders from '@/components/ClientProviders'

export const metadata: Metadata = {
  title: 'Infinite Agent Flow — Dashboard',
  description: 'Autonomous task engine monitor',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-surface-hard text-gruvbox-fg font-sans min-h-screen antialiased">
        <ClientProviders>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <div className="flex-1 overflow-y-auto">
              {children}
            </div>
          </div>
        </ClientProviders>
      </body>
    </html>
  )
}
