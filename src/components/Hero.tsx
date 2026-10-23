import { CTA_HREF, CTA_LABEL, HERO } from "../content";
import { Button } from "./ui";
import { ExampleResults } from "./ExampleResults";

export function Hero() {
  return (
    <section className="page py-6 grid gap-5 lg:grid-cols-2 lg:items-center">
      <div className="flex flex-col gap-3">
        <h1 className="type-display">{HERO.title}</h1>
        <p className="type-body-lg c-muted reading">{HERO.body}</p>
        <div className="flex flex-wrap items-center gap-2">
          <Button href={CTA_HREF} variant="primary" size="lg">
            {CTA_LABEL}
          </Button>
          <Button href="#how" size="lg">
            {HERO.secondaryLabel}
          </Button>
        </div>
        <p className="type-small c-muted">{HERO.reassurance}</p>
      </div>
      <ExampleResults />
    </section>
  );
}
