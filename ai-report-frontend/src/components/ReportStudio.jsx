import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CalendarClock, FileText, Sparkles } from "lucide-react";
import { generateReport } from "../api/client";

function Pill({ value }) {
  return <span className={`pill ${value.toLowerCase()}`}>{value}</span>;
}

export default function ReportStudio() {
  const [topic, setTopic] = useState("Latest AI industry movements");
  const [period, setPeriod] = useState("weekly");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  const quickTopics = useMemo(
    () => ["Open-source LLM race", "AI policy roundup", "Enterprise AI adoption", "AI funding watch"],
    []
  );

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await generateReport({ topic, period });
      setReport(data);
    } catch (apiError) {
      setError("Could not generate report. Ensure backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="report-studio" className="section">
      <div className="section-title">
        <h2>Report Studio</h2>
        <p>Interactive report control panel. Hook this to your backend later without changing the UI.</p>
      </div>

      <div className="studio-grid">
        <div className="panel">
          <h3>Generate report</h3>
          <label htmlFor="topic">Topic</label>
          <input id="topic" value={topic} onChange={(e) => setTopic(e.target.value)} />

          <label htmlFor="period">Frequency</label>
          <div className="select-wrap">
            <CalendarClock size={15} />
            <select id="period" value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <button type="button" className="btn btn-primary full-width" onClick={handleGenerate} disabled={loading}>
            <Sparkles size={15} />
            {loading ? "Generating..." : "Generate Now"}
          </button>

          <div className="quick-list">
            {quickTopics.map((item) => (
              <button key={item} type="button" onClick={() => setTopic(item)}>
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="panel report-output">
          <div className="panel-head">
            <h3>
              <FileText size={16} /> Live preview
            </h3>
          </div>

          {error ? <p className="error-text">{error}</p> : null}

          {!report ? (
            <p className="muted">No report generated yet. Choose topic and click generate.</p>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
              <h4>{report.title}</h4>
              <small>{new Date(report.generated_at).toLocaleString()}</small>
              <p>{report.summary}</p>
              <div className="metric-strip">
                <article className="metric-card">
                  <strong>{report.metrics?.total_articles_reviewed ?? 0}</strong>
                  <span>Articles</span>
                </article>
                <article className="metric-card">
                  <strong>{report.metrics?.high_impact_items ?? 0}</strong>
                  <span>High Impact</span>
                </article>
                <article className="metric-card">
                  <strong>{report.metrics?.categories_covered ?? 0}</strong>
                  <span>Categories</span>
                </article>
              </div>
              <div className="highlight-list">
                {report.highlights.map((item) => (
                  <article key={`${item.type}-${item.title}`} className="highlight-item">
                    <div>
                      <strong>{item.title}</strong>
                      <p>{item.type}</p>
                    </div>
                    <div className="highlight-meta">
                      <Pill value={item.impact} />
                      <small>{item.source}</small>
                    </div>
                  </article>
                ))}
              </div>
              {report.next_actions?.length ? (
                <ul className="next-actions">
                  {report.next_actions.slice(0, 3).map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              ) : null}
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
}
