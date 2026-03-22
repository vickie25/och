import { redirect } from 'next/navigation';

/** Single source of truth: full subscription UI lives under /dashboard/student/subscription */
export default function SettingsSubscriptionRedirect() {
  redirect('/dashboard/student/subscription');
}
