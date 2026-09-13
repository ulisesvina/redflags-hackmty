import Link from "next/link";

export default function AboutPage() {
  return (
    <main className="landing-grid min-h-screen px-6 py-12 sm:px-10 sm:py-16 lg:px-14">
      <div className="mx-auto max-w-6xl">
        <div className="flex items-center justify-between border-b border-foreground/15 pb-5 text-xs uppercase tracking-[0.18em] text-muted-foreground">
          <span>About RedFlags</span>
          <Link href="/" className="underline underline-offset-4 transition-colors hover:text-foreground">
            Back to home
          </Link>
        </div>

        <section className="grid gap-10 border-b border-foreground/15 py-14 lg:grid-cols-[1.35fr_0.65fr] lg:gap-20 lg:py-24">
          <div>
            <p className="mb-6 text-sm uppercase tracking-[0.18em] text-danger">Forensic accounting, with a trail</p>
            <h1 className="classic max-w-4xl text-6xl leading-[0.92] sm:text-8xl lg:text-9xl">
              Flagging is the easy half. Proving is the product.
            </h1>
          </div>
          <p className="self-end text-lg leading-8 text-muted-foreground sm:text-xl">
            RedFlags is a forensic auditor for a company&apos;s books. Give it the invoices, the ledger, and the bank statement, and it follows the money.
          </p>
        </section>

        <section className="grid gap-10 border-b border-foreground/15 py-12 sm:grid-cols-2 lg:grid-cols-3 lg:gap-14 lg:py-16">
          <div>
            <p className="mb-4 text-xs uppercase tracking-[0.18em] text-danger">01 / Find the pattern</p>
            <p className="leading-7 text-muted-foreground">
              From suppliers that exist only on paper to kickbacks routed through shell accounts, it connects records instead of treating them as isolated rows.
            </p>
          </div>
          <div>
            <p className="mb-4 text-xs uppercase tracking-[0.18em] text-mint-strong">02 / Build the case</p>
            <p className="leading-7 text-muted-foreground">
              Every finding names the rule broken, the peso amount, and the records that prove it. Code checks the evidence before anything is printed.
            </p>
          </div>
          <div>
            <p className="mb-4 text-xs uppercase tracking-[0.18em] text-trust">03 / Clear the honest leads</p>
            <p className="leading-7 text-muted-foreground">
              Every lead investigated and cleared is listed with the document that cleared it. Refusing to accuse an honest supplier is half the job.
            </p>
          </div>
        </section>

        <section className="grid gap-10 py-12 sm:grid-cols-2 lg:gap-20 lg:py-16">
          <div>
            <p className="mb-5 text-xs uppercase tracking-[0.18em] text-muted-foreground">Made for Mexico</p>
            <p className="text-2xl leading-9 sm:text-3xl">
              A supplier landing on SAT&apos;s 69-B list gives a company thirty days to prove the operations were real or pay the tax back with fines. A flag does not survive that. A trail does.
            </p>
          </div>
          <div className="flex flex-col justify-between gap-8 border-t border-foreground/15 pt-5 sm:border-t-0 sm:border-l sm:pl-10 sm:pt-0">
            <div>
              <p className="mb-4 text-xs uppercase tracking-[0.18em] text-muted-foreground">Private by design</p>
              <p className="leading-7 text-muted-foreground">
                It runs on an open-weight model on hardware you control, so RFCs and bank accounts never leave the building. The same seed produces the same case file, and a finished run replays with the network off.
              </p>
            </div>
            <p className="text-sm leading-6 text-muted-foreground">
              Built in 36 hours at HackMTY 2026 for the Infosys Forensic Auditor challenge.
            </p>
          </div>
        </section>

        <div className="flex flex-col gap-4 border-t border-foreground/15 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted-foreground">Bring the books. We&apos;ll follow the money.</p>
          <Link href="/auth" className="text-sm font-semibold underline underline-offset-4 transition-colors hover:text-danger">
            Open a case
          </Link>
        </div>
      </div>
    </main>
  );
}