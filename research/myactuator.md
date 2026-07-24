# MyActuator (Suzhou Micro Actuator Technology Co., Ltd.) — direct-sale actuator specs

Data collected 2026-07 for the direct-sale (no-quote) integrated actuators sold under the
**RMD-X planetary**, **EPS-RH harmonic**, and **RMD-L direct-drive** lines. All values are
**raw datasheet figures** — unknowns are left blank, never guessed.

Output file: [`myactuator_specs.csv`](myactuator_specs.csv) — 29 rows, one per variant.

## Primary source

The single best raw source is MyActuator's **2025 General Catalog** (10 MB PDF), which contains a
full "Product Parameters" table + stall-torque table + dimensioned drawing for every V4 planetary
and every RH harmonic model. Downloaded locally:

- `datasheets/myactuator/MyActuator-2025-product-manual.pdf` (covers all RMD-X V4 planetary + all EPS-RH harmonic)
- `datasheets/myactuator/RMD-X10-40_datasheet.pdf` (RMD-X10 V3 1:7, from the X10-40 download archive)
- `datasheets/myactuator/RMD-X10-100_datasheet.pdf` (RMD-X10-S2 V3 35:1, from the X10-100 download archive)

The X10 series and the RMD-L series are **not** in the 2025 catalog (X10 is the older V3 line; RMD-L is a
separate direct-drive line). X10 came from MyActuator's own per-model download ZIPs (which contain spec PDFs);
RMD-L came from the official US distributor **Dings Motion USA** (dingsmotionusa.com) and reseller rcdrone.top.
Prices in EUR were converted from AIFITLAB USD list prices at ~0.92 EUR/USD (original USD retained in `price_source`).

The product pages on myactuator.com render their spec tables as **images** (Wix site), so live-fetch text
extraction returns nothing useful — the catalog PDF and reseller mirrors (AIFITLAB, Dings, RobotShop) are the
usable text sources.

## Coverage (29 variants)

- **RMD-X planetary (12):** X2-7, X4-10, X4-36, X6-8, X6-60, X8-32, X8-50, X8-120, X12-320, X15-450, X10-40 (7:1), X10-100 (35:1)
- **EPS-RH harmonic (7):** RH-11 (80:1), RH-14, RH-17 Lite, RH-17, RH-20, RH-25, RH-32 (all standard 100:1; 50:1 variants noted in each row's Notes)
- **RMD-L direct-drive (10):** L-4005, L-4010, L-4015, L-5005, L-5010, L-5015, L-7015, L-7025, L-9015, L-9025

## Key data-integrity notes

- **MyActuator "torque constant" is OUTPUT-referenced.** The datasheet field "Module Torque Constant"
  (N.m/A) is torque at the **output shaft after the gearbox** — recorded as `Kt_raw_Nm_per_A` with
  `Kt_ref = "output (module, after gearbox)"`. This confirms the interpretation flagged in the brief: the
  existing DB's "Kt" values (2.1, 2.4, 3.3, 5.8, 6.9, 7.3, 7.4, 10.1, 4.0) are output/module constants, and
  are correct as such.
- Each planetary/harmonic datasheet **separately** lists a "Motor Back-EMF Constant" in **Vdc/krpm**
  (motor/bus-referenced) — recorded in `Kv_raw` + `Kv_unit` + `Kv_ref`. This is a back-EMF (Ke) constant,
  not a speed constant; kept raw.
- `Motor Phase Resistance` is the motor phase value; `3 Phase Connection = Y` → `Winding = wye`.
- `Cont_Current_A` / `Peak_Current_A` are the datasheet **phase currents in A(rms)**.
- Rated speed → `Rated_Speed_RPM`; No-load speed → `Max_Speed_RPM`. Rated torque test is at 60 °C rise / 24 °C ambient.
- Harmonic standard models ship **without brake**; brake variant weights/lengths are in each row's Notes.
  Standard harmonic units are not waterproof (IP54 available on request) — `IP` left blank, noted in Notes.
- The RMD-L "torque constant" (rcdrone) is motor-referenced but the line is direct-drive (ratio 1:1), so
  motor = output; recorded `Kt_ref = "motor (direct drive, ratio 1:1)"`, Kv in rpm/V. Kt·Kv ≈ 9.55 (self-consistent).
- **X8-50** diameter recorded (96 mm, X8 frame) but its datasheet drawing length was not legible → blank.
- **RMD-L-4005 / -4010**: only peak torque is published by distributors → all other fields blank (not guessed).

## Cross-check vs existing data (actuators.csv)

Existing rows were re-verified against the raw datasheets. Format: **our value / datasheet value → verdict**.

| Model | Field(s) | Our value | Datasheet value | Verdict |
|---|---|---|---|---|
| RMD-X6-P20-60-E | all | 20/60, 153/176, 320 W, 0.82 kg, Kt 2.1 | 20/60, 153/176, 320 W, 0.82 kg, Kt(out) 2.1 | ✅ exact match |
| RMD-X8-P20-120-E | all | 43/120, 127/158, 574 W, 1.40 kg, Kt 2.4 | identical | ✅ exact match |
| RMD-X12-P20-320-E | **power, weight** | 85/320, 100/125, **1000 W**, **2.40 kg**, Kt 3.3 | 85/320, 100/125, **900 W**, **2.37 kg**, Kt(out) 3.3 | ⚠️ **CORRECTION** |
| RMD-X15-P20-450-E | all | 72 V, 145/450, 98/108, 1480 W, 3.50 kg, Kt 5.8 | identical | ✅ exact match |
| RMD-X10-P7-40-R-N | **rated τ, speed, power** | 15/40, **165 rpm**, **265 W** | datasheet PDF: **12/40, 170 rpm, 215 W** | ⚠️ **CONFLICT** (see below) |
| RMD-X10-P35-100-R-N | all | 35:1, 50/100, 50 rpm, 265 W, 1.70 kg | identical | ✅ exact match |
| EPS-RH-32-100-E-N-D | all | 150/229, 18/20, 282 W, 4.32 kg (4.74 w/brake), Kt 6.9 | identical | ✅ exact match |
| EPS-RH-25-100 | all | 108/157, 25/30, 282 W, 2.42 kg (2.74 w/brake), Kt 10.1 | identical | ✅ exact match |
| EPS-RH-20-100 | all | 50/80, 25/30, 130 W, 1.45 kg (1.75 w/brake), Kt 7.3 | identical | ✅ exact match |
| EPS-RH-17-100 | all | 35/54, 25/30, 91 W, 1.11 kg (1.28 w/brake), Kt 7.4 | identical | ✅ exact match |
| EPS-RH-14-100 | all | 11/28, 25/30, 28 W, 0.78 kg, Kt 4.0 | identical | ✅ exact match |

### The two flags

1. **RMD-X12-P20-320-E rated power = 900 W, not 1000 W (and weight 2.37 kg, not 2.40).**
   Both the 2025 catalog datasheet **and** the AIFITLAB store list `Rated Output Power = 900 W`, `Weight = 2.37 kg`.
   The existing DB value of 1000 W is wrong; recommend correcting to 900 W / 2.37 kg. Torque and Kt are correct.

2. **RMD-X10-P7-40 — MyActuator's own datasheet PDF disagrees with its website/AIFITLAB.**
   - MyActuator V3 datasheet PDF (`RMD-X10-40_datasheet.pdf`, Apr 2024): **rated 12 N·m @ 170 rpm, 215 W**,
     motor Kt 0.32 N·m/A, motor Kv 30 rpm/V, R 0.3 Ω, 1.15 kg, 7:1, backlash 7 arcmin.
   - Website / AIFITLAB store / existing DB: **rated 15 N·m, 165 rpm, 265 W** (peak 40, 1.15 kg).
   Peak torque (40) and weight (1.15 kg) agree; the rated point / rated power conflict is internal to MyActuator's
   sources. The CSV row records the **datasheet-PDF** values (rawest source) with the website figures noted; which is
   "right" cannot be resolved without the vendor — flagged for the orchestrator. (This is also the only planetary row
   whose torque constant is **motor**-referenced, because the V3 PDF lists a motor torque constant, not a module one.)

## New products not previously in the DB

Beyond the 11 cross-check rows, the following direct-sale variants were added:
X2-7 (24 V), X4-10 (24 V), X4-36 (24 V), X6-8 (V3, 48 V), X8-32 (24 V, single-encoder RS485),
X8-50 (48 V, high-Kt X8 winding), EPS-RH-11 (80:1), EPS-RH-17-Lite (100:1), and the entire RMD-L
direct-drive line (10 models, gimbal-class 0.13–2.79 N·m). Note several small planetary V4 units run at
**24 V**, not 48 V — worth flagging when the DB assumes 48 V.
