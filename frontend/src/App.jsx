import { useEffect, useState } from "react";

function App() {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);

  const API_URL = "https://news-dashboard-6grl.onrender.com/topics";

  // 🔁 Fetch with retry (handles Render sleep)
  const fetchTopics = async () => {
    try {
      console.log("Fetching topics...");

      const res = await fetch(API_URL);

      console.log("Status:", res.status);

      if (!res.ok) {
        throw new Error("Response not OK");
      }

      const data = await res.json();

      console.log("DATA:", data);

      setTopics(data);
      setLoading(false);

    } catch (err) {
      console.error("Fetch failed, retrying in 5s...", err);

      // retry after 5 sec
      setTimeout(fetchTopics, 5000);
    }
  };

  useEffect(() => {
    fetchTopics();
  }, []);

  return (
    <div
      style={{
        padding: "20px",
        backgroundColor: "#0f172a",
        minHeight: "100vh",
        color: "white"
      }}
    >
      <h1 style={{ textAlign: "center" }}>
        🔥 Live News Dashboard
      </h1>

      {/* 🔄 Loading state */}
      {loading ? (
        <div style={{ textAlign: "center", marginTop: "40px" }}>
          <p>Waking up server... ⏳</p>
        </div>
      ) : topics.length === 0 ? (
        <p>No topics found</p>
      ) : (
        topics.map((t, i) => (
          <div
            key={i}
            style={{
              border: "1px solid #334155",
              borderRadius: "12px",
              padding: "15px",
              marginBottom: "15px",
              backgroundColor: "#1e293b"
            }}
          >
            <h3>🔥 {t.headline}</h3>

            <p style={{ color: "#94a3b8" }}>
              Updates: {t.updates}
            </p>

            <p>{t.summary}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default App;