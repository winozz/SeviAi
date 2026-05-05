import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { X, BarChart3, MessageSquare, AlertTriangle, ThumbsUp } from "lucide-react";
import { api } from "../lib/api";

interface AdminDashboardProps {
  onClose: () => void;
}

export function AdminDashboard({ onClose }: AdminDashboardProps) {
  const [today, setToday] = useState<any>(null);
  const [feedbackStats, setFeedbackStats] = useState<any>(null);
  const [fallbacks, setFallbacks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [t, f, fb] = await Promise.all([
          api.getTodayStats().catch(() => null),
          api.getFeedbackStats().catch(() => null),
          api.getFallbacks(20).catch(() => null),
        ]);
        if (cancelled) return;
        setToday(t);
        setFeedbackStats(f);
        setFallbacks(Array.isArray(fb) ? fb : fb?.fallbacks ?? []);
      } catch (e: any) {
        if (!cancelled) setError(e?.message ?? "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 bg-white z-20 flex flex-col"
    >
      <div className="bg-gradient-to-r from-green-600 to-green-700 px-6 py-5 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-6 h-6 text-white" />
          <h2 className="text-xl text-white">Sevi Admin Dashboard</h2>
        </div>
        <button
          onClick={onClose}
          className="w-9 h-9 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5 text-white" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {loading && <p className="text-gray-500">Loading stats…</p>}
        {error && (
          <div className="p-4 rounded-xl bg-red-50 text-red-700 text-sm">
            Could not reach API: {error}
          </div>
        )}

        {!loading && (
          <>
            <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard
                icon={MessageSquare}
                label="Messages Today"
                value={today?.total_messages ?? today?.messages ?? "—"}
              />
              <StatCard
                icon={ThumbsUp}
                label="Helpful %"
                value={
                  feedbackStats?.helpful_pct !== undefined
                    ? `${Math.round(feedbackStats.helpful_pct)}%`
                    : "—"
                }
              />
              <StatCard
                icon={BarChart3}
                label="Avg Rating"
                value={
                  feedbackStats?.avg_rating !== undefined
                    ? Number(feedbackStats.avg_rating).toFixed(2)
                    : "—"
                }
              />
            </section>

            {feedbackStats?.low_rated_intents?.length > 0 && (
              <section>
                <h3 className="text-sm text-gray-700 mb-2">Low-Rated Intents</h3>
                <div className="space-y-2">
                  {feedbackStats.low_rated_intents.map((i: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 rounded-xl bg-amber-50 border border-amber-200"
                    >
                      <span className="text-sm text-amber-900">{i.intent}</span>
                      <span className="text-xs text-amber-700">
                        avg {Number(i.avg_rating).toFixed(2)} · {i.count} ratings
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section>
              <h3 className="text-sm text-gray-700 mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Recent Fallbacks (training gaps)
              </h3>
              {fallbacks.length === 0 ? (
                <p className="text-sm text-gray-500">No recent fallbacks.</p>
              ) : (
                <div className="space-y-2">
                  {fallbacks.slice(0, 10).map((f: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-gray-50 border border-gray-200 text-sm text-gray-800"
                    >
                      "{f.message ?? f.user_message ?? f.text ?? JSON.stringify(f)}"
                    </div>
                  ))}
                </div>
              )}
            </section>

            {feedbackStats?.recent_comments?.length > 0 && (
              <section>
                <h3 className="text-sm text-gray-700 mb-2">Recent Comments</h3>
                <div className="space-y-2">
                  {feedbackStats.recent_comments.map((c: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-gray-50 border border-gray-200">
                      <p className="text-sm text-gray-800">"{c.comment}"</p>
                      {c.intent && (
                        <p className="text-xs text-gray-500 mt-1">on {c.intent}</p>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: any;
  label: string;
  value: string | number;
}) {
  return (
    <div className="p-4 rounded-2xl bg-gradient-to-br from-green-50 to-white border border-green-100">
      <div className="flex items-center gap-2 text-green-700 mb-2">
        <Icon className="w-4 h-4" />
        <span className="text-xs">{label}</span>
      </div>
      <p className="text-2xl text-gray-900">{value}</p>
    </div>
  );
}
