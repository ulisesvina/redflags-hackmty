import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Page() {
  return (
    <main className="landing-grid min-h-screen px-6 py-7 sm:px-10 sm:py-9 lg:px-14">
      <section className="flex min-h-[calc(100vh-4rem)] items-center py-8 sm:min-h-[calc(100vh-5.5rem)] sm:py-20">
        <div className="w-full">
          <h1 className="classic stretched-text max-w-6xl text-balance text-[clamp(8.5rem,11.5vw,15rem)] font-extralight leading-[0.95] tracking-[-0.050em] text-foreground">
            We tell <span className="text-danger">red flags</span> apart from{" "}
            <span className="text-mint-strong">green flags</span>
          </h1>
          <div className="mt-12 flex max-w-full flex-col items-stretch gap-4 border-t border-foreground/15 pt-5 sm:flex-row sm:items-end sm:gap-8">
            <Button
              render={<Link href="/auth" />}
              nativeButton={false}
              size="lg"
              className="h-auto flex-1 px-6 py-6 text-4xl sm:py-6"
            >
              Get Started
            </Button>
            <Button
              render={<Link href="/auth" />}
              nativeButton={false}
              variant="outline"
              size="lg"
              className="h-auto flex-1 px-6 py-6 text-4xl sm:py-6"
            >
              Know More
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}
