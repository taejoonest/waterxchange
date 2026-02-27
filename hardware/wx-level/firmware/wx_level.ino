/*
 * WX-Level — Smart Well Level Meter Firmware
 * ESP32-S3 + ADS1115 + BME280 + SX1276 LoRa + SIM7000G
 *
 * Reads submersible pressure transducer (4-20mA) to compute water level,
 * compensates for barometric pressure via BME280, and transmits readings
 * over LoRa (primary) and LTE Cat-M1 (fallback) to WaterXchange cloud.
 */

#include <Wire.h>
#include <SPI.h>
#include <LoRa.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_BME280.h>
#include <ArduinoJson.h>
#include "config.h"

// ── Globals ─────────────────────────────────────────────────
Adafruit_ADS1115 ads;
Adafruit_BME280  bme;
RTC_DATA_ATTR uint32_t boot_count = 0;
RTC_DATA_ATTR uint32_t tx_fail_count = 0;

struct SensorReading {
    float water_level_ft;
    float pressure_psi;
    float water_temp_c;
    float baro_pressure_hpa;
    float baro_temp_c;
    float humidity_pct;
    float battery_v;
    float solar_v;
};

// ── Forward Declarations ────────────────────────────────────
SensorReading read_sensors();
float         read_pressure_psi();
float         read_battery_voltage();
float         read_solar_voltage();
bool          send_lora(const SensorReading &r);
bool          send_cellular(const SensorReading &r);
String        build_json(const SensorReading &r);
void          enter_deep_sleep();
void          sim_power_on();
void          sim_power_off();

// ── Setup ───────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    boot_count++;

    Wire.begin(PIN_SDA, PIN_SCL);

    // ADS1115 — 16-bit ADC for pressure transducer
    if (!ads.begin(ADS1115_ADDR)) {
        Serial.println("ADS1115 not found");
    }
    ads.setGain(GAIN_ONE); // ±4.096V range → 0.125mV/bit

    // BME280 — barometric pressure for compensation
    if (!bme.begin(BME280_ADDR)) {
        Serial.println("BME280 not found");
    }
    bme.setSampling(
        Adafruit_BME280::MODE_FORCED,
        Adafruit_BME280::SAMPLING_X1,
        Adafruit_BME280::SAMPLING_X1,
        Adafruit_BME280::SAMPLING_X1,
        Adafruit_BME280::FILTER_OFF
    );

    // LoRa — SX1276
    LoRa.setPins(PIN_LORA_CS, PIN_LORA_RST, PIN_LORA_DIO0);
    SPI.begin(PIN_LORA_SCK, PIN_LORA_MISO, PIN_LORA_MOSI, PIN_LORA_CS);
    bool lora_ok = LoRa.begin(LORA_FREQ);
    if (lora_ok) {
        LoRa.setSpreadingFactor(LORA_SPREAD_FACTOR);
        LoRa.setSignalBandwidth(LORA_BANDWIDTH);
        LoRa.setTxPower(LORA_TX_POWER);
    }

    // Read all sensors
    SensorReading reading = read_sensors();

    // Print to serial for debugging
    Serial.printf("Boot #%u | WL: %.2f ft | P: %.3f PSI | Baro: %.1f hPa | "
                  "Batt: %.2fV | Solar: %.2fV\n",
                  boot_count, reading.water_level_ft, reading.pressure_psi,
                  reading.baro_pressure_hpa, reading.battery_v, reading.solar_v);

    // Transmit: try LoRa first, cellular fallback
    bool sent = false;
    if (lora_ok) {
        sent = send_lora(reading);
    }
    if (!sent) {
        sent = send_cellular(reading);
    }

    if (!sent) {
        tx_fail_count++;
        Serial.printf("TX failed (total failures: %u)\n", tx_fail_count);
    } else {
        tx_fail_count = 0;
    }

    enter_deep_sleep();
}

void loop() {
    // Never reached — device sleeps after setup()
}

// ── Sensor Reading ──────────────────────────────────────────
SensorReading read_sensors() {
    SensorReading r;

    // Pressure transducer via ADS1115
    r.pressure_psi = read_pressure_psi();

    // BME280 barometric readings
    bme.takeForcedMeasurement();
    r.baro_pressure_hpa = bme.readPressure() / 100.0f;
    r.baro_temp_c       = bme.readTemperature();
    r.humidity_pct       = bme.readHumidity();
    r.water_temp_c       = r.baro_temp_c; // approximation; actual comes from transducer if available

    // Convert pressure to water level (ft) with barometric compensation
    // Standard atmosphere ≈ 14.696 PSI ≈ 1013.25 hPa
    // Barometric offset in PSI: (actual_hPa - 1013.25) × 0.01450
    float baro_offset_psi = (r.baro_pressure_hpa - 1013.25f) * 0.01450f;
    float corrected_psi   = r.pressure_psi - baro_offset_psi;
    r.water_level_ft      = corrected_psi * PSI_TO_FT_WATER;

    if (r.water_level_ft < 0) r.water_level_ft = 0;

    // Battery and solar voltages
    r.battery_v = read_battery_voltage();
    r.solar_v   = read_solar_voltage();

    return r;
}

float read_pressure_psi() {
    int16_t raw = ads.readADC_SingleEnded(ADS_CHANNEL_PRESSURE);
    float voltage = raw * 0.000125f; // ADS1115 at GAIN_ONE: 0.125mV/bit
    float psi = mapf(voltage, PRESSURE_V_MIN, PRESSURE_V_MAX,
                     PRESSURE_PSI_MIN, PRESSURE_PSI_MAX);
    return constrain(psi, PRESSURE_PSI_MIN, PRESSURE_PSI_MAX);
}

float mapf(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

float read_battery_voltage() {
    // Voltage divider: 100kΩ + 100kΩ → half voltage to ADC
    int raw = analogRead(PIN_BATTERY_ADC);
    return (raw / 4095.0f) * 3.3f * 2.0f;
}

float read_solar_voltage() {
    int raw = analogRead(PIN_SOLAR_ADC);
    return (raw / 4095.0f) * 3.3f * 2.0f;
}

// ── LoRa Transmission ───────────────────────────────────────
bool send_lora(const SensorReading &r) {
    String json = build_json(r);

    LoRa.beginPacket();
    LoRa.print(json);
    bool ok = LoRa.endPacket();

    Serial.printf("LoRa TX: %s → %s\n", json.c_str(), ok ? "OK" : "FAIL");
    return ok;
}

// ── Cellular Transmission ───────────────────────────────────
bool send_cellular(const SensorReading &r) {
    Serial1.begin(115200, SERIAL_8N1, PIN_SIM_RX, PIN_SIM_TX);
    sim_power_on();
    delay(3000);

    // AT init sequence
    Serial1.println("AT");
    delay(500);
    Serial1.println("AT+CNACT=1,\"" APN "\"");
    delay(3000);

    String json = build_json(r);

    // HTTP POST
    Serial1.println("AT+SHCONF=\"URL\",\"https://" SERVER_HOST API_ENDPOINT "\"");
    delay(500);
    Serial1.println("AT+SHCONF=\"BODYLEN\",1024");
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

    // Read response status
    String resp = "";
    unsigned long start = millis();
    while (millis() - start < 5000) {
        if (Serial1.available()) {
            resp += (char)Serial1.read();
        }
    }

    Serial1.println("AT+SHDISC");
    delay(500);
    Serial1.println("AT+CNACT=0");
    sim_power_off();

    bool ok = resp.indexOf("200") >= 0;
    Serial.printf("Cell TX: %s\n", ok ? "OK" : "FAIL");
    return ok;
}

// ── JSON Payload ────────────────────────────────────────────
String build_json(const SensorReading &r) {
    JsonDocument doc;
    doc["device_id"]    = DEVICE_ID;
    doc["device_type"]  = DEVICE_TYPE;
    doc["fw_version"]   = FIRMWARE_VERSION;
    doc["boot_count"]   = boot_count;
    doc["water_level_ft"]      = round2(r.water_level_ft);
    doc["pressure_psi"]        = round3(r.pressure_psi);
    doc["water_temp_c"]        = round1(r.water_temp_c);
    doc["baro_pressure_hpa"]   = round1(r.baro_pressure_hpa);
    doc["baro_temp_c"]         = round1(r.baro_temp_c);
    doc["humidity_pct"]        = round1(r.humidity_pct);
    doc["battery_v"]           = round2(r.battery_v);
    doc["solar_v"]             = round2(r.solar_v);

    String out;
    serializeJson(doc, out);
    return out;
}

float round1(float v) { return ((int)(v * 10 + 0.5f)) / 10.0f; }
float round2(float v) { return ((int)(v * 100 + 0.5f)) / 100.0f; }
float round3(float v) { return ((int)(v * 1000 + 0.5f)) / 1000.0f; }

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
