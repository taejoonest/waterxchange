#pragma once

// ── Pin Assignments ─────────────────────────────────────────
#define PIN_SDA             8
#define PIN_SCL             9
#define PIN_LORA_CS         10
#define PIN_LORA_RST        11
#define PIN_LORA_DIO0       12
#define PIN_LORA_MOSI       35
#define PIN_LORA_MISO       37
#define PIN_LORA_SCK        36
#define PIN_SIM_TX          17
#define PIN_SIM_RX          18
#define PIN_SIM_PWR         21
#define PIN_HEATER          38   // MOSFET gate for nichrome heater
#define PIN_BATTERY_ADC     4
#define PIN_SOLAR_ADC       5

// ── ADS1115 Addresses ───────────────────────────────────────
// Two ADS1115 on I2C: ADDR pin tied differently
#define ADS_ADDR_SENSORS    0x48  // pressure, conductivity, PT1000
#define ADS_ADDR_THERM      0x49  // 4 thermistors (N, E, S, W)

// ADS #1 channels
#define CH_PRESSURE         0     // 4-20mA across 250Ω
#define CH_CONDUCTIVITY     1     // EC circuit analog output
#define CH_PT1000           2     // RTD via Wheatstone bridge

// ADS #2 channels — thermistors in voltage divider with 10kΩ ref
#define CH_THERM_N          0
#define CH_THERM_E          1
#define CH_THERM_S          2
#define CH_THERM_W          3

// ── Pressure Transducer ─────────────────────────────────────
#define PRESSURE_V_MIN      1.0f
#define PRESSURE_V_MAX      5.0f
#define PRESSURE_PSI_MIN    0.0f
#define PRESSURE_PSI_MAX    10.0f
#define PSI_TO_FT_WATER     2.31f

// ── Thermistor Parameters (NTC 10kΩ B=3950) ────────────────
#define THERM_NOMINAL_R     10000.0f
#define THERM_NOMINAL_T     25.0f     // °C
#define THERM_B_COEFF       3950.0f
#define THERM_SERIES_R      10000.0f  // series resistor in divider

// ── Heat Pulse Parameters ───────────────────────────────────
#define HEATER_POWER_MS     4000     // heat pulse duration (4 seconds)
#define HEATER_SETTLE_MS    500      // wait after power-off before sampling
#define FLOW_SAMPLE_MS      100      // sample interval during monitoring
#define FLOW_MONITOR_MS     60000    // total monitoring window (60 seconds)
#define THERM_DISTANCE_MM   15.0f    // thermistors are 15mm from heater center

// Flow velocity calibration: delay_seconds → cm/day
// Derived from lab calibration with known flow velocities
// v = K / delay_peak  where K is empirical constant
#define FLOW_CAL_K          900.0f   // calibrate in lab; cm·s/day

// ── Timing ──────────────────────────────────────────────────
#define TX_INTERVAL_MS      (15UL * 60UL * 1000UL)
#define DEEP_SLEEP_US       (TX_INTERVAL_MS * 1000ULL)

// ── LoRa ────────────────────────────────────────────────────
#define LORA_FREQ           915E6
#define LORA_BANDWIDTH      125E3
#define LORA_SPREAD_FACTOR  7
#define LORA_TX_POWER       17

// ── Cellular ────────────────────────────────────────────────
#define APN                 "iot.1nce.net"
#define SERVER_HOST         "api.waterxchange.io"
#define SERVER_PORT         443
#define API_ENDPOINT        "/hardware/data"

// ── Device ──────────────────────────────────────────────────
#define DEVICE_TYPE         "wx-flow"
#define DEVICE_ID           "WXF-001"
#define FIRMWARE_VERSION    "1.0.0"
