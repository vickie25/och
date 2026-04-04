import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'OCH Platform',
  description: 'OCH Role-Based Dashboard Platform',
  icons: {
    icon: [{ url: '/och-secondary-logo-blue.png', type: 'image/png' }],
    shortcut: '/och-secondary-logo-blue.png',
    apple: '/och-secondary-logo-blue.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}

