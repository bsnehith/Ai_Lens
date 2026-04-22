import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import HeroSection from "../components/HeroSection";
import InteractiveShowcase from "../components/InteractiveShowcase";
import FeatureGrid from "../components/FeatureGrid";
import ReportStudio from "../components/ReportStudio";
import ChatPreview from "../components/ChatPreview";
import RecentReports from "../components/RecentReports";
import Footer from "../components/Footer";
import { checkBackendHealth } from "../api/client";

export default function HomePage() {
  const [backendOnline, setBackendOnline] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const progress = max > 0 ? (window.scrollY / max) * 100 : 0;
      document.documentElement.style.setProperty("--scroll-progress", `${progress}%`);
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    const check = async () => {
      try {
        await checkBackendHealth();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }
    };

    check();
    const timer = setInterval(check, 20000);

    return () => {
      window.removeEventListener("scroll", onScroll);
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="page">
      <Navbar backendOnline={backendOnline} />
      <main className="content-wrap">
        <HeroSection />
        <RecentReports />
        <InteractiveShowcase />
        <FeatureGrid />
        <ReportStudio />
        <ChatPreview />
      </main>
      <Footer />
    </div>
  );
}
