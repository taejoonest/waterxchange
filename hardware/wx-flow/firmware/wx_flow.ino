/*
 * WX-Flow — Aquifer Flow + Quality Probe Firmware
 * ESP32-S3 + 2× ADS1115 + SX1276 LoRa + SIM7000G
 *
 * Measures:
 *   - Groundwater flow velocity & direction (heat pulse method)
 *   - Conductivity / TDS
 *   - Temperature (PT1000 RTD)
 *   - Water level (submersible pressure transducer)
 * Transmits via LoRa (primary) + LTE Cat-M1 (fallback).
 */

#include <Wire.h>
#include <SPI.h>
#include <LoRa.h>
#include <Adafruit_ADS1X15.h>
#include <ArduinoJson.h>
#include "config.h"
#include "heat_pulse.h"

// ── Globals ─────────────────────────────────────────────────
Adafruit_ADS1115 ads_sensors;  // pressure, conductivity, PT1000
Adafruit_ADS1115 ads_therm;    // 4 thermistors

RTC_DATA_ATTR uint32_t boot_count = 0;
RTC_DATA_ATTR uint32_t tx_fail_count = 0;

struct FullReading {
    FlowResult flow;
    float conductivity_us;
    float tds_ppm;
    float water_temp_c;
    float water_level_ft;
    float pressure_psi;
    float battery_v;
    float solar_v;
};

// ── Forward Declarations ────────────────────────────────────
FullReading read_all();
float       read_pressure_psi();
float       read_conductivity();
float       read_pt1000_temp();
float       read_battery_voltage();
float       read_solar_voltage();
float       mapf(float x, float in_min, float in_max, float out_min, float out_max);
bool        send_lora(const FullReading &r);
bool        send_cellular(const FullReading &r);
String      build_json(const FullReading &r);
void        enter_deep_sleep();
void        sim_power_on();
void        sim_power_off();

// ── Setup ───────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    boot_count++;

    Wire.begin(PIN_SDA, PIN_SCL);

    // ADS1115 #1 — sensor channels
    if (!ads_sensors.begin(ADS_ADDR_SENSORS)) {
        Serial.println("ADS #1 (sensors) not found");
    }
    ads_sensors.setGain(GAIN_ONE);

    // ADS1115 #2 — thermistor channels
    if (!ads_therm.begin(ADS_ADDR_THERM)) {
        Serial.println("ADS #2 (thermistors) not found");
    }
    ads_therm.setGain(GAIN_ONE);

    // LoRa
    LoRa.setPins(PIN_LORA_CS, PIN_LORA_RST, PIN_LORA_DIO0);
    SPI.begin(PIN_LORA_SCK, PIN_LORA_MISO, PIN_LORA_MOSI, PIN_LORA_CS);
    bool lora_ok = LoRa.begin(LORA_FREQ);
    if (lora_ok) {
        LoRa.setSpreadingFactor(LORA_SPREAD_FACTOR);
        LoRa.setSignalBandwidth(LORA_BANDWIDTH);
        LoRa.setTxPower(LORA_TX_POWER);
    }

    // Read everything (including ~65s heat pulse cycle)
    FullReading reading = read_all();

    Serial.printf("Boot #%u | Flow: %.1f cm/day @ %.0f° | EC: %.0f µS/cm | "
                  "T: %.1f°C | WL: %.2f ft | Batt: %.2fV\n",
                  boot_count, reading.flow.velocity_cm_day,
                  reading.flow.direction_deg, reading.conductivity_us,
                  reading.water_temp_c, reading.water_level_ft,
                  reading.battery_v);

    // Transmit
    bool sent = false;
    if (lora_ok) sent = send_lora(reading);
    if (!sent) sent = send_cellular(reading);

    if (!sent) tx_fail_count++;
    else tx_fail_count = 0;

    enter_deep_sleep();
}

void loop() {}

// ── Full Reading ────────────────────────────────────────────
FullReading read_all() {
    FullReading r;

    // Heat pulse flow measurement (~65 seconds)
    Serial.println("Starting heat pulse measurement...");
    r.flow = run_heat_pulse(ads_therm);
    Serial.printf("Flow: %.1f cm/day, direction: %.0f°, valid: %d\n",
                  r.flow.velocity_cm_day, r.flow.direction_deg, r.flow.valid);

    // Pressure → water level
    r.pressure_psi  = read_pressure_psi();
    r.water_level_ft = r.pressure_psi * PSI_TO_FT_WATER;
    if (r.water_level_ft < 0) r.water_level_ft = 0;

    // Conductivity
    r.conductivity_us = read_conductivity();
    r.tds_ppm = r.conductivity_us * 0.55f;  // approximate conversion factor

    // Temperature
    r.water_temp_c = read_pt1000_temp();

    // Power
    r.battery_v = read_battery_voltage();
    r.solar_v   = read_solar_voltage();

    return r;
}

// ── Individual Sensor Reads ─────────────────────────────────
float read_pressure_psi() {
    int16_t raw = ads_sensors.readADC_SingleEnded(CH_PRESSURE);
    float voltage = raw * 0.000125f;
    float psi = mapf(voltage, PRESSURE_V_MIN, PRESSURE_V_MAX,
                     PRESSURE_PSI_MIN, PRESSURE_PSI_MAX);
    return constrain(psi, PRESSURE_PSI_MIN, PRESSURE_PSI_MAX);
}

float read_conductivity() {
    // Atlas EZO-EC or DFRobot outputs 0–3.0V proportional to conductivity
    // 0V = 0 µS/cm, 3.0V = 100,000 µS/cm (adjustable via calibration)
    int16_t raw = ads_sensors.readADC_SingleEnded(CH_CONDUCTIVITY);
    float voltage = raw * 0.000125f;
    return mapf(voltage, 0.0f, 3.0f, 0.0f, 100000.0f);
}

float read_pt1000_temp() {
    // PT1000 in Wheatstone bridge with 1kΩ references
    // Output voltage is proportional to resistance deviation
    // PT1000: R = 1000 × (1 + 0.00385 × T)
    // Bridge output ΔV → ΔR → T
    int16_t raw = ads_sensors.readADC_SingleEnded(CH_PT1000);
    float voltage = raw * 0.000125f;

    // Approximate: bridge excitation 3.3V, all arms 1kΩ at 0°C
    // ΔV ≈ Vexc/4 × ΔR/R0 → ΔR = ΔV × 4 × R0 / Vexc
    float delta_r = voltage * 4.0f * 1000.0f / 3.3f;
    float resistance = 1000.0f + delta_r;
    float temp_c = (resistance / 1000.0f - 1.0f) / 0.00385f;

    return temp_c;
}

float read_battery_voltage() {
    int raw = analogRead(PIN_BATTERY_ADC);
    return (raw / 4095.0f) * 3.3f * 2.0f;
}

float read_solar_voltage() {
    int raw = analogRead(PIN_SOLAR_ADC);
    return (raw / 4095.0f) * 3.3f * 2.0f;
}

float mapf(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// ── LoRa ────────────────────────────────────────────────────
bool send_lora(const FullReading &r) {
    String json = build_json(r);
    LoRa.beginPacket();
    LoRa.print(json);
    bool ok = LoRa.endPacket();
    Serial.printf("LoRa TX: %s\n", ok ? "OK" : "FAIL");
    return ok;
}

// ── Cellular ────────────────────────────────────────────────
bool send_cellular(const FullReading &r) {
    Serial1.begin(115200, SERIAL_8N1, PIN_SIM_RX, PIN_SIM_TX);
    sim_power_on();
    delay(3000);

    Serial1.println("AT");
    delay(500);
    Serial1.println("AT+CNACT=1,\"" APN "\"");
    delay(3000);

    String json = build_json(r);

    Serial1.println("AT+SHCONF=\"URL\",\"https://" SERVER_HOST API_ENDPOINT "\"");
    delay(500);
    Serial1.println("AT+SHCONF=\"BODYLEN\",2048");
    delay(500);
    Serial1.println("AT+SHCONF=\"HEADERLEN\",350");
    delay(500);
    Serial1.println("AT+SHCONN");
    delay(3000);
    Serial1.println("AT+SHCHEAD");
    delay(200);
    Serial1.println("AT+SHAHEAD=\"Content-Type\",\"application/json\"");
    delay(200);
    Serial1.printf("AT+SHBOD=%d,10000\r\n", json.length());
    delay(200);
    Serial1.print(json);
    delay(1000);
    Serial1.println("AT+SHREQ=\"" API_ENDPOINT "\",3");
    delay(5000);

    String resp = "";
    unsigned long start = millis();
    while (millis() - start < 5000) {
        if (Serial1.available()) resp += (char)Serial1.read();
    }

    Serial1.println("AT+SHDISC");
    delay(500);
    Serial1.println("AT+CNACT=0");
    sim_power_off();

    bool ok = resp.indexOf("200") >= 0;
    Serial.printf("Cell TX: %s\n", ok ? "OK" : "FAIL");
    return ok;
}

// ── JSON ────────────────────────────────────────────────────
String build_json(const FullReading &r) {
    JsonDocument doc;

    doc["device_id"]   = DEVICE_ID;
    doc["device_type"] = DEVICE_TYPE;
    doc["fw_version"]  = FIRMWARE_VERSION;
    doc["boot_count"]  = boot_count;

    // Flow data
    JsonObject flow = doc["flow"].to<JsonObject>();
    flow["velocity_cm_day"] = roundf(r.flow.velocity_cm_day * 10) / 10.0f;
    flow["direction_deg"]   = roundf(r.flow.direction_deg);
    flow["valid"]           = r.flow.valid;
    JsonArray peaks = flow["peak_temps"].to<JsonArray>();
    JsonArray times = flow["peak_times"].to<JsonArray>();
    for (int i = 0; i < 4; i++) {
        peaks.add(roundf(r.flow.peak_temps[i] * 100) / 100.0f);
        times.add(roundf(r.flow.peak_times[i] * 10) / 10.0f);
    }

    // Water quality
    doc["conductivity_us"] = roundf(r.conductivity_us);
    doc["tds_ppm"]         = roundf(r.tds_ppm);
    doc["water_temp_c"]    = roundf(r.water_temp_c * 10) / 10.0f;

    // Water level
    doc["water_level_ft"]  = roundf(r.water_level_ft * 100) / 100.0f;
    doc["pressure_psi"]    = roundf(r.pressure_psi * 1000) / 1000.0f;

    // Power
    doc["battery_v"] = roundf(r.battery_v * 100) / 100.0f;
    doc["solar_v"]   = roundf(r.solar_v * 100) / 100.0f;

    String out;
    serializeJson(doc, out);
    return out;
}

// ── Power Management ────────────────────────────────────────
void enter_deep_sleep() {
    LoRa.sleep();
    Serial.printf("Sleeping for %lu ms\n", TX_INTERVAL_MS);
    Serial.flush();
    esp_sleep_enable_timer_wakeup(DEEP_SLEEP_US);
    esp_deep_sleep_start();
}

void sim_power_on() {
    pinMode(PIN_SIM_PWR, OUTPUT);
    digitalWrite(PIN_SIM_PWR, HIGH);
    delay(1000);
    digitalWrite(PIN_SIM_PWR, LOW);
}

void sim_power_off() {
    Serial1.println("AT+CPOWD=1");
    delay(2000);
}
