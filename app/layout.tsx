import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Open.Video Channel Search',
  description: 'Search and discover channels on Open.Video',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
