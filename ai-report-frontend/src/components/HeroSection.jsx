import { motion } from "framer-motion";
import { ArrowRight, PlayCircle } from "lucide-react";
import Hero3D from "./Hero3D";
import { kpis } from "../data/mockData";

function statVariants(index) {
  return {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: { delay: 0.2 + index * 0.08, duration: 0.4 },
    },
  };
}

export default function HeroSection() {
  return (
    <section id="hero" className="hero-section">
      <div className="hero-copy">
        <motion.span
          className="eyebrow"
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          Agentic AI Platform
        </motion.span>
        <motion.h1
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.55 }}
        >
          Build real-time AI industry insights with MCP-powered agents.
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.55 }}
        >
          This frontend is designed like modern commerce websites with rich visuals, fast interaction,
          and responsive behavior across desktop, tablet, and mobile.
        </motion.p>

        <motion.div
          className="hero-actions"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.45 }}
        >
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => document.getElementById("report-studio")?.scrollIntoView({ behavior: "smooth" })}
          >
            Launch Report Studio <ArrowRight size={16} />
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => document.getElementById("workflow")?.scrollIntoView({ behavior: "smooth" })}
          >
            <PlayCircle size={16} /> Watch Workflow
          </button>
        </motion.div>

        <div className="kpi-grid">
          {kpis.map((kpi, index) => (
            <motion.article
              key={kpi.label}
              className="kpi-card"
              variants={statVariants(index)}
              initial="hidden"
              animate="show"
            >
              <strong>{kpi.value}</strong>
              <span>{kpi.label}</span>
            </motion.article>
          ))}
        </div>
      </div>

      <Hero3D />
    </section>
  );
}
