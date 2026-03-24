import { useEffect, useState } from "react";

function App() {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_URL = "https://news-dashboard-eitf.onrender.com/topics";

  const fetchData = async () => {
    try {
      const res = await fetch(API_URL);

      if (!res.ok) {
        throw new Error("Failed to fetch");
      }

      const data = await res.json();
      setTopics(data);
      setLoading(false);
    } catch (err) {
      console.error("Error:", err);
      setError("Failed to load news");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(); // initial load

    const interval = setInterval(() => {
      fetchData(); // auto refresh every 60 sec
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>🔥 Live News Dashboard</h1>

      {loading && <p>Loading news...</p>}
      {error && <p>{error}</p>}

      {!loading && topics.length === 0 && <p>No news available</p>}

      {topics.map((t, index) => (
        <div
          key={index}
          style={{
            border: "1px solid #ccc",
            padding: "15px",
            marginBottom: "15px",
            borderRadius: "10px",
            background: "#111",
            color: "#fff"
          }}
        >
          <h3>🔥 {t.headline}</h3>

          <p style={{ color: "#ccc" }}>
            {t.summary || "No summary available"}
          </p>

          <p>
            <strong>Updates:</strong> {t.updates}
          </p>

          <p style={{ fontSize: "12px", color: "#aaa" }}>
            {t.last_updated
              ? new Date(t.last_updated).toLocaleString()
              : "No time"}
          </p>
        </div>
      ))}
    </div>
  );
}

export default App;