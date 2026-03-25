import { redirect } from 'next/navigation'

/** Employers are managed under Enrollment → Organizations. */
export default function LegacyEmployersRedirect() {
  redirect('/dashboard/director/enrollment/organizations')
}
