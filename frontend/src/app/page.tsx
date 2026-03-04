"use client";

import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import FadeIn from "@/components/FadeIn";

/* ─── Data ─── */

const partnerLogos = [
  "Kern County GSA", "Tulare Lake GSA", "USBR", "DWR",
  "Rosedale-RB WSD", "Mojave Water Agency", "Sustainable Groundwater",
  "Friant Water Authority", "Central Valley", "SGMA", "Water Board", "CalEPA",
];

const comparisonData = [
  { label: "Compliance check time", traditional: "2–4 weeks", waterx: "Under 2 minutes", pct: 15 },
  { label: "Regulatory research", traditional: "10+ hours per trade", waterx: "Instant RAG lookup", pct: 8 },
  { label: "Transfer routing", traditional: "Manual pathway selection", waterx: "Auto-routed", pct: 5 },
];

const demoStages = [
  { name: "Intake Validation", score: 95, finding: "PASS" },
  { name: "Allocation Check", score: 88, finding: "PASS" },
  { name: "GSP Compliance", score: 82, finding: "PASS" },
  { name: "Well Impact (Theis)", score: 71, finding: "CONDITIONAL" },
  { name: "Basin Health", score: 90, finding: "PASS" },
  { name: "Cross-GSA Check", score: 85, finding: "PASS" },
];

const features = [
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
    title: "Live Order Book",
    desc: "Real-time bids and asks across Central Valley basins with quantity in acre-feet and price per AF.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
      </svg>
    ),
    title: "AI Compliance Engine",
    desc: "12-point SGMA evaluation powered by knowledge graph traversal and LLM reasoning with GSP citations.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
      </svg>
    ),
    title: "Smart Matching",
    desc: "Multi-objective optimization balances economic surplus against environmental risk across every trade.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
      </svg>
    ),
    title: "Interactive Basin Map",
    desc: "90,566 wells, hydrology contours, flow direction, subsidence zones, and water quality alerts on one map.",
  },
];

const personas = [
  { title: "For Farmers", desc: "Trade water allocations with full SGMA compliance built in.", icon: "🌾" },
  { title: "For Water Districts", desc: "Manage basin-wide transfers with real-time monitoring.", icon: "🏛" },
  { title: "For GSAs", desc: "Enforce sustainability goals with automated compliance checks.", icon: "📋" },
  { title: "For Researchers", desc: "Open-source hardware and data for aquifer studies.", icon: "🔬" },
  { title: "For Consultants", desc: "Run transfer analyses across 10 regulatory pathways.", icon: "💼" },
  { title: "For Regulators", desc: "Full audit trails and GSP-referenced compliance reports.", icon: "⚖️" },
];

/* ─── Components ─── */

function ComparisonBar({ label, traditional, waterx, pct, delay }: {
  label: string; traditional: string; waterx: string; pct: number; delay: number;
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <div ref={ref} className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
      <p className="mb-4 text-sm font-semibold text-gray-800">{label}</p>
      <div className="space-y-3">
        <div>
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="text-gray-400">Traditional</span>
            <span className="font-semibold text-gray-500">{traditional}</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-100">
            <motion.div
              initial={{ width: 0 }}
              animate={inView ? { width: "100%" } : {}}
              transition={{ duration: 1, delay }}
              className="bar-traditional h-full rounded-full"
            />
          </div>
        </div>
        <div>
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="text-gray-400">WaterXchange</span>
            <span className="font-semibold text-teal">{waterx}</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-100">
            <motion.div
              initial={{ width: 0 }}
              animate={inView ? { width: `${pct}%` } : {}}
              transition={{ duration: 0.8, delay: delay + 0.3 }}
              className="bar-waterx h-full rounded-full"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Page ─── */

export default function Home() {
  return (
    <>
      {/* ═══ HERO — dark section ═══ */}
      <section className="relative flex min-h-[100vh] items-center justify-center overflow-hidden bg-gradient-to-br from-navy via-[#0f2b5e] to-navy-light">
        <div className="hero-grid absolute inset-0" />
        <div className="absolute inset-0">
          <div className="absolute left-[10%] top-[60%] h-[50%] w-[70%] rounded-full bg-teal/[0.07] blur-[120px]" />
          <div className="absolute right-[10%] top-[10%] h-[40%] w-[50%] rounded-full bg-blue/[0.05] blur-[100px]" />
        </div>

        <div className="relative z-10 mx-auto max-w-4xl px-6 pt-24 pb-20 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-6 inline-flex items-center gap-2.5 rounded-full border border-teal/30 bg-teal/10 px-5 py-2 text-sm font-medium text-teal"
          >
            <span className="animate-pulse-dot h-2 w-2 rounded-full bg-green" />
            SGMA-Compliant Platform
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-5xl font-extrabold leading-[1.08] tracking-tight text-white sm:text-6xl lg:text-7xl"
          >
            The <span className="gradient-text">first AI</span> for<br />
            California water trading
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-gray-400"
          >
            From compliance checks to final settlement, we handle it all so you don&apos;t have to.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            className="mt-10 flex flex-wrap justify-center gap-4"
          >
            <Link
              href="#features"
              className="rounded-xl bg-white px-8 py-3.5 text-sm font-semibold text-navy shadow-lg transition-all hover:-translate-y-0.5 hover:shadow-xl"
            >
              See How It Works
            </Link>
            <Link
              href="/hardware"
              className="rounded-xl border border-white/25 px-8 py-3.5 text-sm font-semibold text-white transition-all hover:border-white/50 hover:bg-white/5"
            >
              View Hardware
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ═══ MARQUEE — logo ticker ═══ */}
      <section className="overflow-hidden border-b border-gray-100 bg-gray-50/50 py-6">
        <div className="animate-marquee flex w-max items-center gap-12">
          {[...partnerLogos, ...partnerLogos].map((name, i) => (
            <span
              key={`${name}-${i}`}
              className="whitespace-nowrap text-sm font-semibold text-gray-300 transition-colors hover:text-gray-500"
            >
              {name}
            </span>
          ))}
        </div>
      </section>

      {/* ═══ VALUE PROP — "Stop wasting weeks" ═══ */}
      <section className="bg-white py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto max-w-3xl text-center">
            <FadeIn>
              <h2 className="text-4xl font-extrabold leading-tight tracking-tight text-navy sm:text-5xl">
                Stop wasting weeks<br />on compliance paperwork
              </h2>
            </FadeIn>
            <FadeIn delay={0.1}>
              <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-gray-500">
                Water transfers take weeks of regulatory research, manual compliance checks, and spreadsheets. WaterXchange makes it effortless — from first order to verified settlement.
              </p>
            </FadeIn>
            <FadeIn delay={0.2}>
              <div className="mt-8 flex flex-wrap justify-center gap-4">
                <Link
                  href="#demo"
                  className="rounded-xl bg-navy px-7 py-3 text-sm font-semibold text-white transition-all hover:bg-navy-light hover:shadow-lg"
                >
                  See a Demo
                </Link>
                <Link
                  href="/transfer"
                  className="rounded-xl border border-gray-200 px-7 py-3 text-sm font-semibold text-gray-700 transition-all hover:border-gray-300 hover:bg-gray-50"
                >
                  Run a Transfer
                </Link>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ═══ COMPARISON BARS ═══ */}
      <section className="bg-gray-50 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <FadeIn>
            <p className="text-center text-xs font-bold uppercase tracking-[0.15em] text-teal">
              Why choose WaterXchange?
            </p>
            <h2 className="mt-3 text-center text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
              Traditional process vs. WaterXchange
            </h2>
          </FadeIn>

          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {comparisonData.map((item, i) => (
              <FadeIn key={item.label} delay={i * 0.1}>
                <ComparisonBar {...item} delay={i * 0.15} />
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ INTERACTIVE DEMO MOCKUP ═══ */}
      <section id="demo" className="bg-white py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid items-center gap-16 lg:grid-cols-2">
            <FadeIn direction="left">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal">
                  AI Compliance Pipeline
                </p>
                <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
                  12-point compliance check in under 2 minutes
                </h2>
                <p className="mt-4 max-w-md text-base leading-relaxed text-gray-500">
                  Every trade is automatically routed through the correct regulatory pathway and evaluated against real GSP data, knowledge graph traversal, and LLM reasoning — with page-level citations.
                </p>
                <div className="mt-8 flex gap-3">
                  <Link
                    href="/transfer-tool"
                    className="rounded-xl bg-navy px-6 py-3 text-sm font-semibold text-white transition-all hover:bg-navy-light"
                  >
                    Try It Live
                  </Link>
                </div>
              </div>
            </FadeIn>

            <FadeIn direction="right" delay={0.15}>
              <div className="rounded-2xl border border-gray-200 bg-white p-1 shadow-xl shadow-gray-200/50">
                {/* Mockup window chrome */}
                <div className="flex items-center gap-2 border-b border-gray-100 px-4 py-3">
                  <div className="h-3 w-3 rounded-full bg-red/60" />
                  <div className="h-3 w-3 rounded-full bg-amber/60" />
                  <div className="h-3 w-3 rounded-full bg-green/60" />
                  <span className="ml-3 text-xs text-gray-400">WaterXchange Compliance Pipeline</span>
                </div>
                {/* Mockup content */}
                <div className="p-5">
                  {/* Decision banner */}
                  <div className="mb-4 flex items-center gap-3 rounded-xl bg-green/5 border border-green/20 px-4 py-3">
                    <span className="rounded-md bg-green px-2.5 py-1 text-xs font-bold text-white">APPROVED</span>
                    <span className="text-lg font-extrabold text-navy">85.2%</span>
                    <span className="text-xs text-gray-500">via SGMA Standard pathway</span>
                  </div>
                  {/* Stage cards */}
                  <div className="space-y-2.5">
                    {demoStages.map((stage) => (
                      <div key={stage.name} className="flex items-center gap-3 rounded-lg bg-gray-50 px-4 py-2.5">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-gray-700">{stage.name}</span>
                            <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                              stage.finding === "PASS"
                                ? "bg-green/10 text-green"
                                : "bg-amber/10 text-amber"
                            }`}>
                              {stage.finding}
                            </span>
                          </div>
                          <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
                            <motion.div
                              initial={{ width: 0 }}
                              whileInView={{ width: `${stage.score}%` }}
                              viewport={{ once: true }}
                              transition={{ duration: 0.8, delay: 0.3 }}
                              className={`h-full rounded-full ${
                                stage.finding === "PASS" ? "bg-green" : "bg-amber"
                              }`}
                            />
                          </div>
                        </div>
                        <span className="text-xs font-bold text-gray-400">{stage.score}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ═══ SECOND DEMO — Order Book Mockup ═══ */}
      <section className="bg-gray-50 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid items-center gap-16 lg:grid-cols-2">
            <FadeIn direction="left" delay={0.1}>
              <div className="rounded-2xl border border-gray-200 bg-white p-1 shadow-xl shadow-gray-200/50 order-2 lg:order-1">
                <div className="flex items-center gap-2 border-b border-gray-100 px-4 py-3">
                  <div className="h-3 w-3 rounded-full bg-red/60" />
                  <div className="h-3 w-3 rounded-full bg-amber/60" />
                  <div className="h-3 w-3 rounded-full bg-green/60" />
                  <span className="ml-3 text-xs text-gray-400">Live Order Book — Kern County</span>
                </div>
                <div className="p-5">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm font-bold text-navy">Water Market</span>
                    <span className="rounded-full bg-green/10 px-3 py-1 text-xs font-semibold text-green">Live</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="mb-2 text-xs font-bold text-green">BIDS (Buy)</p>
                      {[
                        { price: "$485", qty: "120 AF" },
                        { price: "$480", qty: "85 AF" },
                        { price: "$475", qty: "200 AF" },
                        { price: "$470", qty: "50 AF" },
                      ].map((bid) => (
                        <div key={bid.price} className="flex justify-between border-b border-gray-50 py-1.5 text-xs">
                          <span className="font-semibold text-green">{bid.price}</span>
                          <span className="text-gray-500">{bid.qty}</span>
                        </div>
                      ))}
                    </div>
                    <div>
                      <p className="mb-2 text-xs font-bold text-red">ASKS (Sell)</p>
                      {[
                        { price: "$490", qty: "75 AF" },
                        { price: "$495", qty: "150 AF" },
                        { price: "$500", qty: "300 AF" },
                        { price: "$510", qty: "90 AF" },
                      ].map((ask) => (
                        <div key={ask.price} className="flex justify-between border-b border-gray-50 py-1.5 text-xs">
                          <span className="font-semibold text-red">{ask.price}</span>
                          <span className="text-gray-500">{ask.qty}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="mt-4 rounded-lg bg-navy/5 px-3 py-2 text-center">
                    <span className="text-xs text-gray-500">Best Bid/Ask Spread: </span>
                    <span className="text-sm font-bold text-navy">$485 / $490</span>
                    <span className="ml-2 text-xs text-gray-400">($5 spread)</span>
                  </div>
                </div>
              </div>
            </FadeIn>

            <FadeIn direction="right" className="order-1 lg:order-2">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal">
                  Real-Time Market
                </p>
                <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
                  Don&apos;t spend weeks negotiating trades
                </h2>
                <p className="mt-4 max-w-md text-base leading-relaxed text-gray-500">
                  View live bids and asks across Central Valley basins. The matching engine uses price-time priority with multi-objective optimization for economic and environmental outcomes.
                </p>
                <Link
                  href="/transfer-tool"
                  className="mt-8 inline-flex rounded-xl bg-navy px-6 py-3 text-sm font-semibold text-white transition-all hover:bg-navy-light"
                >
                  Place an Order
                </Link>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ═══ TESTIMONIAL ═══ */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-4xl px-6">
          <FadeIn>
            <blockquote className="rounded-3xl border border-gray-100 bg-gray-50/50 p-10 text-center shadow-sm">
              <p className="text-xl font-medium leading-relaxed text-gray-700 sm:text-2xl">
                &ldquo;WaterXchange&apos;s compliance engine evaluated our 500 AF inter-basin transfer in under 90 seconds — with citations to the actual GSP pages. What used to take our team two weeks of research now happens automatically.&rdquo;
              </p>
              <div className="mt-6">
                <p className="font-bold text-navy">Water District Manager</p>
                <p className="text-sm text-gray-400">Kern County, CA</p>
              </div>
            </blockquote>
          </FadeIn>
        </div>
      </section>

      {/* ═══ FEATURES — clean grid ═══ */}
      <section id="features" className="bg-gray-50 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <FadeIn>
            <p className="text-center text-xs font-bold uppercase tracking-[0.15em] text-teal">Platform</p>
            <h2 className="mt-3 text-center text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
              One platform replaces your entire workflow
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-center text-base leading-relaxed text-gray-500">
              More than just a marketplace — WaterXchange manages the full transfer lifecycle from order to compliance-verified settlement.
            </p>
          </FadeIn>

          <div className="mt-14 grid gap-5 sm:grid-cols-2">
            {features.map((f, i) => (
              <FadeIn key={f.title} delay={i * 0.08}>
                <div className="group rounded-2xl border border-gray-100 bg-white p-7 shadow-sm transition-all hover:-translate-y-1 hover:border-teal/30 hover:shadow-lg hover:shadow-teal/5">
                  <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-teal/10 text-teal">
                    {f.icon}
                  </div>
                  <h3 className="text-lg font-bold text-navy">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-gray-500">{f.desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ WHO WE'RE BUILT FOR ═══ */}
      <section className="bg-white py-24">
        <div className="mx-auto max-w-6xl px-6">
          <FadeIn>
            <h2 className="text-center text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
              Who we&apos;re built for
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-center text-base leading-relaxed text-gray-500">
              Whether you&apos;re managing a single well or an entire basin, WaterXchange adapts to your needs.
            </p>
          </FadeIn>

          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {personas.map((p, i) => (
              <FadeIn key={p.title} delay={i * 0.06}>
                <div className="group rounded-2xl border border-gray-100 bg-white p-6 transition-all hover:-translate-y-1 hover:border-teal/30 hover:shadow-lg hover:shadow-teal/5">
                  <div className="mb-3 text-2xl">{p.icon}</div>
                  <h3 className="text-base font-bold text-navy">{p.title}</h3>
                  <p className="mt-1.5 text-sm text-gray-500">{p.desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CTA — dark section ═══ */}
      <section className="bg-navy py-24">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <FadeIn>
            <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Ready to streamline your water trades?
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-base leading-relaxed text-gray-400">
              Get started with WaterXchange today and see the difference AI-powered compliance can make.
            </p>
            <div className="mt-10 flex flex-wrap justify-center gap-4">
              <a
                href="mailto:contact@waterxchange.io"
                className="rounded-xl bg-white px-8 py-3.5 text-sm font-semibold text-navy shadow-lg transition-all hover:-translate-y-0.5 hover:shadow-xl"
              >
                Get Started
              </a>
              <Link
                href="/transfer"
                className="rounded-xl border border-white/25 px-8 py-3.5 text-sm font-semibold text-white transition-all hover:border-white/50 hover:bg-white/5"
              >
                Run a Transfer
              </Link>
            </div>
          </FadeIn>
        </div>
      </section>
    </>
  );
}
