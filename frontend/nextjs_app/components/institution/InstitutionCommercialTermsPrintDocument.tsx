/**
 * Reference for print / Save as PDF — aligns with commercial spec §2.2 (institutional licensing).
 */
export function InstitutionCommercialTermsPrintDocument() {
  return (
    <article className="prose prose-invert max-w-none text-sm text-och-steel print:text-black print:bg-white">
      <header className="mb-8 border-b border-och-steel/30 pb-4 print:border-gray-300">
        <h1 className="text-2xl font-bold text-white print:text-black">OCH — Institutional licensing (reference)</h1>
        <p className="text-xs mt-2">
          Reference only. Final terms are on your executed contract and invoices generated in the platform.
        </p>
      </header>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.2.1 Contract requirements</h2>
        <ul className="list-disc pl-5 mt-3 space-y-1">
          <li>Minimum term: 12 months for institutional agreements.</li>
          <li>Early termination: 60-day notice; remaining balance may be prorated per agreement.</li>
          <li>Auto-renewal: additional 12-month terms unless 60-day non-renewal notice.</li>
          <li>Renewal pricing: annual review; per-student rates may be updated on renewal quote.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.2.2 Per-student licensing tiers (USD)</h2>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-och-steel/30 print:border-gray-300">
                <th className="py-2 pr-2">Students</th>
                <th className="py-2 pr-2">$/student/month</th>
                <th className="py-2">$/student/year (indicative)</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-och-steel/15 print:border-gray-200">
                <td className="py-2">1–50</td>
                <td className="py-2">$15</td>
                <td className="py-2">$180</td>
              </tr>
              <tr className="border-b border-och-steel/15 print:border-gray-200">
                <td className="py-2">51–200</td>
                <td className="py-2">$12</td>
                <td className="py-2">$144</td>
              </tr>
              <tr className="border-b border-och-steel/15 print:border-gray-200">
                <td className="py-2">201–500</td>
                <td className="py-2">$9</td>
                <td className="py-2">$108</td>
              </tr>
              <tr className="border-b border-och-steel/15 print:border-gray-200">
                <td className="py-2">500+</td>
                <td className="py-2">$7</td>
                <td className="py-2">$84</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.2.3 Billing cycles</h2>
        <p className="mt-2">
          Monthly, quarterly, or annual invoicing may be selected at contract setup. Invoices are typically due net 30.
          Seat changes mid-cycle may be prorated on the next invoice. Annual billing may include a small discount (e.g.
          ~2%).
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.2.4–2.2.5 Cohorts and seats</h2>
        <p className="mt-2">
          Your contract defines purchased seat capacity. Active seats are students with current access; allocated seats
          are purchased capacity. Utilization and reassignment follow your agreement and operational deadlines.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.2.10 Track mandates</h2>
        <p className="mt-2">
          You may document mandated tracks and module selections in your contract blueprint so your director and
          learners see the intended curriculum. All enrolled students inherit the licensing tier tied to the contract.
        </p>
      </section>
    </article>
  )
}
