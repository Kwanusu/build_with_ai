import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { HowItWorks, WhatItFinds, WhyTrustIt, Closing } from "./components/Sections";
import { Footer } from "./components/Footer";

export function App() {
  return (
    <>
      <Header />
      <main id="top">
        <Hero />
        <HowItWorks />
        <WhatItFinds />
        <WhyTrustIt />
        <Closing />
      </main>
      <Footer />
    </>
  );
}
