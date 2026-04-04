import { memo, useState, useEffect, useRef, useMemo, useCallback } from "react";
import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";

// TopoJSON world map CDN
const GEO_URL =
  "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Country name → ISO numeric code mapping
const COUNTRY_CODES = {
  ukraine: "804", russia: "643", china: "156", india: "356",
  israel: "376", iran: "364", iraq: "368", syria: "760",
  turkey: "792", pakistan: "586", afghanistan: "004",
  usa: "840", "united states": "840", "north korea": "408",
  "south korea": "410", japan: "392", taiwan: "158",
  yemen: "887", lebanon: "422", palestine: "275", gaza: "275",
  egypt: "818", libya: "434", saudi: "682", "saudi arabia": "682",
  myanmar: "104", bangladesh: "050", nepal: "524",
  uk: "826", "united kingdom": "826", france: "250",
  germany: "276", poland: "616", romania: "642",
};

// Hotspot markers [lng, lat]
const HOTSPOT_COORDS = {
  "804": { name: "Ukraine", coords: [31.16, 48.38] },
  "643": { name: "Russia", coords: [37.62, 55.75] },
  "156": { name: "China", coords: [116.4, 39.9] },
  "356": { name: "India", coords: [77.21, 28.61] },
  "376": { name: "Israel", coords: [35.21, 31.77] },
  "364": { name: "Iran", coords: [51.39, 35.69] },
  "368": { name: "Iraq", coords: [44.37, 33.31] },
  "760": { name: "Syria", coords: [36.29, 33.51] },
  "792": { name: "Turkey", coords: [32.86, 39.93] },
  "586": { name: "Pakistan", coords: [73.05, 33.69] },
  "004": { name: "Afghanistan", coords: [69.17, 34.53] },
  "840": { name: "United States", coords: [-95.71, 37.09] },
  "408": { name: "North Korea", coords: [125.75, 39.02] },
  "410": { name: "South Korea", coords: [126.98, 37.57] },
  "392": { name: "Japan", coords: [139.69, 35.69] },
  "158": { name: "Taiwan", coords: [121.57, 25.03] },
  "887": { name: "Yemen", coords: [44.21, 15.35] },
  "422": { name: "Lebanon", coords: [35.50, 33.89] },
  "275": { name: "Palestine", coords: [35.23, 31.95] },
  "818": { name: "Egypt", coords: [31.24, 30.04] },
  "682": { name: "Saudi Arabia", coords: [46.72, 24.71] },
  "104": { name: "Myanmar", coords: [96.20, 16.87] },
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

function extractCountryData(topics) {
  const countryData = {};

  for (const topic of topics) {
    const allText = (
      (topic.headline || "") +
      " " +
      (topic.summary || "") +
      " " +
      (topic.topic || "")
    ).toLowerCase();

    for (const [keyword, numCode] of Object.entries(COUNTRY_CODES)) {
      if (allText.includes(keyword)) {
        if (!countryData[numCode]) {
          countryData[numCode] = {
            count: 0,
            topics: new Set(),
            name: HOTSPOT_COORDS[numCode]?.name || keyword,
          };
        }
        countryData[numCode].count += topic.message_count || 1;
        countryData[numCode].topics.add(topic.topic);
      }
    }
  }
  return countryData;
}

// ============================================
// ZOOM & PAN HOOK
// ============================================

function useMapTransform(containerRef) {
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const isPanning = useRef(false);
  const panStart = useRef({ x: 0, y: 0 });
  const lastTransform = useRef({ x: 0, y: 0 });

  const MIN_SCALE = 0.8;
  const MAX_SCALE = 6;
  const ZOOM_SENSITIVITY = 0.002;

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();

    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    // Mouse position relative to the container
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    setTransform((prev) => {
      const delta = -e.deltaY * ZOOM_SENSITIVITY;
      const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, prev.scale * (1 + delta)));
      const scaleFactor = newScale / prev.scale;

      // Zoom toward cursor position
      const newX = mouseX - scaleFactor * (mouseX - prev.x);
      const newY = mouseY - scaleFactor * (mouseY - prev.y);

      return { x: newX, y: newY, scale: newScale };
    });
  }, [containerRef]);

  const handleMouseDown = useCallback((e) => {
    // Only pan on middle-click or when map is zoomed in
    if (e.button === 1 || (e.button === 0 && e.target.closest('.map-inner'))) {
      isPanning.current = true;
      panStart.current = { x: e.clientX, y: e.clientY };
      setTransform((prev) => {
        lastTransform.current = { x: prev.x, y: prev.y };
        return prev;
      });
      e.preventDefault();
    }
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (!isPanning.current) return;

    const dx = e.clientX - panStart.current.x;
    const dy = e.clientY - panStart.current.y;

    setTransform((prev) => ({
      ...prev,
      x: lastTransform.current.x + dx,
      y: lastTransform.current.y + dy,
    }));
  }, []);

  const handleMouseUp = useCallback(() => {
    isPanning.current = false;
  }, []);

  const resetZoom = useCallback(() => {
    setTransform({ x: 0, y: 0, scale: 1 });
  }, []);

  // Attach wheel listener with passive: false to allow preventDefault
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
      container.removeEventListener("wheel", handleWheel);
    };
  }, [containerRef, handleWheel]);

  // Attach mouse listeners
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      container.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [containerRef, handleMouseDown, handleMouseMove, handleMouseUp]);

  return { transform, resetZoom };
}


// ============================================
// WORLD MAP COMPONENT
// ============================================

function WorldMap({ topics, onCountryClick }) {
  const [geoData, setGeoData] = useState(null);
  const [tooltip, setTooltip] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const containerRef = useRef(null);
  const wrapperRef = useRef(null);

  const { transform, resetZoom } = useMapTransform(wrapperRef);

  const width = 960;
  const height = 500;

  // Fetch world topology
  useEffect(() => {
    fetch(GEO_URL)
      .then((res) => res.json())
      .then((topology) => {
        const countries = feature(topology, topology.objects.countries);
        setGeoData(countries);
      })
      .catch((err) => console.error("Map load error:", err));
  }, []);

  const countryData = extractCountryData(topics);

  const projection = geoNaturalEarth1()
    .scale(155)
    .center([20, 15])
    .translate([width / 2, height / 2]);

  const pathGenerator = geoPath().projection(projection);

  // Active hotspots
  const activeHotspots = useMemo(() => {
    return Object.entries(countryData)
      .filter(([code]) => HOTSPOT_COORDS[code])
      .map(([code, data]) => {
        const projected = projection(HOTSPOT_COORDS[code].coords);
        const topicArr = Array.from(data.topics);
        return {
          code,
          name: HOTSPOT_COORDS[code].name,
          x: projected?.[0] || 0,
          y: projected?.[1] || 0,
          count: data.count,
          topics: topicArr,
          color: TOPIC_MAP_COLORS[topicArr[0]] || "#a78bfa",
        };
      });
  }, [countryData]);

  function getCountryFill(numericId) {
    const code = String(numericId);
    const data = countryData[code];
    if (!data) return "rgba(148, 163, 184, 0.04)";

    const topicArr = Array.from(data.topics);
    const baseColor = TOPIC_MAP_COLORS[topicArr[0]] || "#a78bfa";
    const intensity = Math.min(0.6, 0.12 + (data.count / 30) * 0.4);

    const r = parseInt(baseColor.slice(1, 3), 16);
    const g = parseInt(baseColor.slice(3, 5), 16);
    const b = parseInt(baseColor.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${intensity})`;
  }

  function handleMouseMove(e) {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  }

  // Tooltip positioning
  const tooltipStyle = tooltip
    ? {
        left: Math.min(
          mousePos.x + 16,
          (containerRef.current?.offsetWidth || 600) - 260
        ),
        top: Math.max(mousePos.y - 20, 10),
      }
    : {};

  const isZoomed = transform.scale > 1.05;

  return (
    <div className="world-map-section" ref={containerRef}>
      <div className="map-header">
        <h2 className="map-title">
          <span className="map-title-dot"></span>
          Global Situation Monitor
        </h2>

        <div className="map-controls">
          {isZoomed && (
            <button className="map-reset-btn" onClick={resetZoom}>
              ↺ Reset
            </button>
          )}
          <span className="map-zoom-level">
            {Math.round(transform.scale * 100)}%
          </span>
          <div className="map-legend">
            {Object.entries(TOPIC_MAP_COLORS)
              .slice(0, 5)
              .map(([topic, color]) => (
                <span key={topic} className="legend-item">
                  <span
                    className="legend-dot"
                    style={{ background: color }}
                  ></span>
                  {topic}
                </span>
              ))}
          </div>
        </div>
      </div>

      <div
        className="map-wrapper"
        ref={wrapperRef}
        onMouseMove={handleMouseMove}
        style={{ cursor: isZoomed ? "grab" : "default" }}
      >
        {!geoData ? (
          <div className="map-loading">Loading map data…</div>
        ) : (
          <div
            className="map-inner"
            style={{
              transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
              transformOrigin: "0 0",
              transition: "none",
              width: "100%",
              height: "100%",
            }}
          >
            <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "100%" }}>
              {/* Dotted graticule background */}
              <defs>
                <pattern
                  id="dotPattern"
                  x="0"
                  y="0"
                  width="12"
                  height="12"
                  patternUnits="userSpaceOnUse"
                >
                  <circle
                    cx="6"
                    cy="6"
                    r="0.5"
                    fill="rgba(148,163,184,0.1)"
                  />
                </pattern>
              </defs>
              <rect width={width} height={height} fill="url(#dotPattern)" />

              {/* Country shapes */}
              <g>
                {geoData.features.map((geo) => {
                  const numId = String(geo.id);
                  const isActive = !!countryData[numId];

                  return (
                    <path
                      key={geo.id}
                      d={pathGenerator(geo) || ""}
                      fill={getCountryFill(geo.id)}
                      stroke="rgba(148, 163, 184, 0.1)"
                      strokeWidth={0.3}
                      className={
                        isActive ? "country-active" : "country-default"
                      }
                      onMouseEnter={() => {
                        if (isActive) {
                          const data = countryData[numId];
                          setTooltip({
                            name: data.name,
                            count: data.count,
                            topics: Array.from(data.topics),
                          });
                        }
                      }}
                      onMouseLeave={() => setTooltip(null)}
                      onClick={() => {
                        if (isActive && onCountryClick) {
                          const data = countryData[numId];
                          const topicArr = Array.from(data.topics);
                          onCountryClick(topicArr[0]);
                        }
                      }}
                    />
                  );
                })}
              </g>

              {/* Hotspot markers */}
              <g>
                {activeHotspots.map((hs) => {
                  const size = Math.min(4 + hs.count / 5, 10);
                  return (
                    <g key={hs.code}>
                      {/* Pulse ring */}
                      <circle
                        cx={hs.x}
                        cy={hs.y}
                        r={size + 4}
                        fill={hs.color}
                        fillOpacity={0.15}
                        className="hotspot-pulse"
                      />
                      {/* Solid dot */}
                      <circle
                        cx={hs.x}
                        cy={hs.y}
                        r={size}
                        fill={hs.color}
                        fillOpacity={0.8}
                      />
                      {/* Inner bright dot */}
                      <circle
                        cx={hs.x}
                        cy={hs.y}
                        r={Math.max(size * 0.4, 2)}
                        fill="white"
                        fillOpacity={0.6}
                      />
                      {/* Count label */}
                      {hs.count > 3 && (
                        <text
                          x={hs.x}
                          y={hs.y - size - 6}
                          className="hotspot-label"
                          fontSize="9"
                          fill="rgba(255,255,255,0.7)"
                        >
                          {hs.count}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </svg>
          </div>
        )}

        {/* Scroll hint */}
        {!isZoomed && (
          <div className="map-scroll-hint">
            Scroll to zoom · Drag to pan
          </div>
        )}

        {/* Tooltip card — follows mouse */}
        {tooltip && (
          <div className="map-tooltip-card" style={tooltipStyle}>
            <div className="tooltip-header">
              <span className="tooltip-country">{tooltip.name}</span>
              <span
                className={`tooltip-status ${
                  tooltip.count > 10 ? "hot" : "active"
                }`}
              >
                {tooltip.count > 10 ? "Hot" : "Active"}
              </span>
            </div>
            <div className="tooltip-stats">
              <div className="tooltip-stat">
                <span className="tooltip-stat-label">Messages</span>
                <span className="tooltip-stat-value">{tooltip.count}</span>
              </div>
              <div className="tooltip-stat">
                <span className="tooltip-stat-label">Topics</span>
                <span className="tooltip-stat-value">
                  {tooltip.topics.length}
                </span>
              </div>
            </div>
            <div className="tooltip-topics">
              {tooltip.topics.map((t) => (
                <span
                  key={t}
                  className="tooltip-topic-tag"
                  style={{
                    borderColor: TOPIC_MAP_COLORS[t] || "#a78bfa",
                    color: TOPIC_MAP_COLORS[t] || "#a78bfa",
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(WorldMap);
