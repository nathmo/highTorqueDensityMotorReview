# QDD / Western direct-sale actuators & motors — research notes

Fresh capture of direct-sale BLDC motors, quasi-direct-drive (QDD) actuators and standalone
motor controllers from **Unitree**, **mjbots**, and **HEBI Robotics**.

Data lives in [`qdd-western_specs.csv`](qdd-western_specs.csv) (16 rows). Manufacturer pages/datasheets
were treated as authoritative. RAW datasheet wording preserved; unknown fields left blank and the
exact source noted per row. Two image-based datasheet PDFs were downloaded and OCR-read visually
(rendered to PNG), stored under `datasheets/qdd-western/`.

Prices converted to EUR at **~0.92 USD→EUR**; original price + store kept in `price_source`.
Adjust the rate if a precise conversion is needed.

---

## Unitree (5 rows — 4 direct-sale motors + 1 integrated)

Unitree sells joint motors directly via **shop.unitree.com** (official store). Confirmed standalone
products: **GO-M8010-6** ($369), **A1 Motor** ($500), **B1 Motor** ($3,000), **IM6014 Motor** (from $539).
The **M107** is *not* sold standalone (integrated in H1/B2) and is included only as a flagged
marketing-data row.

- **GO-M8010-6** — best-documented Unitree part. Full user manual PDF (downloaded, image-based,
  read via render). Integrated 6.33:1 reducer, "Maximum Torque 23.7 Nm" (output), 30 rad/s @24V,
  Kt 0.63895 Nm/A (reference frame unstated), 15-bit encoder, RS485. No rated torque / Kv / R.
- **A1 Motor** — official spec page (unitree.com/a1/motor). "Maximum Instantaneous Torque 33.5 N·m",
  21 rad/s, Kt 0.9287 Nm/A (frame unstated), 605 g, 20–40 V. Reduction ratio NOT published.
- **B1 Motor** — heavy-duty knee/joint motor. 140 N·m (max instantaneous), 9.1 rad/s, 1:16, 1.2 kg,
  36–64 V, RS485. Official store lists price only; spec numbers came from a reseller (sonnyrobotics).
- **IM6014 Motor** — newest retail motor. Full spec on unitree.com/mobile/IM6014: 34.4 N·m (opposing
  rotation) / 31.7 N·m (with rotation), 54.2 rad/s no-load @60V, 12.67:1 (3:38), 40 A line, 535 g,
  φ65×60 mm, dual absolute encoders, 24–75 V. No Kt / rated torque published.
- **M107** — integrated H1/B2 joint actuator, not purchasable standalone. Only marketing numbers exist
  (knee ~360, hip ~220, ankle ~59, arm ~75 N·m; 189 N·m/kg density). Flagged in Notes; price blank.

**Documentation quality:** mixed. GO-M8010-6 has a real user-manual datasheet. A1 and IM6014 have
clean official spec tables. B1 has a price on the official store but no on-site spec table (reseller-sourced
specs). No Unitree part publishes Kv, pole pairs, phase resistance, or winding type, and torque-constant
reference frames are never stated → all `*_ref="unknown"`.

## mjbots (5 rows — 1 actuator, 1 motor, 3 drivers)

US vendor, **mjbots.com**, open-source ecosystem, cleanest and most consistent spec presentation of the three.

- **qdd100 beta 3** (actuator, $879; dev kit $999) — 6:1 planetary QDD. Excellent thermal-tiered torque
  spec: peak 16 N·m (<1 s), 10 N·m (60 s), 6 N·m (400 s), 3.3 N·m continuous. 100 mm × 44 mm, 507 g,
  10–44 V, CAN-FD. Currently out of stock (50-unit MOQ).
- **mj5208** (motor, $74) — 5208 outrunner, Kv 330, peak torque 1.7 N·m, 7500 RPM, 193 g, 63×25 mm.
  No Kt / R / pole pairs / winding (Kv frame unstated).
- **moteus r4.11 / n1 / c1** (drivers, $94 / $149 / $69) — standalone FOC controllers. Each publishes
  continuous phase current (w/o and w/ thermal management), peak phase current, bus voltage range,
  and peak electrical power — exactly the driver-layer fields requested:
  - r4.11: 12/32 A cont, 100 A peak, 10–44 V, 900 W @30 V
  - n1: 9/26 A cont, 100 A peak, 10–54 V, 2 kW @36 V
  - c1: 5/14 A cont, 20 A peak, 10–51 V, 250 W @28 V

**Documentation quality:** best of the three. Public prices, explicit voltage/current envelopes, open-source
firmware. Gap: motor-level electrical constants (Kt, R, pole pairs, winding) not published for mj5208 or qdd100.

## HEBI Robotics (6 rows — X-series actuators)

X-Series is now a **legacy** line (replaced by T-Series) but still sold/supported. All six models
(**X5-1, X5-4, X5-9, X8-3, X8-9, X8-16**) captured from the official 2-page datasheet PDF (downloaded,
image-based, read via render).

- Series-elastic geared actuators, 24–48 V DC, 100 Mbps Ethernet (dual port), ±0.25° backlash,
  15 mm hollow bore. Peak torque 2.5→38 N·m, continuous 1.3→16 N·m, max speed 90→14 RPM.
- **Gear ratios, torque/speed constants, and motor winding resistance** are NOT on the X-series
  datasheet — they were taken from HEBI's T-series parameter table (docs.hebi.us/hardware.html), which
  HEBI explicitly states "can be directly correlated to the corresponding X-Series Actuators." Flagged in
  every HEBI row's Notes. Ratios 272:1→1742:1; Kt 1.1→8.8 N·m/A (output); speed const 5.6→0.7 RPM/V;
  winding R 10 Ω (X5 motor) / 5.3 Ω (X8 motor). Winding type wye/delta unstated → noted.
- **Caveat:** the datasheet's "Cont./Peak Current" (0.5/1.6 A @36V for X5; 1.3/3.0 A for X8) are
  bus-side currents, inconsistent with the output Kt — not phase currents. Recorded as-is with a note.

**Pricing:** HEBI publishes **no public prices**. Used reseller mybotshop.de: €3,945.95 (X5 models),
≈€4,595.95 (X8 = X5 + €650). `price_source` flags this clearly.

**Documentation quality:** good mechanical/torque datasheet, but X-series is de-emphasized in favor of
T-series; electrical constants require cross-referencing the T-series docs. No IP rating, no pole pairs,
no winding type published. No public pricing.

---

## Notable gaps (for the orchestrator)

- **Kt/Kv reference frames** are unstated for every Unitree and mjbots part → `*_ref="unknown"`.
  HEBI constants are output-referenced (T-series correlation) but winding type is unknown.
- **Pole pairs & winding type**: not published by any of the three brands for any product.
- **Phase resistance (R)**: only HEBI (via T-series docs, 2 of 6 rows) — not published by Unitree/mjbots.
- **Unitree B1**: specs are reseller-sourced (official store has no spec table).
- **Unitree M107**: marketing figures only, not a standalone product (row flagged).
- **HEBI pricing**: reseller-only (no public MSRP); X8 price is X5+€650 inferred from reseller note.
- **HEBI IP rating**: not stated on the datasheet.
- **datasheet_local** populated only for GO-M8010-6 and HEBI X-series (only two products with real PDF
  datasheets; both image-based, read by rendering to PNG). All other specs are from HTML product pages.
