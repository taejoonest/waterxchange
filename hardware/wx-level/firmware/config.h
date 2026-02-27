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
#define PIN_BATTERY_ADC     4    // voltage divider to LiPo
#define PIN_SOLAR_ADC       5    // voltage divider to solar panel

// ── ADS1115 ─────────────────────────────────────────────────
#define ADS1115_ADDR        0x48
#define ADS_CHANNEL_PRESSURE  0  // 4-20mA across 250Ω → 1-5V

// ── BME280 ──────────────────────────────────────────────────
#define BME280_ADDR         0x76

// ── Pressure Transducer Calibration ─────────────────────────
// 4-20mA across 250Ω = 1.0V–5.0V
// 4mA = 0 PSI, 20mA = 10 PSI
// 1 PSI = 2.31 ft of water head
#define PRESSURE_V_MIN      1.0f
#define PRESSURE_V_MAX      5.0f
#define PRESSURE_PSI_MIN    0.0f
#define PRESSURE_PSI_MAX    10.0f
#define PSI_TO_FT_WATER     2.31f

// ── Timing ──────────────────────────────────────────────────
#define TX_INTERVAL_MS      (15UL * 60UL * 1000UL)  // 15 minutes
#define DEEP_SLEEP_US       (TX_INTERVAL_MS * 1000ULL)

// ── LoRa ────────────────────────────────────────────────────
#define LORA_FREQ           915E6
#define LORA_BANDWIDTH      125E3
#define LORA_SPREAD_FACTOR  7
#define LORA_TX_POWER       17   // dBm

// ── Cellular ────────────────────────────────────────────────
#define APN                 "iot.1nce.net"   // change for your SIM
#define SERVER_HOST         "api.waterxchange.io"
#define SERVER_PORT         443
#define API_ENDPOINT        "/hardware/data"

// ── Device Identity ─────────────────────────────────────────
#define DEVICE_TYPE         "wx-level"
#define DEVICE_ID           "WXL-001"        // unique per unit
#define FIRMWARE_VERSION    "1.0.0"
