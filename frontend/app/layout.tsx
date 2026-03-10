import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Infinite Agent Flow — Dashboard',
  description: 'Autonomous task engine monitor',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-surface-hard text-gruvbox-fg font-sans min-h-screen antialiased">
        {children}
      </body>
    </html>
  )
}
