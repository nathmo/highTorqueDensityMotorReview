# Maxon Robotics Joint Actuators — HEJ & HPJ-DT

Research date: 2026-07-23. Manufacturer site treated as authoritative.

## Sources (all maxon)
- **HEJ overview / datasheet links:** https://global.maxongroup.com/high-efficiency-joints
- **HEJ 50-48-30 datasheet** rev1.1, P/N 922156 — `datasheets/maxon/Datasheet_HEJ_50_48_30_rev1.1.pdf`
- **HEJ 70-48-60 datasheet** rev1.2, P/N 933846/933847 — `datasheets/maxon/Datasheet_HEJ_70_48_60_rev1.2.pdf`
- **HEJ 90-48-140 datasheet** rev2.3, P/N 831220/895330 — `datasheets/maxon/Datasheet_HEJ_90_48_140_rev2.3.pdf`
- **Robotics Drives — Products & Services flyer rev1.6 (Sept 2025)** — HPJ-DT joint table + EC frameless DT motor table — `datasheets/maxon/maxon_robotics_flyer_rev1.6.pdf`
  (https://www.maxongroup.com/assets/public/caas/v1/media/271238/data/5fd47e48fa580fb8bf564b71097107dc/whitepaper-flyer-robotics-products-and-services-en.pdf)
- **EC frameless DT brochure (Jul 2025)** — motor performance table — `datasheets/maxon/Brochure-EC-frameless-DT-06-25-EN.pdf`

## Summary

**HEJ (High Efficiency Joint)** — quasi-direct-drive, fully integrated (controller + motor + planetary gear + sensing), EtherCAT, impedance controller, cross-roller output bearing, 14/12-bit absolute output encoder. Full datasheets published for HEJ 50 / 70 / 90. **HEJ Hercules** is still in development (only comparison-table figures).

Key HEJ torque wording (raw): each datasheet gives a **Nominal joint torque** (continuous, indefinite) and a **Maximum joint torque, actively controlled & repetitive** (applied ~1–2 s, or ~4–5 s on the 90) — this is the repetitive-peak figure. Separately, a **high-cycle-fatigue / impact ladder** gives structural overtorque survival (12e6 / 100e3 / 1e3 impacts). Note the model-number torque (…-30 / …-60 / …-140) is *not* identical to the repetitive-peak: HEJ 50 is named "-30" (the 100e3-impact value) but its repetitive peak is **28 Nm**; HEJ 70 "-60" has a repetitive peak of **63 Nm**.

**Kt / Kv / R are NOT published for the HEJ joints** — the datasheets state torque is derived "via electric motor current, compensated," so `Kt_ref=unknown` for all HEJ rows. Operating range is **30–60 V** (headline family 20–60 V; 20 V possible on request), not a single 60 V. Max joint velocity is quoted at both 48 V and 60 V.

**HPJ-DT (High Precision Joint)** — customizable strain-wave (zero-backlash) joints built on the frameless **EC frameless DT** motors (motor + 2× encoder + gear + output bearing; optional brake/safety/electronics). The current flyer (rev1.6) publishes joint-level data for **only four** systems: DT38S-WGA14, DT38M-WGU14, DT50S-WGA20, DT50M-WGU20, each as a **"Peak Joint Torque, Repetitive"** range and a **"Peak Joint Velocity"** range in **rad/s**. No rated/nominal joint torque, voltage, IP, or current is published at joint level.

The **only Kt / R Maxon publishes is at the frameless-motor level**: "Torque Constant, FOC, Amplitude (mNm/A)" and "Terminal Resistance, Phase-Phase (Ω)". Per our modeling paper, Maxon references Kt to **phase current** — the "FOC, Amplitude" wording confirms it is the amplitude of the sinusoidal phase current, so all HPJ rows use **`Kt_ref=phase_peak`** and **`R_ref=phase-phase (terminal)`**, with a note that these are motor-level (pre-gear). Winding is single-tooth concentrated. Pole-pair count is not published in any accessible maxon document.

### Frameless EC DT motor reference table (raw, from flyer rev1.6)
| Motor | OD/ID mm | Kt FOC amp (mNm/A) | R ph-ph (Ω) | MSat (Nm) | stator+rotor (g) |
|---|---|---|---|---|---|
| DT38S | 42/17 | 16.5 | 0.26 | 0.5 | 71 |
| DT38M | 42/17 | 32.2 | 0.37 | 1.0 | 104 |
| DT50S | 54/28 | 60.4 | 0.58 | 1.5 | 123 |
| DT50M | 54/28 | 92.6 | 0.76 | 2.2 | 163 |
| DT65S | 70/35.5 | 88.1 | 0.33 | 2.6 | 226 |
| DT65M | 70/35.5 | 157 | 0.47 | 4.9 | 339 |
| DT85M | 90/47 | 126 | 0.16 | 5.6 | 526 |
| DT85L | 90/47 | 219 | 0.22 | 9.8 | 774 |
(EC frameless DT brochure Jul2025 gives slightly different peak-torque/MSat figures per size, e.g. DT65M 3.61 Nm vs flyer 4.9 Nm — maxon's own two docs disagree here.)

### Data gap: DT65 / DT85 HPJ joints
The DT65S-WGA25, DT65M-WGU25, DT85M-WGA32, DT85L-WGU32 **joint** systems (in scope and in our existing DB) are **not present in the current published flyer rev1.6**, which stops at DT50M. An older flyer (media/247660) that likely fed those rows is no longer retrievable (returns an error page). I kept these four rows but **flagged the joint-level torque/speed/mass/dims as UNVERIFIED** (carried from prior DB), while attaching **verified motor-level Kt/R/OD** from the DT brochure. These should be confirmed with robotics@maxongroup.com.

### Prices
No prices are published for HEJ or HPJ (contact-sales products). `price_EUR` left blank for all rows.

## Cross-check vs existing data (`actuators.csv`)

Format: field — our (existing) / found (maxon) / verdict. "Maxon" = authoritative unless noted.

### HEJ 50 (existing row `maxon-hej-50`)
- Peak torque — **30 / 28 Nm** — **maxon**. Datasheet repetitive peak is 28 Nm; "30" is the model-name / 100e3-impact number, not the controllable peak.
- Weight — **0.57 / 0.53 kg** — **maxon** (datasheet 0.53 kg).
- Voltage — **60 / 30–60 V** — **maxon** (operating range 30–60 V).
- Rated speed — **200 rpm / 21 rad/s @48V (200) & 26 rad/s @60V (248)** — OK as 48 V figure, but note the existing row pairs "60 V" with "200 rpm" which is inconsistent (200 rpm is the 48 V value; 60 V gives 248 rpm).
- Rated power — **230 W / not stated by maxon** — existing 230 W ≈ 11 Nm × 21 rad/s (computed, not a datasheet figure). Left blank in new CSV.
- Impact ladder — existing `1e3@40, 12e6@23` / maxon `12e6@23, 100e3@30, 1e3@40` — **match**; existing just omits the middle 100e3@30 Nm point.
- New raw data added: Ø71.5 mm, L 65 mm, cont. DC-link 4.7 Arms, default not IP-sealed (IP67 on request), 14-bit encoder.

### HEJ 70 (existing `maxon-hej-70`)
- Peak torque — **62 / 63 Nm** — **maxon** (repetitive peak 63 Nm).
- Weight — **1.05 / 1.04 kg** — **maxon** (minor).
- Voltage — **60 / 30–60 V** — **maxon**.
- Rated speed — **172 / 170 rpm** (17.8 rad/s @48V) — effectively match; 60 V gives 210 rpm.
- Rated power — **486 W / not stated** — ≈ 27 Nm × 18 rad/s (computed). Blank in new CSV.
- Impact ladder — `1e3@67, 12e6@38` / `12e6@38, 100e3@50, 1e3@67` — **match** (+100e3@50 added).
- New raw data: Ø88 mm, L 77 mm, cont. 8.0 Arms, IP67, two P/N variants (radial 933846 / axial 933847), integrated fan.

### HEJ 90 (existing `maxon-hej-90`)
- Peak torque — **140 / 140 Nm** — **match** (180 Nm variant on request).
- Rated torque — **75 / 75 Nm** — **match**.
- Weight — **2.00 / 2.006 kg radial (1.987 axial)** — **match**.
- Voltage — **60 / 30–60 V** — **maxon**.
- Rated speed — **96 / 99 rpm** (10.4 rad/s @48V; existing 96 came from rounding 10 rad/s) — **maxon** more precise; 60 V gives 124 rpm.
- Rated power — **754 W / not stated** — ≈ 75 Nm × 10.05 rad/s (computed). Blank in new CSV.
- Impact ladder — `1e3@320, 12e6@180` / `12e6@180, 100e3@240, 1e3@320` — **match** (+100e3@240).
- New raw data: Ø108 mm, L 90 mm, cont. 8.0 Arms, IP67, 12-bit encoder, P/N 831220/895330.

### HEJ Hercules (existing `maxon-hej-hercules-dev`)
- Peak — existing `~250–300` / flyer **300 Nm** — use 300.
- Continuous — existing blank / flyer **150 Nm** — add 150 Nm.
- Otherwise match: <3 kg, ~10 rad/s (~96 rpm), 20–60 V, EtherCAT. Still in development / preliminary.

### HPJ DT38S-WGA14 (existing `maxon-hpj-dt38s-wga14`)
- Torque (repetitive peak) — **12–19 / 12–19 Nm** — **match**.
- Speed — existing **85–170 rpm** / flyer **8.8–17.5 rad/s = 84–167 rpm** — **match** (rad/s is the raw unit).
- Mass **0.9 / 0.9 kg**, Ø **74 / 74 mm** — match. Length **73 / 74 mm** — trivial.
- New: motor Kt 16.5 mNm/A (phase, FOC amplitude), R ph-ph 0.26 Ω.

### HPJ DT38M-WGU14 (existing `maxon-hpj-dt38m-wgu14`)
- Torque — **23–36 / 23–36 Nm** — **match**.
- Speed — existing **65–130 rpm** / flyer **8.8–17.5 rad/s = 84–167 rpm** — **MISMATCH → maxon** (existing understates).
- Mass — **0.9 / 1.0 kg** — **MISMATCH → maxon**. Length **83 / 86 mm** — maxon.

### HPJ DT50S-WGA20 (existing `maxon-hpj-dt50s-wga20`)
- Torque — **39–64 / 39–64 Nm** — **match**.
- Speed — existing **32–106 rpm** / flyer **4.2–13.3 rad/s = 40–127 rpm** — **MISMATCH → maxon**.
- Mass **1.5 / 1.5 kg**, Ø **94 / 94 mm** — match. Length **78 / 81 mm** — maxon.

### HPJ DT50M-WGU20 (existing `maxon-hpj-dt50m-wgu20`)
- Torque (repetitive peak) — existing **73–120** / flyer **27–120 Nm** — **MISMATCH → maxon** on the low end (27, not 73); high end 120 matches.
- Speed — existing **22–69 rpm** / flyer **4.2–22.0 rad/s = 40–210 rpm** — **MISMATCH → maxon** (large).
- Mass **1.8 / 1.8 kg**, Ø **94 / 94 mm**, Length **86 / 86 mm** — match.

### HPJ DT65S-WGA25, DT65M-WGU25, DT85M-WGA32, DT85L-WGU32 (existing rows)
- **Not in current maxon flyer rev1.6.** Joint-level values (e.g. DT65M-WGU25 127–229 Nm @ 12–41 rpm; DT85L-WGU32 281–484 Nm @ 9–29 rpm) **could not be verified** against any currently accessible maxon source and are carried as **UNVERIFIED**. Motor-level Kt/R/OD for their DT65S/M and DT85M/L motors are verified from the DT brochure and added. **Action:** confirm joint specs with maxon before trusting.

## Discrepancy summary (for orchestrator)
| Model | Field | Ours | Maxon (authoritative) | Which is right |
|---|---|---|---|---|
| HEJ 50 | Peak torque | 30 Nm | 28 Nm (repetitive peak) | maxon |
| HEJ 50 | Weight | 0.57 kg | 0.53 kg | maxon |
| HEJ 50 | Voltage | 60 V | 30–60 V | maxon |
| HEJ 70 | Peak torque | 62 Nm | 63 Nm | maxon |
| HEJ 70 | Weight | 1.05 kg | 1.04 kg | maxon |
| HEJ 90 | Rated speed | 96 rpm | 99 rpm @48V (124 @60V) | maxon |
| HEJ Hercules | Continuous | (blank) | 150 Nm; peak 300 | maxon |
| HPJ DT38M-WGU14 | Speed | 65–130 rpm | 84–167 rpm (8.8–17.5 rad/s) | maxon |
| HPJ DT38M-WGU14 | Mass | 0.9 kg | 1.0 kg | maxon |
| HPJ DT50S-WGA20 | Speed | 32–106 rpm | 40–127 rpm (4.2–13.3 rad/s) | maxon |
| HPJ DT50M-WGU20 | Peak torque (low) | 73 Nm | 27 Nm | maxon |
| HPJ DT50M-WGU20 | Speed | 22–69 rpm | 40–210 rpm (4.2–22.0 rad/s) | maxon |
| HPJ DT65/DT85 (4 rows) | all joint specs | present | not published in rev1.6 | UNVERIFIED — confirm w/ maxon |

All "computed" rated-power figures (230/486/754 W) are `Mnom × Vmax@48V`, not maxon datasheet values — left blank in the new CSV to respect raw-data-only.
