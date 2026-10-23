import { useEffect } from "react";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { HowItWorks, WhatItFinds, WhyTrustIt, Closing } from "./components/Sections";
import { ScanPage } from "./components/ScanPage";
import { Footer } from "./components/Footer";
import { useRoute } from "./route";

export function App() {
  const route = useRoute();
  const onScanPage = route.name === "scan";

  // A hash change doesn't scroll by itself when the page swaps: go to the top, or to the section that was linked.
  useEffect(() => {
    if (onScanPage) {
      window.scrollTo({ top: 0 });
    } else {
      document.getElementById(window.location.hash.slice(1))?.scrollIntoView();
    }
  }, [onScanPage]);

  return (
    <>
      <Header showAction={!onScanPage} />
      <main id={onScanPage ? "scan" : "top"}>
        {route.name === "scan" ? (
          <ScanPage owner={route.owner} repo={route.repo} />
        ) : (
          <>
            <Hero />
            <HowItWorks />
            <WhatItFinds />
            <WhyTrustIt />
            <Closing />
          </>
        )}
      </main>
      <Footer />
    </>
  );
}
