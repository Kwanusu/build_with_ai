import { useEffect } from "react";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { HowItWorks, WhatItFinds, WhyTrustIt, Closing } from "./components/Sections";
import { AuthErrorPage } from "./components/AuthErrorPage";
import { ScanPage } from "./components/ScanPage";
import { Footer } from "./components/Footer";
import { useRoute } from "./route";

export function App() {
  const route = useRoute();
  const onLanding = route.name === "landing";

  // A hash change doesn't scroll by itself when the page swaps: go to the top, or to the section that was linked.
  useEffect(() => {
    if (onLanding) {
      document.getElementById(window.location.hash.slice(1))?.scrollIntoView();
    } else {
      window.scrollTo({ top: 0 });
    }
  }, [onLanding]);

  return (
    <>
      <Header showAction={onLanding} />
      <main id={onLanding ? "top" : "app"}>
        {route.name === "scan" ? (
          <ScanPage owner={route.owner} repo={route.repo} />
        ) : route.name === "auth-error" ? (
          <AuthErrorPage code={route.code} />
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
