"use client";

import { motion } from "framer-motion";
import FadeIn from "@/components/FadeIn";

const layers = [
  { icon: "💧", title: "90,566 Wells", desc: "Irrigation, domestic, monitoring, public supply, and industrial wells across 7 counties" },
  { icon: "🌊", title: "Groundwater Contours", desc: "DWR ArcGIS tile layers for seasonal elevation and level-change contours" },
  { icon: "🗺", title: "C2VSim Watersheds", desc: "Fine-grid watershed boundaries from DWR's C2VSim model" },
  { icon: "➡", title: "Flow Direction", desc: "Computed flow arrows showing groundwater movement from Sierra foothills to valley trough" },
  { icon: "📍", title: "Monitoring Stations", desc: "Active measurement stations with count and basin data" },
  { icon: "⚠", title: "Risk Zones", desc: "Land subsidence zones (critical/high/moderate) and water quality alert areas" },
];

const stats = [
  { value: "90,566", label: "Total Wells" },
  { value: "7", label: "Counties" },
  { value: "Real-time", label: "Subsidence Data" },
  { value: "4", label: "Risk Categories" },
];

export default function MonitoringPage() {
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
            Live Dashboard
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl"
          >
            Groundwater <span className="gradient-text">Monitoring</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-gray-400"
          >
            Central Valley groundwater data — wells, hydrology contours, flow direction, subsidence, and water quality.
          </motion.p>
        </div>
      </section>

      {/* Stats */}
      <section className="border-b border-gray-100 bg-white py-10">
        <div className="mx-auto grid max-w-5xl grid-cols-2 gap-6 px-6 md:grid-cols-4">
          {stats.map((stat, i) => (
            <FadeIn key={stat.label} delay={i * 0.1}>
              <div className="text-center">
                <div className="text-3xl font-extrabold tracking-tight text-navy">{stat.value}</div>
                <div className="mt-1 text-sm text-gray-400">{stat.label}</div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* Layer cards */}
      <section className="bg-gray-50/50 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <FadeIn>
            <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal">Map Layers</p>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-navy sm:text-4xl">
              Interactive Groundwater Map
            </h2>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-gray-500">
              Toggle between well types, hydrology layers, and risk zones to explore basin conditions in real time.
            </p>
          </FadeIn>

          <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {layers.map((layer, i) => (
              <FadeIn key={layer.title} delay={i * 0.08}>
                <div className="group rounded-2xl border border-gray-100 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:border-teal/30 hover:shadow-lg hover:shadow-teal/5">
                  <div className="mb-3 text-2xl">{layer.icon}</div>
                  <h3 className="text-lg font-bold text-navy">{layer.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-gray-500">{layer.desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>

          <FadeIn delay={0.3}>
            <div className="mt-12 text-center">
              <a
                href="/monitor-dashboard"
                className="inline-flex items-center gap-2 rounded-xl bg-navy px-8 py-4 text-sm font-semibold text-white transition-all hover:bg-navy-light hover:shadow-lg"
              >
                Launch Interactive Map
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 8h10M9 4l4 4-4 4" />
                </svg>
              </a>
              <p className="mt-3 text-xs text-gray-400">
                Opens the full Mapbox-powered dashboard with all well and hydrology data
              </p>
            </div>
          </FadeIn>
        </div>
      </section>
    </>
  );
}
