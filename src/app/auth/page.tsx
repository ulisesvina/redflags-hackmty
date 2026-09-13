import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function AuthPage() {
  return (
    <main className="flex items-center justify-center px-6 py-16 sm:px-10">
      <section className="w-full max-w-lg border border-foreground/15 bg-background p-8 sm:p-12">
        <p className="mb-4 text-xs uppercase tracking-[0.2em] text-muted-foreground">RedFlags investigator access</p>
        <h1 className="classic text-6xl leading-none sm:text-7xl">Open a case.</h1>
        <p className="mt-4 max-w-sm text-sm leading-6 text-muted-foreground">
          Name this local demo session, then bring the company&apos;s evidence estate.
        </p>

        <form action="/dashboard" className="mt-10 space-y-5">
          <label className="block text-sm">
            <span className="mb-2 block">Investigator name</span>
            <input
              required
              name="userName"
              type="text"
              placeholder="Your name"
              className="h-12 w-full border border-foreground/20 bg-transparent px-4 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-foreground"
            />
          </label>
          <Button type="submit" className="h-12 w-full text-base">Enter forensic workspace</Button>
        </form>

        <Link href="/" className="mt-8 inline-block text-xs text-muted-foreground underline underline-offset-4">
          Back to home
        </Link>
      </section>
    </main>
  );
}
