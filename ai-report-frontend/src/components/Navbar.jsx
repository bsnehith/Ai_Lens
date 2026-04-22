import { useEffect, useState } from "react";
import { Menu, X, Sparkles } from "lucide-react";
import clsx from "clsx";
import { navItems } from "../data/mockData";

function scrollToSection(id) {
  const target = document.getElementById(id);
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

export default function Navbar({ backendOnline }) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleItemClick = (id) => {
    setOpen(false);
    scrollToSection(id);
  };

  return (
    <header className={clsx("navbar", scrolled && "navbar-scrolled")}>
      <button className="brand" onClick={() => scrollToSection("hero")} type="button">
        <Sparkles size={18} />
        <span>AI Lens</span>
      </button>

      <nav className={clsx("nav-links", open && "nav-open")}>
        {navItems.map((item) => (
          <button key={item.id} type="button" onClick={() => handleItemClick(item.id)}>
            {item.label}
          </button>
        ))}
        <button className="cta cta-mobile" type="button" onClick={() => handleItemClick("report-studio")}>
          Get Started
        </button>
      </nav>

      <div className="nav-right">
        <div className={clsx("backend-pill", backendOnline ? "backend-online" : "backend-offline")}>
          <span className="status-dot" />
          <span>{backendOnline ? "Backend Online" : "Backend Offline"}</span>
        </div>
        <button className="cta cta-desktop" type="button" onClick={() => handleItemClick("report-studio")}>
          Get Started
        </button>
      </div>

      <button className="menu-btn" type="button" onClick={() => setOpen((prev) => !prev)}>
        {open ? <X size={19} /> : <Menu size={19} />}
      </button>
    </header>
  );
}
