import { useEffect, useState, useCallback } from "react";
import "./App.css";

// ============================================
// CONFIG
// ============================================
const API_BASE = "https://news-dashboard-xsto.onrender.com";

// Topic color mapping
const TOPIC_COLORS = {
  "War and Conflict": {
    accent: "linear-gradient(135deg, #ef4444, #dc2626)",
    glow: "rgba(239, 68, 68, 0.08)",
    badgeBg: "rgba(239, 68, 68, 0.12)",
    badgeColor: "#f87171",
    badgeBorder: "rgba(239, 68, 68, 0.25)",
    icon: "⚔️",
  },
  Defense: {
    accent: "linear-gradient(135deg, #f97316, #ea580c)",
    glow: "rgba(249, 115, 22, 0.08)",
    badgeBg: "rgba(249, 115, 22, 0.12)",
    badgeColor: "#fb923c",
    badgeBorder: "rgba(249, 115, 22, 0.25)",
    icon: "🛡️",
  },
  "India Politics": {
    accent: "linear-gradient(135deg, #22c55e, #16a34a)",
    glow: "rgba(34, 197, 94, 0.08)",
    badgeBg: "rgba(34, 197, 94, 0.12)",
    badgeColor: "#4ade80",
    badgeBorder: "rgba(34, 197, 94, 0.25)",
    icon: "🏛️",
  },
  "International Relations": {
    accent: "linear-gradient(135deg, #3b82f6, #2563eb)",
    glow: "rgba(59, 130, 246, 0.08)",
    badgeBg: "rgba(59, 130, 246, 0.12)",
    badgeColor: "#60a5fa",
    badgeBorder: "rgba(59, 130, 246, 0.25)",
    icon: "🌍",
  },
  Technology: {
    accent: "linear-gradient(135deg, #06b6d4, #0891b2)",
    glow: "rgba(6, 182, 212, 0.08)",
    badgeBg: "rgba(6, 182, 212, 0.12)",
    badgeColor: "#22d3ee",
    badgeBorder: "rgba(6, 182, 212, 0.25)",
    icon: "💻",
  },
  Economy: {
    accent: "linear-gradient(135deg, #eab308, #ca8a04)",
    glow: "rgba(234, 179, 8, 0.08)",
    badgeBg: "rgba(234, 179, 8, 0.12)",
    badgeColor: "#facc15",
    badgeBorder: "rgba(234, 179, 8, 0.25)",
    icon: "📊",
  },
  "General News": {
    accent: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
    glow: "rgba(139, 92, 246, 0.08)",
    badgeBg: "rgba(139, 92, 246, 0.12)",
    badgeColor: "#a78bfa",
    badgeBorder: "rgba(139, 92, 246, 0.25)",
    icon: "📰",
  },
};

function getTopicStyle(topic) {
  return TOPIC_COLORS[topic] || TOPIC_COLORS["General News"];
}

// ============================================
// UTILITIES
// ============================================
function timeAgo(dateStr) {
  if (!dateStr) return "—";
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

// ============================================
// COMPONENTS
// ============================================

function Header({ stats }) {
  return (
    <header className="dashboard-header">
      <div className="header-badge">
        <span className="live-dot"></span>
        Live Intelligence Feed
      </div>
      <h1 className="header-title">News Dashboard</h1>
      <p className="header-subtitle">
        Real-time updates from Telegram channels, classified by AI
      </p>

      {stats && (
        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-value">{stats.total_messages}</span>
            <span className="stat-label">Messages</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.total_topics}</span>
            <span className="stat-label">Topics</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{timeAgo(stats.last_updated)}</span>
            <span className="stat-label">Last Update</span>
          </div>
        </div>
      )}
    </header>
  );
}

function TopicCard({ topic, onClick }) {
  const style = getTopicStyle(topic.topic);

  return (
    <article
      className="topic-card"
      id={`topic-card-${topic.topic.replace(/\s+/g, "-").toLowerCase()}`}
      onClick={() => onClick(topic.topic)}
      style={{
        "--card-accent": style.accent,
        "--card-glow": style.glow,
        "--badge-bg": style.badgeBg,
        "--badge-color": style.badgeColor,
        "--badge-border": style.badgeBorder,
      }}
    >
      <div className="card-top">
        <span className="topic-badge">
          <span className="topic-badge-dot"></span>
          {topic.topic}
        </span>
        <span className="message-count">
          <span className="message-count-icon">💬</span>
          {topic.message_count}
        </span>
      </div>

      <h2 className="card-headline">{topic.headline}</h2>

      <p className="card-summary">
        {topic.summary || "No summary available"}
      </p>

      <div className="card-footer">
        <span className="card-channel">@{topic.channel}</span>
        <span className="card-time">{timeAgo(topic.last_updated)}</span>
        <span className="card-arrow">View all →</span>
      </div>
    </article>
  );
}

function TopicDetail({ topicName, onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/topics/${encodeURIComponent(topicName)}`)
      .then((res) => res.json())
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [topicName]);

  const style = getTopicStyle(topicName);

  if (loading) {
    return (
      <div className="detail-view">
        <button className="detail-back" onClick={onBack}>
          ← Back to topics
        </button>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <span className="loading-text">Loading messages...</span>
        </div>
      </div>
    );
  }

  if (!data || !data.messages || data.messages.length === 0) {
    return (
      <div className="detail-view">
        <button className="detail-back" onClick={onBack}>
          ← Back to topics
        </button>
        <div className="empty-container">
          <div className="empty-icon">📭</div>
          <h3 className="empty-title">No messages found</h3>
          <p className="empty-message">
            No messages available for this topic yet.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="detail-view">
      <button className="detail-back" onClick={onBack}>
        ← Back to topics
      </button>

      <div
        className="detail-header"
        style={{ "--card-accent": style.accent }}
      >
        <span
          className="detail-topic-badge"
          style={{
            "--badge-bg": style.badgeBg,
            "--badge-color": style.badgeColor,
            "--badge-border": style.badgeBorder,
          }}
        >
          {style.icon} {topicName}
        </span>
        <h1 className="detail-headline">{data.headline}</h1>
        <p className="detail-summary">{data.summary}</p>
        <div className="detail-meta">
          <span className="detail-meta-item">
            Messages: <span className="detail-meta-value">{data.count}</span>
          </span>
          <span className="detail-meta-item">
            Last update:{" "}
            <span className="detail-meta-value">
              {timeAgo(data.last_updated)}
            </span>
          </span>
        </div>
      </div>

      <h3 className="messages-section-title">
        All Messages ({data.count})
      </h3>

      <div className="messages-list">
        {data.messages.map((msg, i) => (
          <div className="message-item" key={i}>
            <p className="message-text">{msg.text}</p>
            <div className="message-meta">
              <span className="message-channel">📡 @{msg.channel}</span>
              <span className="message-time">{timeAgo(msg.created_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="skeleton-grid">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div className="skeleton-card" key={i}>
          <div className="skeleton-line short"></div>
          <div className="skeleton-line long"></div>
          <div className="skeleton-line medium"></div>
          <div className="skeleton-line short"></div>
        </div>
      ))}
    </div>
  );
}

// ============================================
// MAIN APP
// ============================================

function App() {
  const [topics, setTopics] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [countdown, setCountdown] = useState(60);

  const fetchData = useCallback(async () => {
    try {
      const [topicsRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/topics`),
        fetch(`${API_BASE}/stats`),
      ]);

      if (!topicsRes.ok) throw new Error("Failed to fetch topics");

      const topicsData = await topicsRes.json();
      const statsData = await statsRes.json();

      setTopics(topicsData);
      setStats(statsData);
      setError(null);
      setLoading(false);
    } catch (err) {
      console.error("Fetch error:", err);
      setError("Failed to load news feed. Please try again.");
      setLoading(false);
    }
  }, []);

  // Initial load + auto-refresh every 60s
  useEffect(() => {
    fetchData();

    const interval = setInterval(() => {
      fetchData();
      setCountdown(60);
    }, 60000);

    return () => clearInterval(interval);
  }, [fetchData]);

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 60));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleTopicClick = (topicName) => {
    setSelectedTopic(topicName);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleBack = () => {
    setSelectedTopic(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="dashboard">
      <Header stats={stats} />

      {/* Error state */}
      {error && (
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h3 className="error-title">Connection Error</h3>
          <p className="error-message">{error}</p>
          <button className="retry-btn" onClick={fetchData}>
            🔄 Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && !error && <LoadingSkeleton />}

      {/* Detail view */}
      {!loading && !error && selectedTopic && (
        <TopicDetail topicName={selectedTopic} onBack={handleBack} />
      )}

      {/* Grid view */}
      {!loading && !error && !selectedTopic && (
        <>
          {topics.length === 0 ? (
            <div className="empty-container">
              <div className="empty-icon">📡</div>
              <h3 className="empty-title">No news yet</h3>
              <p className="empty-message">
                Waiting for messages from Telegram channels...
              </p>
            </div>
          ) : (
            <>
              <div className="topics-grid">
                {topics.map((topic, i) => (
                  <TopicCard
                    key={topic.topic + i}
                    topic={topic}
                    onClick={handleTopicClick}
                  />
                ))}
              </div>

              <div className="refresh-bar">
                <span className="refresh-text">
                  Auto-refresh in{" "}
                  <span className="refresh-countdown">{countdown}s</span>
                </span>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

export default App;