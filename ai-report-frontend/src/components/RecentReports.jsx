import { useEffect, useState } from "react";
import { RefreshCcw } from "lucide-react";
import { fetchReportHistory } from "../api/client";

export default function RecentReports() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchReportHistory();
      setItems(Array.isArray(data) ? data.slice(0, 6) : []);
    } catch {
      setError("Could not load recent reports.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <section className="section recent-reports">
      <div className="section-title row-title">
        <div>
          <h2>Recent Reports</h2>
          <p>Latest reports generated from your backend history endpoint.</p>
        </div>
        <button type="button" className="btn btn-ghost refresh-btn" onClick={load} disabled={loading}>
          <RefreshCcw size={15} />
          Refresh
        </button>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="report-history-grid">
        {loading
          ? Array.from({ length: 4 }).map((_, index) => (
              <article key={index} className="history-card skeleton-card">
                <div />
                <div />
              </article>
            ))
          : items.map((item) => (
              <article key={item.id} className="history-card">
                <strong>{item.title}</strong>
                <small>{item.date}</small>
                <span>{item.id}</span>
              </article>
            ))}
      </div>
    </section>
  );
}
