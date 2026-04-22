import { motion } from "framer-motion";
import { featureCards, workflowSteps } from "../data/mockData";

export default function FeatureGrid() {
  return (
    <>
      <section id="features" className="section">
        <div className="section-title">
          <h2>Built for real production workflows</h2>
          <p>Modern UI with clear hierarchy, smart interactions, and premium card animations.</p>
        </div>
        <div className="feature-grid">
          {featureCards.map((card, index) => (
            <motion.article
              key={card.title}
              className={`feature-card gradient-${card.gradient}`}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ duration: 0.4, delay: index * 0.08 }}
            >
              <h3>{card.title}</h3>
              <p>{card.description}</p>
            </motion.article>
          ))}
        </div>
      </section>

      <section id="workflow" className="section workflow">
        <div className="section-title">
          <h2>Agent workflow</h2>
          <p>How your report generation agent executes tasks end-to-end.</p>
        </div>
        <div className="timeline">
          {workflowSteps.map((step, idx) => (
            <motion.div
              key={step}
              className="timeline-item"
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.45 }}
              transition={{ delay: idx * 0.12, duration: 0.35 }}
            >
              <span>{idx + 1}</span>
              <p>{step}</p>
            </motion.div>
          ))}
        </div>
      </section>
    </>
  );
}
