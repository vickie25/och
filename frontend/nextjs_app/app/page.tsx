import { redirect } from 'next/navigation'

export default function HomePage() {
  // Serve the interactive marketing HTML directly.
  // Embedding it in an iframe is blocked by security headers (X-Frame-Options: DENY).
  redirect('/legacy-home')
}
