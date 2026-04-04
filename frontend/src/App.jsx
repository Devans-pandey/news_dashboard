import { useEffect, useState, useCallback } from "react";
import "./App.css";
import WorldMap from "./WorldMap";

// ============================================
// CONFIG
// ============================================
const API_BASE = "https://news-dashboard-xsto.onrender.com";

// Topic color mapping
const TOPIC_COLORS = {
  "War and Conflict": {
    accent: "#ef4444",
    badgeBg: "rgba(239, 68, 68, 0.1)",
    badgeColor: "#f87171",
    badgeBorder: "rgba(239, 68, 68, 0.2)",
    icon: "⚔️",
  },
  Defense: {
    accent: "#f97316",
    badgeBg: "rgba(249, 115, 22, 0.1)",
    badgeColor: "#fb923c",
    badgeBorder: "rgba(249, 115, 22, 0.2)",
    icon: "🛡️",
  },
  "India Politics": {
    accent: "#22c55e",
    badgeBg: "rgba(34, 197, 94, 0.1)",
    badgeColor: "#4ade80",
    badgeBorder: "rgba(34, 197, 94, 0.2)",
    icon: "🏛️",
  },
  "International Relations": {
    accent: "#38bdf8",
    badgeBg: "rgba(56, 189, 248, 0.1)",
    badgeColor: "#7dd3fc",
    badgeBorder: "rgba(56, 189, 248, 0.2)",
    icon: "🌍",
  },
  Technology: {
    accent: "#06b6d4",
    badgeBg: "rgba(6, 182, 212, 0.1)",
    badgeColor: "#22d3ee",
    badgeBorder: "rgba(6, 182, 212, 0.2)",
    icon: "💻",
  },
  Economy: {
    accent: "#eab308",
    badgeBg: "rgba(234, 179, 8, 0.1)",
    badgeColor: "#facc15",
    badgeBorder: "rgba(234, 179, 8, 0.2)",
    icon: "📊",
  },
  "General News": {
    accent: "#a78bfa",
    badgeBg: "rgba(167, 139, 250, 0.1)",
    badgeColor: "#c4b5fd",
    badgeBorder: "rgba(167, 139, 250, 0.2)",
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
// SIDEBAR
// ============================================

function Sidebar({ topics, selectedTopic, onSelectTopic, stats }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">N</div>
          <div>
            <div className="sidebar-logo-text">NewsGrid</div>
            <div className="sidebar-logo-sub">Intelligence Hub</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-title">Overview</div>
        <button
          className={`sidebar-item ${!selectedTopic ? "active" : ""}`}
          onClick={() => onSelectTopic(null)}
        >
          <span className="sidebar-item-icon">📊</span>
          Dashboard
        </button>

        <div className="sidebar-section-title">Topics</div>
        {topics.map((t) => {
          const style = getTopicStyle(t.topic);
          return (
            <button
              key={t.topic}
              className={`sidebar-item ${
                selectedTopic === t.topic ? "active" : ""
              }`}
              onClick={() => onSelectTopic(t.topic)}
            >
              <span className="sidebar-item-icon">{style.icon}</span>
              {t.topic}
              <span className="sidebar-item-count">{t.message_count}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <div className="sidebar-status">
          <span className={`status-dot ${stats ? "" : "offline"}`}></span>
          {stats ? "System Online" : "Connecting..."}
        </div>
      </div>
    </aside>
  );
}

// ============================================
// TOP BAR
// ============================================

function TopBar({ stats, countdown, selectedTopic, onBack }) {
  return (
    <div className="top-bar">
      <div className="top-bar-left">
        {selectedTopic ? (
          <>
            <button className="detail-back" onClick={onBack} style={{ margin: 0 }}>
              ← Back
            </button>
            <span className="page-title">{selectedTopic}</span>
          </>
        ) : (
          <span className="page-title">Dashboard</span>
        )}
      </div>

      <div className="top-bar-right">
        {stats && (
          <>
            <div className="top-bar-stat">
              <span className="top-bar-stat-value">{stats.total_messages}</span>
              Messages
            </div>
            <div className="top-bar-divider"></div>
            <div className="top-bar-stat">
              <span className="top-bar-stat-value">{stats.total_topics}</span>
              Topics
            </div>
            <div className="top-bar-divider"></div>
          </>
        )}
        <div className="refresh-indicator">
          Refresh in{" "}
          <span className="refresh-countdown">{countdown}s</span>
        </div>
      </div>
    </div>
  );
}

// ============================================
// METRIC CARDS
// ============================================

function MetricCards({ stats, topics }) {
  const latestChannel = topics.length > 0 ? topics[0].channel : "—";
  const totalMsgs = stats?.total_messages || 0;

  return (
    <div className="metrics-row">
      <div className="metric-card">
        <div className="metric-icon blue">📨</div>
        <div className="metric-info">
          <span className="metric-value">{totalMsgs}</span>
          <span className="metric-label">Total Messages</span>
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-icon green">📡</div>
        <div className="metric-info">
          <span className="metric-value">{stats?.total_topics || 0}</span>
          <span className="metric-label">Active Topics</span>
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-icon orange">🕐</div>
        <div className="metric-info">
          <span className="metric-value">{timeAgo(stats?.last_updated)}</span>
          <span className="metric-label">Last Update</span>
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-icon purple">📺</div>
        <div className="metric-info">
          <span className="metric-value">@{latestChannel}</span>
          <span className="metric-label">Top Channel</span>
        </div>
      </div>
    </div>
  );
}

// ============================================
// TOPIC CARD
// ============================================

function TopicCard({ topic, onClick }) {
  const style = getTopicStyle(topic.topic);

  return (
    <article
      className="topic-card"
      id={`topic-card-${topic.topic.replace(/\s+/g, "-").toLowerCase()}`}
      onClick={() => onClick(topic.topic)}
      style={{
        "--card-accent": style.accent,
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
        <span className="card-arrow">View →</span>
      </div>
    </article>
  );
}

// ============================================
// TOPIC DETAIL
// ============================================

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
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <span className="loading-text">Loading messages…</span>
        </div>
      </div>
    );
  }

  if (!data || !data.messages || data.messages.length === 0) {
    return (
      <div className="detail-view">
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

// ============================================
// LOADING SKELETON
// ============================================

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
  };

  const handleBack = () => {
    setSelectedTopic(null);
  };

  return (
    <div className="app-layout">
      <Sidebar
        topics={topics}
        selectedTopic={selectedTopic}
        onSelectTopic={(topic) => {
          setSelectedTopic(topic);
        }}
        stats={stats}
      />

      <main className="main-content">
        <TopBar
          stats={stats}
          countdown={countdown}
          selectedTopic={selectedTopic}
          onBack={handleBack}
        />

        <div className="dashboard-content">
          {/* Error state */}
          {error && (
            <div className="error-container">
              <div className="error-icon">⚠️</div>
              <h3 className="error-title">Connection Error</h3>
              <p className="error-message">{error}</p>
              <button className="retry-btn" onClick={fetchData}>
                Retry
              </button>
            </div>
          )}

          {/* Loading state */}
          {loading && !error && <LoadingSkeleton />}

          {/* Detail view */}
          {!loading && !error && selectedTopic && (
            <TopicDetail topicName={selectedTopic} onBack={handleBack} />
          )}

          {/* Dashboard view */}
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
                  <MetricCards stats={stats} topics={topics} />

                  <WorldMap
                    topics={topics}
                    onCountryClick={handleTopicClick}
                  />

                  <div className="section-header">
                    <span className="section-title">Latest Topics</span>
                    <span className="section-subtitle">
                      {topics.length} active topics
                    </span>
                  </div>

                  <div className="topics-grid">
                    {topics.map((topic, i) => (
                      <TopicCard
                        key={topic.topic + i}
                        topic={topic}
                        onClick={handleTopicClick}
                      />
                    ))}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;