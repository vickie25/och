/**
 * Full commercial reference for print / Save as PDF (browser print dialog).
 * Section numbering matches internal commercial spec (2.3.x).
 */
export function CommercialTermsPrintDocument() {
  return (
    <article className="prose prose-invert max-w-none text-sm text-och-steel print:text-black print:bg-white">
      <header className="mb-8 border-b border-och-steel/30 pb-4 print:border-gray-300">
        <h1 className="text-2xl font-bold text-white print:text-black">OCH — Employer commercial terms</h1>
        <p className="text-xs mt-2">
          Reference document. Final pricing and legal terms are confirmed on your executed contract and invoices.
        </p>
      </header>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3 Employer partnership model</h2>
        <p className="mt-2">
          Employers pay a monthly retainer fee to access the talent pipeline and recruit from OCH graduates. Employers
          can also sponsor private cohorts for their employees, creating a multi-dimensional partnership.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3.1 Monthly retainer fee tiers</h2>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-och-steel/30 print:border-gray-300">
                <th className="py-2 pr-2">Tier</th>
                <th className="py-2 pr-2">Monthly retainer</th>
                <th className="py-2 pr-2">Candidate access / quarter</th>
                <th className="py-2">Key features</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-och-steel/15 print:border-gray-200">
                <td className="py-2 text-white print:text-black">Starter</td>
                <td className="py-2">$500/month</td>
                <td className="py-2">Up to 5</td>
                <td className="py-2">Basic talent pipeline access, standard matching</td>
              </tr>
              <tr className="border-b border-och-steel/15 print:border-gray-200">
                <td className="py-2 text-white print:text-black">Growth</td>
                <td className="py-2">$1,500/month</td>
                <td className="py-2">Up to 15</td>
                <td className="py-2">Priority matching, dedicated account manager</td>
              </tr>
              <tr className="border-b border-och-steel/15 print:border-gray-200">
                <td className="py-2 text-white print:text-black">Enterprise</td>
                <td className="py-2">$3,500/month</td>
                <td className="py-2">Unlimited pipeline</td>
                <td className="py-2">VIP matching, custom reports, exclusive pipeline</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3.2 Per-candidate successful placement fees</h2>
        <ul className="list-disc pl-5 mt-3 space-y-1">
          <li>
            <strong className="text-white print:text-black">Placement fee trigger:</strong> Fee when candidate completes
            interview process, accepts offer, and completes first 90 days of employment.
          </li>
          <li>Starter tier fee: $2,000 per successful placement.</li>
          <li>Growth tier fee: $1,500 per successful placement.</li>
          <li>Enterprise tier fee: $1,000 per successful placement.</li>
          <li>Fee billing: Placement fees invoiced monthly; separate line item from retainer.</li>
          <li>
            Fee cap: Monthly placement fees capped at 2× monthly retainer (e.g. Starter max $1,000 in placement fees
            if 5 successful placements in a month — illustrative; see your contract).
          </li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3.3 Contract tiers comparison</h2>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-och-steel/30 print:border-gray-300">
                <th className="py-2 pr-2">Feature</th>
                <th className="py-2 pr-2">Starter</th>
                <th className="py-2 pr-2">Growth</th>
                <th className="py-2 pr-2">Enterprise</th>
                <th className="py-2">Custom</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-och-steel/15">
                <td className="py-2">Monthly retainer</td>
                <td className="py-2">$500</td>
                <td className="py-2">$1,500</td>
                <td className="py-2">$3,500</td>
                <td className="py-2">Negotiated</td>
              </tr>
              <tr className="border-b border-och-steel/15">
                <td className="py-2">Candidates / quarter</td>
                <td className="py-2">5</td>
                <td className="py-2">15</td>
                <td className="py-2">Unlimited</td>
                <td className="py-2">Unlimited</td>
              </tr>
              <tr className="border-b border-och-steel/15">
                <td className="py-2">Per-placement fee</td>
                <td className="py-2">$2,000</td>
                <td className="py-2">$1,500</td>
                <td className="py-2">$1,000</td>
                <td className="py-2">Negotiated</td>
              </tr>
              <tr className="border-b border-och-steel/15">
                <td className="py-2">Dedicated account manager</td>
                <td className="py-2">No</td>
                <td className="py-2">Yes</td>
                <td className="py-2">Yes</td>
                <td className="py-2">Yes</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3.4 Talent pipeline SLA and quality guarantees</h2>
        <ul className="list-disc pl-5 mt-3 space-y-1">
          <li>Time-to-shortlist SLA: First shortlist (3–5 qualified candidates) within 5 business days of requirements submission.</li>
          <li>Candidate quality score: Minimum 75%+ on skills assessment; OCH certifies results.</li>
          <li>Track completion: Minimum tier level appropriate to role (e.g. Tier 4+ for senior roles).</li>
          <li>Mission score baseline: Minimum mission completion score (70%+).</li>
          <li>Portfolio quality: Projects/missions reviewed and verified before presentation.</li>
          <li>
            Replacement guarantee: If placed candidate leaves within 60 days of start, replacement at no extra fee
            (new replacement period begins with replacement).
          </li>
          <li>Placement success rate target: &gt;70% presented candidates accepted; &lt;60% triggers alignment review.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3.5 Contract lifecycle stages</h2>
        <ul className="list-disc pl-5 mt-3 space-y-1">
          <li><strong className="text-white print:text-black">Proposal:</strong> Pricing tiers, SLAs, profiles for employer review.</li>
          <li><strong className="text-white print:text-black">Negotiation:</strong> Modifications to terms, SLAs, exclusivity.</li>
          <li><strong className="text-white print:text-black">Signed:</strong> Execution; official start date.</li>
          <li><strong className="text-white print:text-black">Active:</strong> Platform access; requirements and candidates.</li>
          <li><strong className="text-white print:text-black">Renewal / termination:</strong> End of term renewal or archive.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3.6 Marketplace integration and priority access</h2>
        <ul className="list-disc pl-5 mt-3 space-y-1">
          <li>Talent matching engine: Algorithm-driven match of requirements to candidates.</li>
          <li>Priority matching: Contract employers first in queue vs non-contract inquiries.</li>
          <li>Presentation order: Top-matched candidates first; others may go to waitlist.</li>
          <li>Exclusivity window: Premium tiers may negotiate 48–72h exclusive presentation windows.</li>
          <li>Analytics: Dashboard for recommendations, availability, historical success.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3.7 Performance-based pricing adjustments</h2>
        <ul className="list-disc pl-5 mt-3 space-y-1">
          <li>Annual performance review at renewal on placement success metrics.</li>
          <li>Success rate = (successful placements ÷ candidates presented) × 100%.</li>
          <li>High performance: If &gt;90% success, 10% discount on renewal retainer.</li>
          <li>Underperformance: If &lt;60%, analysis to improve matching and selection.</li>
          <li>Adjustments apply to renewal; current-year pricing unchanged unless agreed.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3.8 Exclusivity clauses and premium pricing</h2>
        <ul className="list-disc pl-5 mt-3 space-y-1">
          <li>Exclusivity option: Premium access to a pool of matched candidates.</li>
          <li>Exclusive pipeline price: +50% to retainer (e.g. Starter $750/mo illustrative).</li>
          <li>Exclusivity duration: Typically 3–6 months; then candidates re-enter general pipeline.</li>
          <li>Replacement within exclusivity pool if departure within 60 days.</li>
          <li>Multiple employers: Exclusivity can apply to non-competing employers simultaneously.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-och-gold print:text-gray-900">2.3.9 Talent replacement guarantee</h2>
        <ul className="list-disc pl-5 mt-3 space-y-1">
          <li>60-day standard: Departure within 60 days → replacement at no additional cost.</li>
          <li>Replacement offering: Within 10 business days, 3–5 replacement candidates.</li>
          <li>Enterprise: Extended 90-day guarantee option.</li>
          <li>Exclusions: Not for employer-initiated termination for performance.</li>
          <li>Multiple replacements: Guarantee applies again for second replacement within terms.</li>
          <li>After 3 replacements in 12 months, partnership review.</li>
        </ul>
      </section>
    </article>
  )
}
