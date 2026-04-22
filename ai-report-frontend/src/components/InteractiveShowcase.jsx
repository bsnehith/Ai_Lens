import { useState } from "react";
import { motion } from "framer-motion";
import { Bolt, CircleDollarSign, Radar } from "lucide-react";
import { categoryChips, showcaseCards } from "../data/mockData";

const icons = [Radar, CircleDollarSign, Bolt];

export default function InteractiveShowcase() {
  const [activeChip, setActiveChip] = useState(categoryChips[0]);

  const onMoveCard = (event) => {
    const card = event.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const rotateX = ((y / rect.height) - 0.5) * -8;
    const rotateY = ((x / rect.width) - 0.5) * 10;
    card.style.setProperty("--rx", `${rotateX}deg`);
    card.style.setProperty("--ry", `${rotateY}deg`);
  };

  const onLeaveCard = (event) => {
    const card = event.currentTarget;
    card.style.setProperty("--rx", "0deg");
    card.style.setProperty("--ry", "0deg");
  };

  return (
    <section className="section commerce-section">
      <div className="section-title">
        <h2>Interactive intelligence marketplace</h2>
        <p>Designed with ecommerce-like interactions: chips, hover depth, motion cards, and responsive grids.</p>
      </div>

      <div className="chip-row">
        {categoryChips.map((chip) => (
          <button
            type="button"
            key={chip}
            className={chip === activeChip ? "chip active" : "chip"}
            onClick={() => setActiveChip(chip)}
          >
            {chip}
          </button>
        ))}
      </div>

      <div className="showcase-grid">
        {showcaseCards.map((item, index) => {
          const Icon = icons[index % icons.length];
          return (
            <motion.article
              key={item.title}
              className="showcase-card"
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ delay: index * 0.08, duration: 0.35 }}
              onMouseMove={onMoveCard}
              onMouseLeave={onLeaveCard}
            >
              <div className="showcase-top">
                <span className="tag">{item.tag}</span>
                <Icon size={16} />
              </div>
              <h3>{item.title}</h3>
              <h4>{item.subtitle}</h4>
              <p>{item.description}</p>
              <small>Focused view: {activeChip}</small>
            </motion.article>
          );
        })}
      </div>

      <div className="promo-banner">
        <strong>Pro Tip:</strong> Add backend APIs later and keep this same UI for real data streaming.
      </div>
    </section>
  );
}
