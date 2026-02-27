#pragma once
#include <Adafruit_ADS1X15.h>
#include "config.h"
#include <math.h>

/*
 * Heat Pulse Flow Measurement
 *
 * Principle: Fire a heater at probe center. 4 thermistors (N/E/S/W) at 15mm
 * radius monitor temperature rise. The downstream thermistor sees the fastest
 * and largest rise. From timing and magnitude we derive:
 *   - Flow direction (which quadrant sees max ΔT first)
 *   - Flow velocity (inversely proportional to peak delay time)
 */

struct FlowResult {
    float velocity_cm_day;
    float direction_deg;       // 0=N, 90=E, 180=S, 270=W
    float peak_temps[4];       // peak ΔT for each thermistor (°C above baseline)
    float peak_times[4];       // time to peak for each thermistor (seconds)
    bool  valid;
};

struct ThermTimeSeries {
    static const int MAX_SAMPLES = 600; // 60s at 100ms intervals
    float temps[4][MAX_SAMPLES];
    int   count;
};

// Convert raw ADC to thermistor temperature using Steinhart-Hart (B-parameter)
float thermistor_temp(Adafruit_ADS1115 &adc, uint8_t channel) {
    int16_t raw = adc.readADC_SingleEnded(channel);
    float voltage = raw * 0.000125f;

    // Voltage divider: V = Vref * R_therm / (R_series + R_therm)
    // where Vref = 3.3V applied to top of divider
    float r_therm = THERM_SERIES_R * voltage / (3.3f - voltage);
    if (r_therm <= 0) return -999.0f;

    // Steinhart-Hart simplified (B-parameter equation)
    float steinhart = r_therm / THERM_NOMINAL_R;
    steinhart = logf(steinhart);
    steinhart /= THERM_B_COEFF;
    steinhart += 1.0f / (THERM_NOMINAL_T + 273.15f);
    float temp_c = (1.0f / steinhart) - 273.15f;

    return temp_c;
}

// Read all 4 thermistors at once
void read_all_thermistors(Adafruit_ADS1115 &adc, float out[4]) {
    out[0] = thermistor_temp(adc, CH_THERM_N);
    out[1] = thermistor_temp(adc, CH_THERM_E);
    out[2] = thermistor_temp(adc, CH_THERM_S);
    out[3] = thermistor_temp(adc, CH_THERM_W);
}

/*
 * Run the full heat pulse measurement cycle:
 * 1. Read baseline temperatures (average of 10 readings)
 * 2. Fire heater for HEATER_POWER_MS
 * 3. Monitor all 4 thermistors for FLOW_MONITOR_MS
 * 4. Find peak ΔT and time-to-peak for each
 * 5. Derive flow direction and velocity
 */
FlowResult run_heat_pulse(Adafruit_ADS1115 &therm_adc) {
    FlowResult result;
    result.valid = false;

    // Step 1: Baseline — average 10 readings per thermistor
    float baseline[4] = {0, 0, 0, 0};
    for (int i = 0; i < 10; i++) {
        float t[4];
        read_all_thermistors(therm_adc, t);
        for (int j = 0; j < 4; j++) baseline[j] += t[j];
        delay(50);
    }
    for (int j = 0; j < 4; j++) baseline[j] /= 10.0f;

    // Step 2: Fire heater
    pinMode(PIN_HEATER, OUTPUT);
    digitalWrite(PIN_HEATER, HIGH);
    delay(HEATER_POWER_MS);
    digitalWrite(PIN_HEATER, LOW);
    delay(HEATER_SETTLE_MS);

    // Step 3: Monitor thermistors for FLOW_MONITOR_MS
    float peak_dt[4] = {0, 0, 0, 0};
    float peak_time[4] = {0, 0, 0, 0};

    unsigned long start_ms = millis();
    while (millis() - start_ms < FLOW_MONITOR_MS) {
        float t[4];
        read_all_thermistors(therm_adc, t);

        float elapsed_s = (millis() - start_ms) / 1000.0f;
        for (int j = 0; j < 4; j++) {
            float dt = t[j] - baseline[j];
            if (dt > peak_dt[j]) {
                peak_dt[j] = dt;
                peak_time[j] = elapsed_s;
            }
        }
        delay(FLOW_SAMPLE_MS);
    }

    // Step 4: Find the dominant thermistor (highest peak ΔT)
    int max_idx = 0;
    for (int j = 1; j < 4; j++) {
        if (peak_dt[j] > peak_dt[max_idx]) max_idx = j;
    }

    // Minimum ΔT threshold to consider valid flow
    if (peak_dt[max_idx] < 0.05f) {
        // No measurable flow — essentially stagnant
        result.velocity_cm_day = 0;
        result.direction_deg = -1;
        result.valid = true;
        for (int j = 0; j < 4; j++) {
            result.peak_temps[j] = peak_dt[j];
            result.peak_times[j] = peak_time[j];
        }
        return result;
    }

    // Step 5a: Flow direction from dominant thermistor
    // Refine using weighted average of adjacent thermistors
    const float dirs[4] = {0.0f, 90.0f, 180.0f, 270.0f}; // N, E, S, W
    float sin_sum = 0, cos_sum = 0;
    for (int j = 0; j < 4; j++) {
        float rad = dirs[j] * M_PI / 180.0f;
        float weight = peak_dt[j];
        sin_sum += weight * sinf(rad);
        cos_sum += weight * cosf(rad);
    }
    float direction = atan2f(sin_sum, cos_sum) * 180.0f / M_PI;
    if (direction < 0) direction += 360.0f;

    // Step 5b: Flow velocity from peak delay time
    // v = K / t_peak  (empirical relationship from calibration)
    float velocity = 0;
    if (peak_time[max_idx] > 0.5f) {
        velocity = FLOW_CAL_K / peak_time[max_idx];
    } else {
        velocity = FLOW_CAL_K / 0.5f; // cap at very fast flow
    }

    result.velocity_cm_day = velocity;
    result.direction_deg   = direction;
    result.valid           = true;
    for (int j = 0; j < 4; j++) {
        result.peak_temps[j] = peak_dt[j];
        result.peak_times[j] = peak_time[j];
    }
    return result;
}
