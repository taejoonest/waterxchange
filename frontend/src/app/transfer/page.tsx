"use client";

import { motion } from "framer-motion";
import FadeIn from "@/components/FadeIn";

const pathways = [
  { name: "SGMA Standard", type: "GW", stages: 6, desc: "GSA approval and GSP consistency per CWC §10726.4" },
  { name: "Adjudicated Basin", type: "GW", stages: 5, desc: "Watermaster approval for court-adjudicated basins" },
  { name: "Banked Water", type: "GW", stages: 4, desc: "Withdrawal from previously stored groundwater" },
  { name: "In-Lieu Transfer", type: "GW", stages: 6, desc: "Seller reduces pumping, frees surface water" },
  { name: "Protected Export", type: "GW", stages: 7, desc: "Export from critically overdrafted basin" },
  { name: "Pre-1914 Right", type: "SW", stages: 5, desc: "Pre-1914 appropriative — no SWRCB approval needed" },
  { name: "CVP / SWP Contract", type: "SW", stages: 4, desc: "Federal/state contract water transfer" },
  { name: "Post-1914 Temporary", type: "SW", stages: 5, desc: "SWRCB temporary change petition, ≤1 year" },
  { name: "Post-1914 Long-Term", type: "SW", stages: 5, desc: "Full SWRCB long-term change petition" },
  { name: "Imported Water", type: "SW", stages: 4, desc: "Fewest restrictions — free transfer per CWC §1011" },
];

const stageNames = [
  "Intake Validation",
  "Rights Verification",
  "Compliance Analysis",
  "Impact Assessment",
  "Weighted Decision",
];

export default function TransferPage() {
  return (
    <>
      {/* Hero — dark */}
      <section className="relative overflow-hidden bg-gradient-to-br from-navy via-[#0f2b5e] to-navy-light pb-6 pt-28">
        <div className="hero-grid absolute inset-0" />
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent" />
        <div className="relative z-10 mx-auto max-w-4xl px-6 py-16 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mb-4 inline-flex items-center gap-2 rounded-full border border-teal/30 bg-teal/10 px-4 py-1.5 text-sm font-medium text-teal"
          >
            <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-green" />
            Auto-Routed Compliance
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl"
          >
            Water Transfer <span className="gradient-text">Pipeline</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-gray-400"
          >
            10 regulatory pathways with auto-routed compliance analysis for California groundwater and surface water transfers.
          </motion.p>
        </div>
      </section>

      {/* Pipeline stages */}
      <section className="border-b border-gray-100 bg-white py-16">
        <div className="mx-auto max-w-6xl px-6">
          <FadeIn>
            <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal">Pipeline Stages</p>
            <h2 className="mt-3 text-2xl font-extrabold text-navy">
              Every transfer follows a multi-stage compliance pipeline
            </h2>
          </FadeIn>
          <FadeIn delay={0.15}>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              {stageNames.map((stage, i) => (
                <div key={stage} className="flex items-center gap-3">
                  <div className={`rounded-xl border px-5 py-3 text-center text-sm font-semibold shadow-sm ${
                    i === stageNames.length - 1
                      ? "border-green/30 bg-green/5 text-green"
                      : "border-teal/20 bg-teal/5 text-teal"
                  }`}>
                    <span className="mb-1 block text-[0.6rem] font-bold text-gray-400">STAGE {i + 1}</span>
                    {stage}
                  </div>
                  {i < stageNames.length - 1 && (
                    <span className="text-lg text-gray-300">→</span>
                  )}
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Pathways grid */}
      <section className="bg-gray-50/50 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <FadeIn>
            <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal">10 Pathways</p>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
              Regulatory Pathways
            </h2>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-gray-500">
              Each transfer type follows a different compliance pipeline based on California water law. The auto-router detects the correct pathway.
            </p>
          </FadeIn>

          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {pathways.map((pw, i) => (
              <FadeIn key={pw.name} delay={i * 0.06}>
                <div className="group rounded-2xl border border-gray-100 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:border-teal/30 hover:shadow-lg hover:shadow-teal/5">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-base font-bold text-navy">{pw.name}</h3>
                    <span className={`rounded-md px-2 py-0.5 text-[0.6rem] font-bold ${
                      pw.type === "GW"
                        ? "bg-blue/10 text-blue"
                        : "bg-purple/10 text-purple"
                    }`}>
                      {pw.type}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed text-gray-500">{pw.desc}</p>
                  <p className="mt-3 text-xs font-semibold text-gray-400">{pw.stages} compliance stages</p>
                </div>
              </FadeIn>
            ))}
          </div>

          <FadeIn delay={0.3}>
            <div className="mt-12 text-center">
              <a
                href="/transfer-tool"
                className="inline-flex items-center gap-2 rounded-xl bg-navy px-8 py-4 text-sm font-semibold text-white transition-all hover:bg-navy-light hover:shadow-lg"
              >
                Run a Transfer
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 8h10M9 4l4 4-4 4" />
                </svg>
              </a>
              <p className="mt-3 text-xs text-gray-400">
                Opens the full transfer form with demo scenarios and live API compliance analysis
              </p>
            </div>
          </FadeIn>
        </div>
      </section>
    </>
  );
}
