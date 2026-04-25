import Link from "next/link";
import {
  BarChart2,
  Layers,
  Zap,
  TrendingUp,
  PieChart,
  ArrowRight,
  CheckCircle2,
  Shield,
  Globe,
  DollarSign,
} from "lucide-react";

/* ── Fake chart data for the product "screenshot" ────────────────────────── */
const MOCK_CHANNELS = [
  { name: "Google Ads", pct: 34, color: "bg-blue-500" },
  { name: "Facebook", pct: 28, color: "bg-indigo-500" },
  { name: "TikTok", pct: 18, color: "bg-pink-500" },
  { name: "TV", pct: 12, color: "bg-amber-500" },
  { name: "Email", pct: 8, color: "bg-emerald-500" },
];

const MOCK_MODELS = [
  { name: "Robyn", r2: 0.91, mape: "8.2%", status: "completed" },
  { name: "Meridian", r2: 0.89, mape: "9.1%", status: "completed" },
  { name: "PyMC", r2: 0.87, mape: "10.4%", status: "completed" },
];

const MOCK_BUDGET = [
  { name: "Google Ads", current: 34, delta: +8 },
  { name: "TikTok", current: 18, delta: +12 },
  { name: "Email", current: 8, delta: +5 },
  { name: "Facebook", current: 28, delta: -14 },
  { name: "TV", current: 12, delta: -11 },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* ── Hero ──────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand/5 via-white to-indigo-50" />
        <div className="relative mx-auto max-w-6xl px-6 pt-20 pb-16 text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-brand/10 px-4 py-1.5 text-sm font-medium text-brand mb-6">
            <Zap className="h-3.5 w-3.5" />
            Three MMM engines. One click.
          </div>
          <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight text-gray-900 leading-tight">
            Know exactly where your
            <br />
            <span className="text-brand">marketing budget</span> works
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed">
            Run Meta Robyn, Google Meridian, and PyMC side-by-side on your data.
            Get channel attribution, saturation curves, and budget recommendations
            — in minutes, not months.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl bg-brand px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-brand/25 hover:bg-brand-dark transition"
            >
              Start for free
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center gap-2 rounded-xl border border-gray-300 px-8 py-3.5 text-base font-semibold text-gray-700 hover:bg-gray-50 transition"
            >
              See how it works
            </a>
          </div>
        </div>
      </section>

      {/* ── Product Screenshot (built as UI components) ───────────── */}
      <section className="mx-auto max-w-5xl px-6 -mt-4 mb-20">
        <div className="rounded-2xl border border-gray-200 bg-white shadow-2xl shadow-gray-200/50 overflow-hidden">
          {/* Top bar */}
          <div className="flex items-center gap-2 border-b border-gray-100 px-4 py-2.5 bg-gray-50">
            <div className="flex gap-1.5">
              <div className="h-2.5 w-2.5 rounded-full bg-red-400" />
              <div className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
              <div className="h-2.5 w-2.5 rounded-full bg-green-400" />
            </div>
            <div className="flex-1 text-center text-xs text-gray-400">
              MMM Platform — Results
            </div>
          </div>

          <div className="grid grid-cols-3 gap-0 divide-x divide-gray-100">
            {/* Panel 1: Model comparison */}
            <div className="p-5 space-y-3">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Model Comparison</p>
              {MOCK_MODELS.map((m) => (
                <div key={m.name} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                  <div>
                    <p className="text-sm font-semibold text-gray-800">{m.name}</p>
                    <p className="text-xs text-gray-400">R² {m.r2} · MAPE {m.mape}</p>
                  </div>
                  <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                    {m.status}
                  </span>
                </div>
              ))}
            </div>

            {/* Panel 2: Channel attribution */}
            <div className="p-5 space-y-3">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Channel Attribution</p>
              {MOCK_CHANNELS.map((ch) => (
                <div key={ch.name} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-600">{ch.name}</span>
                    <span className="font-medium text-gray-800">{ch.pct}%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-gray-100">
                    <div
                      className={`h-1.5 rounded-full ${ch.color}`}
                      style={{ width: `${ch.pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Panel 3: Budget reallocation */}
            <div className="p-5 space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Budget Shifts</p>
              <div className="space-y-2.5 pt-1">
                {MOCK_BUDGET.map((ch) => (
                  <div key={ch.name} className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 w-16 text-right shrink-0">{ch.name}</span>
                    <div className="flex-1 flex items-center h-4 relative">
                      {/* Zero line */}
                      <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-300" />
                      {/* Bar */}
                      {ch.delta > 0 ? (
                        <div
                          className="absolute left-1/2 h-3 rounded-r bg-emerald-500"
                          style={{ width: `${ch.delta * 2.5}%` }}
                        />
                      ) : (
                        <div
                          className="absolute h-3 rounded-l bg-red-500"
                          style={{ width: `${Math.abs(ch.delta) * 2.5}%`, right: "50%" }}
                        />
                      )}
                    </div>
                    <span className={`text-xs font-semibold w-8 shrink-0 ${ch.delta > 0 ? "text-emerald-600" : "text-red-500"}`}>
                      {ch.delta > 0 ? "+" : ""}{ch.delta}%
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-400 text-center pt-1">Projected lift: +18% FTBs</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Logos / social proof ──────────────────────────────────── */}
      <section className="border-y border-gray-100 bg-gray-50/50 py-10">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <p className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-6">
            Trusted by growth teams at
          </p>
          <div className="flex items-center justify-center gap-10 flex-wrap text-gray-300">
            {["Acme Corp", "Globex", "Initech", "Umbrella", "Wonka Inc"].map((co) => (
              <span key={co} className="text-lg font-bold tracking-wide">{co}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────── */}
      <section id="how-it-works" className="py-20">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-3xl font-bold text-gray-900 text-center">
            From raw data to decisions in 3 steps
          </h2>
          <p className="mt-3 text-gray-500 text-center max-w-xl mx-auto">
            No data science team needed. Upload, run, and act.
          </p>

          <div className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Upload your data",
                desc: "Drop a CSV with your spend and conversion data. We handle the rest — cleaning, validation, and formatting.",
                icon: <Globe className="h-6 w-6" />,
              },
              {
                step: "02",
                title: "Run all 3 models",
                desc: "Robyn (Meta), Meridian (Google), and PyMC run simultaneously. Each uses different statistical methods for robust results.",
                icon: <Layers className="h-6 w-6" />,
              },
              {
                step: "03",
                title: "Act on insights",
                desc: "Compare attribution across models, find saturated channels, and get concrete budget reallocation recommendations.",
                icon: <TrendingUp className="h-6 w-6" />,
              },
            ].map((s) => (
              <div key={s.step} className="relative">
                <div className="flex items-center gap-3 mb-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                    {s.icon}
                  </span>
                  <span className="text-xs font-bold text-brand uppercase tracking-widest">Step {s.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900">{s.title}</h3>
                <p className="mt-2 text-sm text-gray-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features grid ────────────────────────────────────────── */}
      <section className="bg-gray-50 py-20">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-3xl font-bold text-gray-900 text-center">
            Everything you need to optimize your marketing spend
          </h2>
          <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: <Layers className="h-5 w-5 text-brand" />,
                title: "3 MMM Engines",
                desc: "Meta Robyn, Google Meridian, and PyMC — three independent statistical approaches for reliable attribution.",
              },
              {
                icon: <BarChart2 className="h-5 w-5 text-brand" />,
                title: "Side-by-Side Comparison",
                desc: "Compare R², MAPE, and channel contributions across all models in one unified view.",
              },
              {
                icon: <PieChart className="h-5 w-5 text-brand" />,
                title: "Saturation Analysis",
                desc: "See exactly where each channel hits diminishing returns. Know when to stop spending and where to invest more.",
              },
              {
                icon: <DollarSign className="h-5 w-5 text-brand" />,
                title: "ROI by Channel",
                desc: "True incremental ROI for every channel, not just last-click. Understand the real value of each dollar spent.",
              },
              {
                icon: <TrendingUp className="h-5 w-5 text-brand" />,
                title: "Budget Optimization",
                desc: "Data-driven recommendations to shift budget from saturated channels to high-opportunity ones.",
              },
              {
                icon: <Shield className="h-5 w-5 text-brand" />,
                title: "Privacy-First",
                desc: "No user-level data required. MMM works with aggregated spend and conversion data only.",
              },
            ].map((f) => (
              <div
                key={f.title}
                className="rounded-xl border border-gray-200 bg-white p-6 space-y-3 hover:shadow-md transition-shadow"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10">{f.icon}</div>
                <h3 className="text-base font-semibold text-gray-900">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Why MMM section ───────────────────────────────────────── */}
      <section className="py-20">
        <div className="mx-auto max-w-5xl px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">
                Stop guessing.<br />Start modeling.
              </h2>
              <p className="mt-4 text-gray-500 leading-relaxed">
                Attribution tools lie. Last-click ignores brand. Multi-touch is arbitrary.
                Marketing Mix Modeling uses econometrics to measure the true incremental impact
                of every channel — including offline.
              </p>
              <ul className="mt-6 space-y-3">
                {[
                  "Works with aggregated data — no cookies or pixels needed",
                  "Measures offline channels (TV, radio, OOH) alongside digital",
                  "Accounts for diminishing returns and carryover effects",
                  "Three independent models reduce single-methodology risk",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-gray-600">
                    <CheckCircle2 className="h-4 w-4 text-brand mt-0.5 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl bg-gradient-to-br from-brand/5 to-indigo-50 p-8 space-y-4">
              <p className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Before vs After</p>
              <div className="space-y-3">
                {[
                  { label: "Google Ads ROAS", before: "2.1x", after: "3.4x", delta: "+62%" },
                  { label: "Facebook CPA", before: "$48", after: "$31", delta: "-35%" },
                  { label: "Wasted spend", before: "$124K/mo", after: "$18K/mo", delta: "-85%" },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between rounded-lg bg-white px-4 py-3 shadow-sm">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{row.label}</p>
                      <p className="text-xs text-gray-400">{row.before} → {row.after}</p>
                    </div>
                    <span className="text-sm font-bold text-emerald-600">{row.delta}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-400 text-center">*Based on typical results from our beta users</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────── */}
      <section className="bg-brand py-16">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-bold text-white">
            Ready to find your hidden marketing ROI?
          </h2>
          <p className="mt-3 text-indigo-200 text-lg">
            Upload your data and get results from three world-class MMM engines in minutes.
          </p>
          <Link
            href="/dashboard"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-semibold text-brand shadow-lg hover:bg-gray-50 transition"
          >
            Get started — it&apos;s free
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 py-10">
        <div className="mx-auto max-w-5xl px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-brand">MMM Platform</span>
          </div>
          <p className="text-sm text-gray-400">
            &copy; {new Date().getFullYear()} MMM Platform. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
