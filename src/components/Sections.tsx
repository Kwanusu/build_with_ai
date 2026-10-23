import type { ReactNode } from "react";
import { CLOSING, CTA_HREF, CTA_LABEL, FINDS, HOW, TRUST, type Card } from "../content";
import { Badge, Button } from "./ui";

interface SectionProps {
  id?: string;
  title: string;
  intro?: string;
  children: ReactNode;
}

function Section({ id, title, intro, children }: SectionProps) {
  return (
    <section id={id} className="page py-6 border-t rule flex flex-col gap-4">
      <div className="flex flex-col gap-1 reading">
        <h2 className="type-h2">{title}</h2>
        {intro && <p className="type-body-lg c-muted">{intro}</p>}
      </div>
      {children}
    </section>
  );
}

function InfoCard({ card }: { card: Card }) {
  return (
    <div className="card flex flex-col gap-1">
      {card.badge ? (
        <div className="flex flex-wrap items-center gap-1">
          <h3 className="type-h4">{card.title}</h3>
          <Badge tone="neutral">{card.badge}</Badge>
        </div>
      ) : (
        <h3 className="type-h4">{card.title}</h3>
      )}
      <p className="type-small c-muted">{card.body}</p>
    </div>
  );
}

export function HowItWorks() {
  return (
    <Section id={HOW.id} title={HOW.title} intro={HOW.intro}>
      <ol className="grid gap-3 md:grid-cols-3 list-none p-0 m-0">
        {HOW.steps.map((step) => (
          <li key={step.number} className="card flex flex-col gap-1">
            <p className="type-code c-muted">{step.number}</p>
            <h3 className="type-h4">{step.title}</h3>
            <p className="type-small c-muted">{step.body}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}

export function WhatItFinds() {
  return (
    <Section id={FINDS.id} title={FINDS.title} intro={FINDS.intro}>
      <div className="grid gap-3 sm:grid-cols-2">
        {FINDS.cards.map((card) => (
          <InfoCard key={card.title} card={card} />
        ))}
      </div>
    </Section>
  );
}

export function WhyTrustIt() {
  return (
    <Section id={TRUST.id} title={TRUST.title} intro={TRUST.intro}>
      <div className="grid gap-3 md:grid-cols-3">
        {TRUST.cards.map((card) => (
          <InfoCard key={card.title} card={card} />
        ))}
      </div>
      <div className="card flex flex-col gap-1 reading">
        <p className="type-code c-muted">{TRUST.push.caption}</p>
        <p className="type-code">{TRUST.push.line}</p>
        <p className="type-small c-muted">{TRUST.push.result}</p>
      </div>
    </Section>
  );
}

export function Closing() {
  return (
    <section className="page py-6 border-t rule flex flex-col items-start gap-3">
      <h2 className="type-h2 reading">{CLOSING.title}</h2>
      <p className="type-body-lg c-muted reading">{CLOSING.body}</p>
      <Button href={CTA_HREF} size="lg">
        {CTA_LABEL}
      </Button>
    </section>
  );
}
