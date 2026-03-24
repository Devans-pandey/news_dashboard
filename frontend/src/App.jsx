import { useEffect, useState } from "react";

function App() {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);

  const API_URL = "https://news-dashboard-6rg1.onrender.com/topics";

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(API_URL);

        const data = await res.json();

        console.log("DATA:", data);

        // ✅ IMPORTANT FIX
        if (Array.isArray(data)) {
          setTopics(data);
        } else {
          console.log("Not an array:", data);
        }

        setLoading(false); // 🔥 always stop loading

      } catch (err) {
        console.error("Error:", err);

        // retry after 5 sec
        setTimeout(fetchData, 5000);
      }
    };

    fetchData();
  }, []);

  return (
    <div style={{ padding: "20px", background: "#0f172a", minHeight: "100vh", color: "white" }}>
      <h1 style={{ textAlign: "center" }}>🔥 Live News Dashboard</h1>

      {loading ? (
        <p style={{ textAlign: "center" }}>Waking up server... ⏳</p>
      ) : topics.length === 0 ? (
        <p style={{ textAlign: "center" }}>No data found</p>
      ) : (
        topics.map((t, i) => (
          <div
            key={i}
            style={{
              border: "1px solid #334155",
              borderRadius: "12px",
              padding: "15px",
              marginBottom: "15px",
              background: "#1e293b"
            }}
          >
            <h3>🔥 {t.headline}</h3>
            <p style={{ color: "#94a3b8" }}>Updates: {t.updates}</p>
            <p>{t.summary}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default App;