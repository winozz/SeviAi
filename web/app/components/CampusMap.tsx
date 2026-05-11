import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { MapPin, Navigation } from "lucide-react";
import { api, type MapPlace } from "../lib/api";

export interface MapData {
  place_id: string;
  label: string;
}

interface CampusMapProps {
  data: MapData;
}

type BuildingShape = {
  x: number;
  y: number;
  w: number;
  h: number;
  short: string;
  full: string;
  direction: string;
  walkMinutes: number;
};

type LayoutData = {
  gate: { x: number; y: number };
  viewbox: { width: number; height: number };
  buildings: Record<string, BuildingShape>;
};

const DEFAULT_GATE = { x: 300, y: 505 };
const DEFAULT_VIEWBOX = { width: 600, height: 540 };

const DEFAULT_BUILDINGS: Record<string, BuildingShape> = {
  admin:   { x: 240, y: 425, w: 120, h: 40, walkMinutes: 1, short: "Admin",   full: "Administration Building",                direction: "Straight ahead, ~30 m past the main gate." },
  grad:    { x: 380, y: 425, w: 80,  h: 40, walkMinutes: 2, short: "Grad",    full: "Graduate School",                        direction: "Past the main gate, turn right at the Admin Building." },
  library: { x: 255, y: 345, w: 130, h: 55, walkMinutes: 2, short: "Library", full: "Ladislao Diwa Memorial Library",         direction: "Follow the main road past Admin; the library is on your left." },
  canteen: { x: 410, y: 345, w: 80,  h: 45, walkMinutes: 3, short: "Canteen", full: "University Canteen",                     direction: "Past Admin, turn right at the library junction." },
  chapel:  { x: 510, y: 350, w: 70,  h: 45, walkMinutes: 4, short: "Chapel",  full: "University Chapel",                      direction: "Past Admin, turn right and continue east past the canteen." },
  cas:     { x: 110, y: 345, w: 110, h: 55, walkMinutes: 3, short: "CAS",     full: "College of Arts & Sciences",             direction: "Past Admin, turn left at the library junction." },
  gym:     { x: 60,  y: 250, w: 110, h: 60, walkMinutes: 4, short: "Gym",     full: "University Gymnasium",                   direction: "Follow the main road, then turn left after the library." },
  ceit:    { x: 440, y: 250, w: 120, h: 65, walkMinutes: 4, short: "CEIT",    full: "College of Engineering & Information Technology", direction: "Follow the main road past Admin and Library, then turn right." },
  cemds:   { x: 240, y: 250, w: 130, h: 55, walkMinutes: 4, short: "CEMDS",   full: "College of Economics, Management & Development Studies", direction: "Continue straight on the main road past the library." },
  coed:    { x: 60,  y: 155, w: 110, h: 60, walkMinutes: 5, short: "CEd",     full: "College of Education",                   direction: "Follow the main road north past CEMDS, then turn left." },
  cvmbs:   { x: 240, y: 155, w: 140, h: 60, walkMinutes: 5, short: "CVMBS",   full: "College of Veterinary Medicine & Biomedical Sciences", direction: "Continue straight on the main road past CEMDS." },
  cfot:    { x: 440, y: 155, w: 130, h: 60, walkMinutes: 5, short: "CFOT",    full: "College of Fisheries & Ocean Technology", direction: "Follow the main road north past CEMDS, then turn right." },
  cafenr:  { x: 140, y: 65,  w: 320, h: 55, walkMinutes: 6, short: "CAFENR",  full: "College of Agriculture, Food, Environment & Natural Resources", direction: "Continue straight to the far north end of campus." },
};

const DEFAULT_LAYOUT: LayoutData = {
  gate: DEFAULT_GATE,
  viewbox: DEFAULT_VIEWBOX,
  buildings: DEFAULT_BUILDINGS,
};

// Module-level cache: fetch the canonical layout from /map on first render,
// then reuse for every subsequent CampusMap instance. Falls back to defaults
// on network error so the UI keeps working offline.
let cachedLayout: LayoutData | null = null;
let inflight: Promise<LayoutData> | null = null;

function placeToBuilding(p: MapPlace): BuildingShape | null {
  if (p.x === null || p.y === null || p.w === null || p.h === null) return null;
  return {
    x: p.x, y: p.y, w: p.w, h: p.h,
    short: p.short,
    full: p.full,
    direction: p.direction_from_gate,
    walkMinutes: p.walk_minutes_from_gate,
  };
}

function loadLayout(): Promise<LayoutData> {
  if (cachedLayout) return Promise.resolve(cachedLayout);
  if (inflight) return inflight;
  inflight = api
    .getCampusMap()
    .then((payload) => {
      const buildings: Record<string, BuildingShape> = {};
      for (const place of payload.places) {
        const b = placeToBuilding(place);
        if (b) buildings[place.place_id] = b;
      }
      const layout: LayoutData = {
        gate: payload.gate,
        viewbox: payload.viewbox,
        buildings,
      };
      cachedLayout = layout;
      return layout;
    })
    .catch(() => {
      cachedLayout = DEFAULT_LAYOUT;
      return DEFAULT_LAYOUT;
    });
  return inflight;
}

function buildPath(gate: { x: number; y: number }, b: BuildingShape): string {
  const targetCX = b.x + b.w / 2;
  const targetCY = b.y + b.h / 2;
  const stopY = Math.max(targetCY, 130);
  return `M ${gate.x} ${gate.y} L ${gate.x} ${stopY} L ${targetCX} ${stopY} L ${targetCX} ${targetCY}`;
}

export function CampusMap({ data }: CampusMapProps) {
  const [layout, setLayout] = useState<LayoutData>(cachedLayout ?? DEFAULT_LAYOUT);

  useEffect(() => {
    if (!cachedLayout) {
      loadLayout().then(setLayout);
    }
  }, []);

  const { gate, viewbox, buildings } = layout;
  const highlightId = data.place_id in buildings ? data.place_id : null;
  const showFullCampus = data.place_id === "main" || highlightId === null;
  const target = highlightId ? buildings[highlightId] : null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35 }}
      className="mt-2 w-full rounded-xl border border-green-200 bg-white overflow-hidden shadow-sm"
    >
      <div className="px-3 py-2 bg-green-50 border-b border-green-200 flex items-center gap-2">
        <MapPin className="w-4 h-4 text-green-700" />
        <span className="text-xs font-medium text-green-900">
          {showFullCampus ? "CvSU Main Campus – Indang" : data.label}
        </span>
      </div>

      <div className="bg-[#eef7ec]">
        <svg
          viewBox={`0 0 ${viewbox.width} ${viewbox.height}`}
          xmlns="http://www.w3.org/2000/svg"
          role="img"
          aria-label={`Campus map highlighting ${data.label}`}
          className="w-full h-auto block"
        >
          <rect x="0" y="0" width={viewbox.width} height={viewbox.height} fill="#eef7ec" />

          <g stroke="#cfe3c9" strokeWidth="1" fill="none" opacity="0.7">
            {Array.from({ length: Math.ceil(viewbox.width / 60) + 1 }).map((_, i) => (
              <line key={`v${i}`} x1={i * 60} y1="0" x2={i * 60} y2={viewbox.height} />
            ))}
            {Array.from({ length: Math.ceil(viewbox.height / 60) + 1 }).map((_, i) => (
              <line key={`h${i}`} x1="0" y1={i * 60} x2={viewbox.width} y2={i * 60} />
            ))}
          </g>

          <g fill="#d8d2c0">
            <rect x={gate.x - 18} y="130" width="36" height={gate.y - 130 + 5} />
            <rect x="60"  y={332} width={viewbox.width - 120} height="22" />
            <rect x="60"  y={242} width={viewbox.width - 120} height="22" />
            <rect x="60"  y={147} width={viewbox.width - 120} height="22" />
            <rect x="60"  y={417} width={viewbox.width - 120} height="22" />
          </g>
          <g stroke="#fff8d6" strokeWidth="1.2" strokeDasharray="6 6" fill="none">
            <line x1={gate.x} y1="135" x2={gate.x} y2={gate.y} />
          </g>

          <text x="20" y="20" fontSize="10" fill="#5c7a55" fontFamily="system-ui, sans-serif">N ▲</text>

          {Object.entries(buildings).map(([id, b]) => {
            const isTarget = id === highlightId;
            const fill = isTarget ? "#16a34a" : "#ffffff";
            const stroke = isTarget ? "#14532d" : "#9ca3af";
            const text = isTarget ? "#ffffff" : "#1f2937";
            return (
              <g key={id}>
                <rect
                  x={b.x}
                  y={b.y}
                  width={b.w}
                  height={b.h}
                  rx="6"
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={isTarget ? 2.5 : 1.2}
                />
                <text
                  x={b.x + b.w / 2}
                  y={b.y + b.h / 2 + 4}
                  textAnchor="middle"
                  fontSize={isTarget ? 13 : 11}
                  fontWeight={isTarget ? 700 : 500}
                  fill={text}
                  fontFamily="system-ui, sans-serif"
                >
                  {b.short}
                </text>
                {isTarget && (
                  <motion.circle
                    cx={b.x + b.w / 2}
                    cy={b.y + b.h / 2}
                    r="6"
                    fill="none"
                    stroke="#16a34a"
                    strokeWidth="2"
                    initial={{ r: 6, opacity: 0.9 }}
                    animate={{ r: 28, opacity: 0 }}
                    transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut" }}
                  />
                )}
              </g>
            );
          })}

          <g>
            <rect x={gate.x - 35} y={gate.y - 5} width="70" height="22" rx="4" fill="#0f766e" />
            <text
              x={gate.x}
              y={gate.y + 10}
              textAnchor="middle"
              fontSize="11"
              fontWeight="600"
              fill="#ffffff"
              fontFamily="system-ui, sans-serif"
            >
              Main Gate
            </text>
          </g>

          {target && (
            <>
              <motion.path
                d={buildPath(gate, target)}
                fill="none"
                stroke="#dc2626"
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray="8 8"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1.2, ease: "easeInOut" }}
              />
              <motion.circle
                r="5"
                fill="#dc2626"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.1, duration: 0.3 }}
              >
                <animateMotion dur="3s" repeatCount="indefinite" path={buildPath(gate, target)} />
              </motion.circle>
            </>
          )}
        </svg>
      </div>

      {target && (
        <div className="px-3 py-2.5 border-t border-green-200 bg-white text-xs text-gray-700 flex items-start gap-2">
          <Navigation className="w-3.5 h-3.5 text-green-700 mt-0.5 flex-shrink-0" />
          <div>
            <div className="font-medium text-gray-900">
              {target.full} · ~{target.walkMinutes} min walk from Main Gate
            </div>
            <div className="text-gray-600 mt-0.5">{target.direction}</div>
          </div>
        </div>
      )}

      {showFullCampus && (
        <div className="px-3 py-2.5 border-t border-green-200 bg-white text-xs text-gray-700 flex items-start gap-2">
          <Navigation className="w-3.5 h-3.5 text-green-700 mt-0.5 flex-shrink-0" />
          <div>
            <div className="font-medium text-gray-900">CvSU Main Campus – Indang, Cavite</div>
            <div className="text-gray-600 mt-0.5">
              Enter via the Main Gate. The main road runs north through Admin, Library, CEMDS, and ends at CAFENR.
              Ask about a specific college (e.g. &ldquo;Where is CEIT?&rdquo;) for walking directions.
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
