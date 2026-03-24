import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "https://news-dashboard-6gr1.onrender.com/topics";

function App() {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await fetch(API_URL, {
          cache: "no-store", // 🔥 prevent caching
        });

        if (!res.ok) {
          throw new Error("Failed to fetch");
        }

        const data = await res.json();
        setNews(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load news");
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  return (
    <div className="container">
      <h1>🔥 Live News Dashboard</h1>

      {loading && <p>Loading news...</p>}
      {error && <p>{error}</p>}

      {!loading && news.length === 0 && <p>No news available</p>}

      {news.map((item, index) => (
        <div key={index} className="card">
          <h2>🔥 {item.headline}</h2>

          <p><b>Updates:</b> {item.updates}</p>

          <p>
            <b>Last Updated:</b>{" "}
            {item.last_updated
              ? new Date(item.last_updated).toLocaleString()
              : "N/A"}
          </p>

          <p className="summary">{item.summary}</p>
        </div>
      ))}
    </div>
  );
}

export default App;