# RobStride & SteadyWin — Direct-Sale QDD Actuators

Fresh capture (2026-07). Cheap integrated joint modules (motor + FOC driver + planetary
reducer + magnetic encoder(s)) sold direct online. Data in
`research/robstride-steadywin_specs.csv` (28 rows: 7 RobStride, 21 SteadyWin).

## Families captured

**RobStride** (灵足时代 / Lingzu Times) — `RS00, RS01, RS02, RS03, RS04, RS05, RS06`.
All CAN-bus (1 Mbps, CANopen), FOC, dual 14-bit magnetic encoders (RS01 = single),
planetary reduction, IP52 (IP67 optional on most). Torque span rated 1.6–40 N·m /
peak 5.5–120 N·m. Task asked for 00–04; 05 (5.5 N·m mini) and 06 (36 N·m) added as newer.

**SteadyWin** (Outrotor Technology) — GIM planetary series: `GIM3505, GIM3510, GIM4305,
GIM4310, GIM4315, GIM6010, GIM8108, GIM8115, GIM10015`, each in several gear-ratio
variants (suffix = ratio, e.g. GIM6010-8 = 8:1). CAN (+RS485 on many), FOC, 14/16-bit
encoder, IP54, backlash 15 arcmin, steel planetary gears. Captured 21 model/ratio
combos. Torque span rated 0.67–35.5 N·m / peak 1.79–133.5 N·m.

## Channel & pricing (EUR)

- **RobStride**: official AliExpress store `aliexpress.com/store/1103506059` and
  `robstride.com`; resellers Seeed Studio, OpenELAB, Amazon, AIFITLAB. EUR prices from
  OpenELAB (motor without debug board): **€126 (RS05) → €280 (RS04)**.
- **SteadyWin**: official `steadywin-motor.com` (Outrotor / Alibaba); resellers OpenELAB,
  AIFITLAB. EUR from-prices (base config, driver optional) from OpenELAB:
  **~€65 (GIM3505-8) → €186 (GIM8115-9)**; only 9 of 21 models had a confirmed EUR price.

## Datasheets downloaded → `datasheets/robstride-steadywin/`

- `robstride_RS00..RS06_user_manual.pdf` — 7 official manuals (from the RobStride GitHub
  `RobStride/Product_Information`). Contain the authoritative spec tables (§1.2–1.4).
- `steadywin_planetary_reduction_motor_selection_table.xlsx` — official master spec table
  for the **entire** GIM family (from steadywin-motor.com document-download). This is the
  primary SteadyWin source; `steadywin_docs/Planetary Reduction Motor/<model>/` holds
  per-model 2D drawings + parameter sheets for the 5 named models (extracted).
- `steadywin_planetary_reduction_motor_docs.zip` — full per-model drawing/CAD pack.
- `steadywin_brushless_direct_drive_motor_selection_table.xls` — bonus (frameless DD motors, not QDD).

## Well-documented vs thin

**Well-documented**
- RobStride RS00, RS02, RS03, RS04: full electrical table — rated/peak torque, no-load &
  rated speed, power, weight, dims, gear, Kt, back-EMF, poles, currents; RS03/RS04 also
  line resistance + inductance.
- SteadyWin whole GIM family: the xlsx gives winding (Δ/Y), voltage, power, rated/peak
  torque, rated/max speed, rated/peak current, phase R + L, speed const, Kt, pole pairs,
  gear, weight (with/without driver), size, loads, IP, comms, encoder — very complete.

**Thin / missing**
- RobStride RS05 & RS06: rated power not published; RS05 pole-pairs not stated; no line
  resistance for RS00/RS02/RS05/RS06.
- RobStride publishes **no winding config** (Δ/Y) and no true rpm/V Kv — only a back-EMF
  constant in Vrms/kRPM. Kt is stated only as "N·m/Arms".
- SteadyWin: no per-model prices for ~12 of 21 variants; exact official product-page URLs
  not found for every variant (root `steadywin-motor.com` used as fallback).

## Data-integrity notes (read before using electrical constants)

- **RobStride currents are peak (Apk)**, not RMS — recorded raw in Cont/Peak_Current_A.
- **RobStride Kt** given as `N·m/Arms`; frame not stated on the datasheet. Kt × (rated
  Apk/√2) reproduces the rated **output** torque for every model, so it is output-shaft /
  RMS-phase referenced (marked "[derived]" in `Kt_ref`). **RobStride Kv column holds the
  back-EMF constant Ke** (Vrms/kRPM), which is motor-shaft referenced (inferred) — it is
  NOT a rpm/V speed constant.
- **SteadyWin dual windings**: most 6010/8108/8115/10015 models ship in a 24 V and a 48 V
  winding with different torque/Kt/current. Each CSV row uses the manufacturer's *primary*
  (header) column; the alternate winding's rated/peak torque, R, Kt, current are in Notes.
  The table's "Torque constant (N·m/A)" and "Speed constant (rpm/V)" have no stated
  motor/output frame (`_ref="unknown"`), and Kv shows some internal inconsistency between
  24 V/48 V columns — treat SteadyWin Kt/Kv as approximate.
- SteadyWin weight & dimensions in the CSV are the **with-driver** figures (full actuator).
- Discrepancies flagged in Notes: RS01 rated voltage = 36 V (per OpenELAB, unusual vs RS02
  48 V); RS03 voltage range = 24–60 V in the manual but 15–60 V on OpenELAB.
