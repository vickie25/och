import { redirect } from 'next/navigation'

/** Moved to director enrollment — organizations (institutions & employers). */
export default function LegacySponsorsRedirect() {
  redirect('/dashboard/director/enrollment/organizations')
}
