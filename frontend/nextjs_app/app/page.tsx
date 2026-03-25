/**
 * Legacy marketing page is served from `/legacy-home` (see route handler).
 * Auth CTAs live inside that document so the navbar has a single primary button.
 */
export default function HomePage() {
  return (
    <main className="h-screen w-screen overflow-hidden bg-[#050810]">
      <iframe
        src="/legacy-home"
        title="OCH-CCF Interactive Platform"
        className="h-full w-full border-0"
      />
    </main>
  )
}
