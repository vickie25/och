import { redirect } from 'next/navigation'

export default function OutsourcedStudentsRedirectPage() {
  redirect('/dashboard/employer/contracts/shortlisted-students')
}
