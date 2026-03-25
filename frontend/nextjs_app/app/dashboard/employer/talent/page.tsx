import { redirect } from 'next/navigation'

/** Talent browsing lives under Marketplace; keep old URL working. */
export default function EmployerTalentRedirectPage() {
  redirect('/dashboard/employer/marketplace/talent')
}
