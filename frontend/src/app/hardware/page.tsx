"use client";

import Image from "next/image";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import FadeIn from "@/components/FadeIn";

const tabs = [
  { id: "level", label: "WX-Level" },
  { id: "flow", label: "WX-Flow" },
  { id: "compare", label: "Compare" },
];

const levelSpecs = [
  { label: "Measurement", value: "Water Level", note: "Pressure-based, 0–100 ft range" },
  { label: "Accuracy", value: "±0.1 ft", note: "0.1% FS, temperature compensated" },
  { label: "Connectivity", value: "LoRa + Cellular", note: "SX1276 915MHz + SIM7000G" },
  { label: "Power", value: "Solar + LiPo", note: "6W panel, 6000mAh battery" },
  { label: "Battery Life", value: "Indefinite", note: "30+ days without sun" },
  { label: "Enclosure", value: "IP67", note: "3D-printed PETG + gasket" },
  { label: "MCU", value: "ESP32-S3", note: "Deep sleep: 10 µA" },
  { label: "Target BOM", value: "~$85", note: "At qty 100" },
];

const flowSpecs = [
  { label: "Flow Velocity", value: "0.5–200 cm/day", note: "Heat pulse + 4-thermistor array" },
  { label: "Flow Direction", value: "360° ± 10°", note: "4 thermistors at 90° spacing" },
  { label: "Conductivity", value: "0–100,000 µS/cm", note: "4-electrode platinum cell" },
  { label: "Temperature", value: "±0.1°C", note: "PT1000 RTD" },
  { label: "Water Level", value: "0–100 ft", note: "Integrated pressure sensor" },
  { label: "Probe Diameter", value: "45 mm", note: 'Fits 2" well casing' },
  { label: "Connectivity", value: "LoRa + Cellular", note: "Shared controller platform" },
  { label: "Target BOM", value: "~$140", note: "At qty 100" },
];

const compareRows = [
  { feature: "Primary measurement", level: "Groundwater level", flow: "Flow velocity + direction" },
  { feature: "Water level", level: "Yes (pressure-based)", flow: "Yes (integrated)" },
  { feature: "Flow velocity", level: "—", flow: "0.5–200 cm/day" },
  { feature: "Flow direction", level: "—", flow: "360° ± 10°" },
  { feature: "Conductivity / TDS", level: "—", flow: "0–100,000 µS/cm" },
  { feature: "Temperature", level: "Via transducer", flow: "PT1000 RTD ± 0.1°C" },
  { feature: "Barometric comp.", level: "BME280 onboard", flow: "—" },
  { feature: "MCU", level: "ESP32-S3", flow: "ESP32-S3" },
  { feature: "Connectivity", level: "LoRa + Cellular", flow: "LoRa + Cellular" },
  { feature: "Power", level: "Solar + 6000mAh LiPo", flow: "Solar + 6000mAh LiPo" },
  { feature: "Enclosure", level: "IP67 PETG box", flow: "IP67 box + sealed probe" },
  { feature: "Probe", level: "Pressure transducer", flow: "45mm multi-sensor" },
  { feature: "Target BOM", level: "~$85", flow: "~$140" },
  { feature: "Best for", level: "Well level monitoring", flow: "Aquifer studies" },
];

function SpecCard({ label, value, note, index }: { label: string; value: string; note: string; index: number }) {
  return (
    <FadeIn delay={index * 0.05}>
      <motion.div
        whileHover={{ y: -3 }}
        className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm transition-all hover:border-teal/30 hover:shadow-lg hover:shadow-teal/5"
      >
        <p className="text-[0.65rem] font-bold uppercase tracking-wider text-gray-400">{label}</p>
        <p className="mt-1 text-xl font-extrabold text-navy">{value}</p>
        <p className="mt-1 text-xs text-gray-400">{note}</p>
      </motion.div>
    </FadeIn>
  );
}

export default function HardwarePage() {
  const [active, setActive] = useState("level");

  return (
    <>
      {/* ═══ HERO — dark ═══ */}
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
            Open-Source Hardware
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl"
          >
            Hardware <span className="gradient-text">Products</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-gray-400"
          >
            Open-source IoT sensors for groundwater monitoring. Solar-powered, LoRa/cellular connected, built for the field.
          </motion.p>
        </div>
      </section>

      {/* ═══ TABS — sticky ═══ */}
      <section className="sticky top-[72px] z-30 border-b border-gray-100 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl gap-1 px-6 py-3">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActive(tab.id)}
              className={`relative rounded-xl px-6 py-2.5 text-sm font-bold transition-all ${
                active === tab.id
                  ? "text-teal"
                  : "text-gray-400 hover:text-gray-600"
              }`}
            >
              {active === tab.id && (
                <motion.div
                  layoutId="hw-tab"
                  className="absolute inset-0 rounded-xl border border-teal/20 bg-teal/5"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <span className="relative z-10">{tab.label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* ═══ CONTENT ═══ */}
      <div className="bg-gray-50/50 py-16">
        <div className="mx-auto max-w-6xl px-6">
          <AnimatePresence mode="wait">
            {active === "level" && (
              <motion.div key="level" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.25 }}>
                <ProductSection
                  badge="Smart Well Level Meter"
                  title="WX-Level"
                  subtitle="Continuous groundwater level monitoring"
                  description="Submersible pressure transducer paired with a solar-powered ESP32 controller. Mounts on any monitoring or irrigation well and transmits water level, temperature, and battery status every 15 minutes via LoRa or cellular."
                  productImage="/wx_level_product.png"
                  productAlt="WX-Level — Smart Well Level Meter"
                  specs={levelSpecs}
                  internalLabel="Inside the Controller"
                  internalTitle="What's inside"
                  internalDescription="ESP32-S3 microcontroller, ADS1115 16-bit ADC, BME280 barometric sensor, LoRa and cellular modules, CN3791 solar MPPT charger, and a 6000mAh LiPo battery — all on a compact 80×50mm PCB."
                  internalImage="/wx_level_internal.png"
                  internalAlt="WX-Level internal view"
                />
              </motion.div>
            )}

            {active === "flow" && (
              <motion.div key="flow" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.25 }}>
                <ProductSection
                  badge="Aquifer Flow + Quality Probe"
                  title="WX-Flow"
                  subtitle="Groundwater flow velocity, direction, and water quality"
                  description='Combined flow velocity/direction and water quality probe using heat pulse technology. A 4-thermistor array measures Darcy velocity and flow direction, while integrated conductivity and temperature sensors monitor water quality. Fits inside a standard 2" monitoring well.'
                  productImage="/wx_flow_product.png"
                  productAlt="WX-Flow — Aquifer Flow + Quality Probe"
                  specs={flowSpecs}
                  internalLabel="Inside the System"
                  internalTitle="Controller + submersible probe"
                  internalDescription="The surface controller shares the WX-Level platform with added MOSFET heater driver. The submersible probe houses a nichrome heater, 4 NTC thermistors, platinum conductivity electrodes, a PT1000 RTD, and a pressure transducer — all sealed with epoxy potting."
                  internalImage="/wx_flow_internal.png"
                  internalAlt="WX-Flow internal view"
                />
                <FadeIn delay={0.2}>
                  <div className="mt-10 rounded-2xl border border-teal/15 bg-teal/[0.03] p-6">
                    <p className="text-sm leading-relaxed text-gray-600">
                      <span className="font-bold text-teal">How it works: </span>
                      A 2W nichrome heater creates a brief heat pulse in the groundwater. Four thermistors at 90° intervals detect which direction the heat travels and how fast — giving you both flow direction (360°) and Darcy velocity. Measurements are taken every 15 minutes with minimal power draw.
                    </p>
                  </div>
                </FadeIn>
              </motion.div>
            )}

            {active === "compare" && (
              <motion.div key="compare" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.25 }}>
                <FadeIn>
                  <h2 className="mb-8 text-center text-2xl font-extrabold text-navy">
                    Product Comparison
                  </h2>
                </FadeIn>
                <FadeIn delay={0.1}>
                  <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-navy">
                          <th className="px-5 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-300">Feature</th>
                          <th className="px-5 py-4 text-center text-xs font-bold uppercase tracking-wider text-teal">WX-Level</th>
                          <th className="px-5 py-4 text-center text-xs font-bold uppercase tracking-wider text-teal">WX-Flow</th>
                        </tr>
                      </thead>
                      <tbody>
                        {compareRows.map((row, i) => (
                          <tr key={row.feature} className={`border-t border-gray-50 transition-colors hover:bg-gray-50/80 ${i % 2 === 0 ? "bg-gray-50/30" : ""}`}>
                            <td className="px-5 py-3 font-medium text-gray-700">{row.feature}</td>
                            <td className="px-5 py-3 text-center text-gray-500">{row.level}</td>
                            <td className="px-5 py-3 text-center text-gray-500">{row.flow}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </FadeIn>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  );
}

/* ─── Product Section ─── */

function ProductSection({
  badge, title, subtitle, description, productImage, productAlt,
  specs, internalLabel, internalTitle, internalDescription, internalImage, internalAlt,
}: {
  badge: string; title: string; subtitle: string; description: string;
  productImage: string; productAlt: string;
  specs: { label: string; value: string; note: string }[];
  internalLabel: string; internalTitle: string; internalDescription: string;
  internalImage: string; internalAlt: string;
}) {
  return (
    <>
      {/* Hero row */}
      <div className="grid items-center gap-12 lg:grid-cols-2">
        <FadeIn direction="left">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal">{badge}</p>
            <h2 className="mt-2 text-4xl font-extrabold tracking-tight text-navy">{title}</h2>
            <p className="mt-2 text-lg font-semibold text-teal/80">{subtitle}</p>
            <p className="mt-4 text-base leading-relaxed text-gray-500">{description}</p>
          </div>
        </FadeIn>
        <FadeIn direction="right" delay={0.15}>
          <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg shadow-gray-200/50">
            <Image src={productImage} alt={productAlt} width={600} height={400} className="h-auto w-full" priority />
          </div>
        </FadeIn>
      </div>

      {/* Specs */}
      <div className="mt-16">
        <FadeIn>
          <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal">Key Specifications</p>
        </FadeIn>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {specs.map((s, i) => (
            <SpecCard key={s.label + s.value} {...s} index={i} />
          ))}
        </div>
      </div>

      {/* Internal view */}
      <div className="mt-20 border-t border-gray-200 pt-16">
        <FadeIn>
          <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal">{internalLabel}</p>
          <h3 className="mt-2 text-2xl font-extrabold text-navy">{internalTitle}</h3>
          <p className="mt-3 max-w-2xl text-base leading-relaxed text-gray-500">{internalDescription}</p>
        </FadeIn>
        <FadeIn delay={0.15}>
          <div className="mt-8 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg shadow-gray-200/50">
            <Image src={internalImage} alt={internalAlt} width={900} height={500} className="h-auto w-full" />
          </div>
        </FadeIn>
      </div>
    </>
  );
}
