import { memo, useState, useEffect, useRef, useMemo } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

// Country name → coordinates mapping for hotspot markers
const HOTSPOT_COORDS = {
  ukraine: { name: "Ukraine", coords: [31.16, 48.38] },
  russia: { name: "Russia", coords: [37.62, 55.75] },
  china: { name: "China", coords: [116.4, 39.9] },
  india: { name: "India", coords: [77.21, 28.61] },
  israel: { name: "Israel", coords: [35.21, 31.77] },
  iran: { name: "Iran", coords: [51.39, 35.69] },
  iraq: { name: "Iraq", coords: [44.37, 33.31] },
  syria: { name: "Syria", coords: [36.29, 33.51] },
  turkey: { name: "Turkey", coords: [32.86, 39.93] },
  pakistan: { name: "Pakistan", coords: [73.05, 33.69] },
  afghanistan: { name: "Afghanistan", coords: [69.17, 34.53] },
  usa: { name: "United States", coords: [-95.71, 37.09] },
  "united states": { name: "United States", coords: [-95.71, 37.09] },
  "north korea": { name: "North Korea", coords: [125.75, 39.02] },
  "south korea": { name: "South Korea", coords: [126.98, 37.57] },
  japan: { name: "Japan", coords: [139.69, 35.69] },
  taiwan: { name: "Taiwan", coords: [121.57, 25.03] },
  yemen: { name: "Yemen", coords: [44.21, 15.35] },
  lebanon: { name: "Lebanon", coords: [35.50, 33.89] },
  palestine: { name: "Palestine", coords: [35.23, 31.95] },
  gaza: { name: "Palestine", coords: [34.45, 31.5] },
  egypt: { name: "Egypt", coords: [31.24, 30.04] },
  saudi: { name: "Saudi Arabia", coords: [46.72, 24.71] },
  "saudi arabia": { name: "Saudi Arabia", coords: [46.72, 24.71] },
  myanmar: { name: "Myanmar", coords: [96.20, 16.87] },
  bangladesh: { name: "Bangladesh", coords: [90.4, 23.8] },
  nepal: { name: "Nepal", coords: [85.32, 27.7] },
  uk: { name: "United Kingdom", coords: [-1.17, 52.36] },
  "united kingdom": { name: "United Kingdom", coords: [-1.17, 52.36] },
  france: { name: "France", coords: [2.35, 48.86] },
  germany: { name: "Germany", coords: [10.45, 51.17] },
  poland: { name: "Poland", coords: [19.15, 51.92] },
  romania: { name: "Romania", coords: [24.97, 45.94] },
};

// Topic → color mapping
const TOPIC_MAP_COLORS = {
  "War and Conflict": "#ef4444",
  Defense: "#f97316",
  "India Politics": "#22c55e",
  "International Relations": "#38bdf8",
  Technology: "#06b6d4",
  Economy: "#eab308",
  "General News": "#a78bfa",
};

// Severity levels for legend
const SEVERITY_MAP = {
  "War and Conflict": { label: "High Alert", level: 3 },
  Defense: { label: "Elevated", level: 2 },
  "India Politics": { label: "Monitoring", level: 1 },
  "International Relations": { label: "Monitoring", level: 1 },
  Technology: { label: "Info", level: 0 },
  Economy: { label: "Info", level: 0 },
  "General News": { label: "Info", level: 0 },
};

function extractHotspots(topics) {
  const hotspots = {};

  for (const topic of topics) {
    const allText = (
      (topic.headline || "") +
      " " +
      (topic.summary || "") +
      " " +
      (topic.topic || "")
    ).toLowerCase();

    for (const [keyword, data] of Object.entries(HOTSPOT_COORDS)) {
      if (allText.includes(keyword)) {
        const key = data.name;
        if (!hotspots[key]) {
          hotspots[key] = {
            name: data.name,
            coords: data.coords,
            count: 0,
            topics: new Set(),
          };
        }
        hotspots[key].count += topic.message_count || 1;
        hotspots[key].topics.add(topic.topic);
      }
    }
  }

  return Object.values(hotspots).map((h) => ({
    ...h,
    topics: Array.from(h.topics),
    primaryTopic: Array.from(h.topics)[0] || "General News",
    color: TOPIC_MAP_COLORS[Array.from(h.topics)[0]] || "#a78bfa",
    severity: SEVERITY_MAP[Array.from(h.topics)[0]]?.level || 0,
  }));
}

// Dark vector tile style — using free dark tiles
const MAP_STYLE = {
  version: 8,
  name: "Dark",
  sources: {
    "carto-dark": {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
      ],
      tileSize: 256,
      attribution: "© CARTO © OpenStreetMap contributors",
      maxzoom: 18,
    },
  },
  layers: [
    {
      id: "carto-dark-layer",
      type: "raster",
      source: "carto-dark",
      minzoom: 0,
      maxzoom: 18,
    },
  ],
  glyphs: "https://fonts.openmaptiles.org/{fontstack}/{range}.pbf",
};

function WorldMap({ topics, onCountryClick }) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const popupRef = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const hotspots = useMemo(() => extractHotspots(topics), [topics]);

  // Initialize MapLibre
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: MAP_STYLE,
      center: [20, 30], // Centered beautifully to show Europe/MiddleEast/Asia
      zoom: 1.8,
      interactive: false, // Disables all zooming/panning like worldmonitor.app!
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

    map.on("load", () => {
      setMapLoaded(true);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update markers when hotspots change
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    // Remove old markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Remove old popup
    if (popupRef.current) {
      popupRef.current.remove();
      popupRef.current = null;
    }

    // Add new markers
    hotspots.forEach((hs) => {
      const size = Math.min(16 + hs.count * 1.2, 48);
      const innerSize = Math.max(size * 0.45, 8);

      // Create marker element
      const el = document.createElement("div");
      el.className = "maplibre-hotspot-marker";
      el.style.cssText = `
        width: ${size}px;
        height: ${size}px;
        position: relative;
        cursor: pointer;
      `;

      // Outer glow ring
      const outer = document.createElement("div");
      outer.className = "hotspot-outer";
      outer.style.cssText = `
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: ${hs.color};
        opacity: 0.2;
        pointer-events: none;
        animation: mapPulse 2.5s ease-in-out infinite;
      `;

      // Inner solid circle
      const inner = document.createElement("div");
      inner.className = "hotspot-inner";
      inner.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: ${innerSize}px;
        height: ${innerSize}px;
        border-radius: 50%;
        background: ${hs.color};
        border: 2px solid rgba(255,255,255,0.3);
        box-shadow: 0 0 12px ${hs.color}80, 0 0 4px ${hs.color}40;
      `;

      // Count label (if > 3)
      if (hs.count > 3) {
        const label = document.createElement("div");
        label.className = "hotspot-count-label";
        label.textContent = hs.count;
        label.style.cssText = `
          position: absolute;
          top: -8px;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(11, 17, 32, 0.9);
          color: ${hs.color};
          font-size: 10px;
          font-weight: 700;
          font-family: 'Outfit', 'Inter', sans-serif;
          padding: 1px 5px;
          border-radius: 4px;
          border: 1px solid ${hs.color}40;
          white-space: nowrap;
          pointer-events: none;
          line-height: 1.3;
        `;
        el.appendChild(label);
      }

      el.appendChild(outer);
      el.appendChild(inner);

      // Tooltip on hover
      let leaveTimeout;

      // Ensure stable circular collision box for marker
      el.style.borderRadius = "50%";
      
      el.addEventListener("mouseenter", () => {
        clearTimeout(leaveTimeout);
        if (popupRef.current) popupRef.current.remove();

        const severityLabel = SEVERITY_MAP[hs.primaryTopic]?.label || "Info";
        const severityClass =
          hs.severity >= 3 ? "hot" : hs.severity >= 2 ? "elevated" : "active";

        const topicTags = hs.topics
          .map(
            (t) =>
              `<span class="popup-topic-tag" style="border-color:${TOPIC_MAP_COLORS[t] || "#a78bfa"};color:${TOPIC_MAP_COLORS[t] || "#a78bfa"}">${t}</span>`
          )
          .join("");

        const popup = new maplibregl.Popup({
          offset: [0, -(size / 2 + 8)],
          closeButton: false,
          closeOnClick: false,
          className: "map-custom-popup",
          maxWidth: "260px",
        })
          .setLngLat(hs.coords)
          .setHTML(
            `<div class="popup-card">
              <div class="popup-header">
                <span class="popup-country">${hs.name}</span>
                <span class="popup-severity ${severityClass}">${severityLabel}</span>
              </div>
              <div class="popup-stats">
                <div class="popup-stat">
                  <span class="popup-stat-label">Messages</span>
                  <span class="popup-stat-value">${hs.count}</span>
                </div>
                <div class="popup-stat">
                  <span class="popup-stat-label">Topics</span>
                  <span class="popup-stat-value">${hs.topics.length}</span>
                </div>
              </div>
              <div class="popup-topics">${topicTags}</div>
            </div>`
          )
          .addTo(mapRef.current);

        // Keep popup open if hovering over the popup itself!
        const popupEl = popup.getElement();
        if (popupEl) {
          // ensure the cursor inside popup is standard arrow
          popupEl.style.cursor = 'default';
          
          popupEl.addEventListener('mouseenter', () => {
            clearTimeout(leaveTimeout);
          });
          
          popupEl.addEventListener('mouseleave', () => {
            if (popupRef.current === popup) {
              popupRef.current.remove();
              popupRef.current = null;
            }
          });
        }

        popupRef.current = popup;
      });

      el.addEventListener("mouseleave", () => {
        // Wait 150ms before destroying, allows mouse to travel into popup
        leaveTimeout = setTimeout(() => {
          if (popupRef.current) {
            popupRef.current.remove();
            popupRef.current = null;
          }
        }, 150);
      });

      // Click -> navigate to topic
      el.addEventListener("click", () => {
        if (onCountryClick && hs.primaryTopic) {
          onCountryClick(hs.primaryTopic);
        }
      });

      const marker = new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat(hs.coords)
        .addTo(mapRef.current);

      markersRef.current.push(marker);
    });
  }, [hotspots, mapLoaded, onCountryClick]);

  // Build visible legend items
  const legendItems = useMemo(() => {
    const seen = new Set();
    return [
      { label: "High Alert", color: "#ef4444" },
      { label: "Elevated", color: "#f97316" },
      { label: "Monitoring", color: "#22c55e" },
      { label: "Info", color: "#38bdf8" },
    ].filter((item) => {
      if (seen.has(item.label)) return false;
      seen.add(item.label);
      return true;
    });
  }, []);

  return (
    <div className="world-map-section">
      <div className="map-header">
        <h2 className="map-title">
          <span className="map-title-dot"></span>
          Global Situation Monitor
        </h2>
        <div className="map-controls">
          <span className="map-live-badge">
            <span className="map-live-dot"></span>
            LIVE
          </span>
        </div>
      </div>

      <div className="map-canvas-wrapper">
        <div ref={mapContainerRef} className="map-container" />

        {!mapLoaded && (
          <div className="map-loading-overlay">
            <div className="loading-spinner"></div>
            <span className="loading-text">Loading map…</span>
          </div>
        )}

        {/* Legend */}
        <div className="map-legend-bar">
          <span className="map-legend-label">LEGEND</span>
          {legendItems.map((item) => (
            <span key={item.label} className="legend-item">
              <span
                className="legend-dot"
                style={{ background: item.color }}
              ></span>
              {item.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default memo(WorldMap);
