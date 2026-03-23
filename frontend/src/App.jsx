import { useEffect, useState } from "react";

function App() {
  const [topics, setTopics] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/topics")
      .then((res) => res.json())
      .then((data) => {
        console.log("DATA:", data); // 🔍 debug
        setTopics(data);
      })
      .catch((err) => console.error("ERROR:", err));
  }, []);

  if (!topics || topics.length === 0) {
    return <h1 style={{ textAlign: "center" }}>Loading news...</h1>;
  }

  return (
    <div style={{ padding: "20px", color: "white" }}>
      <h1>🔥 Live News Dashboard</h1>

      {topics.map((topic, index) => (
        <div
          key={index}
          style={{
            marginBottom: "20px",
            padding: "15px",
            border: "1px solid #444",
            borderRadius: "10px",
          }}
        >
          <h2>
            🔥 {topic.headline || topic.topic_name || "News Update"}
          </h2>

          <p>Updates: {topic.updates}</p>

          <p>{topic.summary || "No summary available"}</p>
        </div>
      ))}
    </div>
  );
}

export default App;