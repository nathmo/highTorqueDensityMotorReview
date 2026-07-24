# CubeMars — direct-sale (no-quote) product research

Source: <https://www.cubemars.com/> (manufacturer store, USD pricing, direct online
sale — also mirrored on Amazon / AliExpress / Seeed / RobotShop). Data captured
2026-07-23. All numeric specs are raw datasheet values from each product page's
Specification block and the on-page product-comparison table. USD→EUR converted at
**1 USD = 0.876 EUR** (spot, 2026-07-23); original USD kept in `price_source`.

`research/cubemars_specs.csv` — **45 rows** (25 `actuator`, 20 `motor`).
27 datasheet PDFs downloaded to `datasheets/cubemars/` (2D dimensional drawings +
the AK-series product manual — CubeMars publishes no standalone spec-sheet PDF; the
specs live on the product page, the drawing PDF carries the dimensions).

## Families covered

| Family | Layer | Products captured | Notes |
|---|---|---|---|
| **AK** robotic actuators | actuator | 18 (AK10-9 V3/V2, AK80-9 V3, AK80-8, AK80-6, AK80-64, AK70-10, AK70-9 V3, AK60-39 V3, AK60-6 V3/V1.1, AK45-36/-10 V3+V1, AK40-10 V3+V1) | Motor+planetary+driver+encoder integrated (BLDC + FOC, CAN/UART). Electrical constants (Kt/Kv/R/winding/pole-pairs) fetched individually for the 5 scope models (AK10-9 V3, AK60-6 V3, AK70-10, AK80-6, AK80-9 V3); the rest are mechanical-only from the on-page comparison table. |
| **AKE** quasi-direct-drive | actuator | 3 (AKE90-8 KV35, AKE80-8 KV30, AKE60-8 KV80) | Motor + 8:1 planetary, **no encoder / no driver board** (open QDD module). Full electrical block captured for all three. |
| **AKH** hollow-shaft planetary | actuator | 2 (AKH70-48, AKH70-16) | Planetary modules; mechanical-only (comparison table). Individual pages not fetched → `product_url` = category page. |
| **AKA** robotic actuators | actuator | 2 (AKA10-9, AKA60-6) | Mechanical-only; `product_url` = category page. |
| **RI** frameless inrunner | motor | 5 (RI100, RI80 V2, RI70, RI60, RI50) | Full electrical block; multi-voltage 24/36/48 V (speeds recorded @48 V, triplets in Notes). |
| **RO** frameless outrunner | motor | 5 (RO100, RO80, RO60 Standard-with-hall; RO50, RO40 Lite) | Full electrical block. Standard vs Lite differ in weight/inertia — Standard used, both noted. |
| **GL** gimbal motors | motor | 10 rows / 8 products (GL30, GL35, GL40 KV70+KV210, GL60, GL80 KV30+KV60, GL100, GL40 II, GL60 II) | Full electrical block. Multi-KV pages split into one row per winding variant. |

**Price range (converted, base config / low bound of range):**
- Actuators: AK40-10 ~€88 → AK80-64 ~€780 (AKE €192–€424).
- Motors: RO40 ~€45 → GL100 ~€239.

## Reference-frame notes (per repo convention)
- CubeMars labels its winding resistance **"Phase to Phase resistance"** → recorded as
  `R_ref = terminal_ll`. Winding type (star/delta) **is published** per product →
  recorded as `Winding` (`star`→`wye`). This makes R resolvable to phase R in-app.
- **Kv/Kt frame is never stated** (no phase/line-to-line qualifier) → `Kt_ref` and
  `Kv_ref` set to `unknown` (not guessed), even though delta+Kv is the usual drone
  line-to-line convention. `Kv_unit = rpm/V` throughout.
- For AK/AKE the published **Kt/Kv/R/pole-pairs are motor-frame (pre-gearbox)** while
  the torque/speed/power figures are **output (post-Nx planetary)** — flagged in each Note.
- Torque wording on AK/AKE/RI/RO/GL is uniformly **"Rated torque" + "Peak torque"**;
  **no "max momentary" / "stall" figure is published** → `Max_Momentary_Torque_Nm` left blank.

## Data-quality flags found on CubeMars' own pages
- **AKE90-8**: winding-resistance column header is mislabeled **"MΩ"**; the value 164 is
  **milliohms** (0.164 Ω) — the sibling AKE80/AKE60 pages label the identical column "mΩ",
  and a separate row gives insulation resistance as 10 MΩ. Recorded R = 0.164 Ω.
- **AK70-10**: weight conflicts within the same page — spec block **621 g** vs on-page
  comparison table **521 g**. Recorded 0.621 kg, discrepancy noted.
- **RO50 Lite**: peak current printed **0.9 A** (below its 3.4 A rated) — almost certainly
  a typo; recorded raw with a flag.
- **RO40 Lite**: motor constant printed **0.52 Nm/√W** but computes to ~0.05 (Kt/√R) — likely
  a missing-zero typo (not a CSV column; noted only).
- **GL30/GL35/GL80/GL100**: model-name KV differs from the spec-table Kv (e.g. GL30 title
  "KV290" vs spec 255; GL100 "KV10" vs 9.3) — spec-table value recorded, title noted.
- **GL40 II**: Ke printed 0.0115 V/krpm (units-slip typo, ~11.5).

---

## Cross-check vs existing data

### actuator `cubemars-ake90-8-kv35` (actuators.csv)
Existing: 48 V, rated 55 Nm, peak 170 Nm, rated speed 120 rpm, max 210 rpm, **1500 W**,
1.4 kg, **Ø90 mm**, price **€483**; Notes "Kt=0.272; rated/continuous torque not published;
curve @48VDC shows 1500W peak out; no rated torque given".

CubeMars product page (verified):

| Field | Existing row | CubeMars page (raw) | Verdict |
|---|---|---|---|
| Rated torque | 55 Nm | **"Rated torque (Nm) 55"** | ✅ **Published, not an assumption.** The orchestrator's doubt ("55 Nm rated may be an assumption") is resolved — CubeMars explicitly lists a 55 Nm Rated torque. Existing Note "rated/continuous torque not published … no rated torque given" is **incorrect**. |
| Peak torque | 170 Nm | "Peak torque (Nm) 170" | ✅ match |
| Rated speed / max | 120 / 210 rpm | Rated speed 120 / No-load 210 | ✅ match |
| Voltage | 48 V | 48 V | ✅ match |
| **Rated power** | **1500 W** | **"Rated Power (W) 700"** | ❌ **Mismatch.** CubeMars rated power = 700 W (≈ 55 Nm × 120 rpm). The 1500 W is peak output from the torque-speed curve, **not** the rated figure. Existing `Rated_Power_W` should be 700; 1500 belongs in a note as peak/curve power. |
| **Diameter** | **90 mm** | **"Ф107.5 × 43.5 mm"** | ❌ **Mismatch.** "90" is the nominal model number (stator class); actual housing OD = **107.5 mm**, length 43.5 mm. Existing Ø90 is the nameplate size, not the datasheet OD. |
| Length | (blank) | 43.5 mm | ➕ now filled |
| **Price** | **€483** | **$483.9 USD** → ≈ **€424** | ❌ **Currency error.** €483 is the USD number copied as EUR. True EUR ≈ 424 at 0.876 (pre VAT/import/shipping). |

### motor `cubemars-ake90-motor` (motors.csv)
Existing: Kt_raw 0.272, Kt_ref unknown, Kv_raw 35 rpm/V, Kv_ref unknown, Winding unknown,
R blank; Note "Likely **wye** winding + line-to-line Kv (drone convention): set **Winding=wye**
and Kv_ref=ll to unlock q-axis Kt and Km. **No R published.**"

| Field | Existing row / note | CubeMars page (raw) | Verdict |
|---|---|---|---|
| Kt / Kv | 0.272 Nm/A / 35 rpm/V | Kt 0.272, Kv 35 | ✅ match (self-consistent: 9.549/35 = 0.273). Motor-frame, pre-8:1. |
| **Winding** | note suggests **wye** | **"Winding type: delta"** | ❌ **The wye assumption is wrong — CubeMars publishes delta.** This matters: for a line-to-line Kv the q-axis factor is √(3/2) for delta vs 1/√2 for wye, so the suggested wye+ll fix would give the wrong q-axis Kt. Correct: `Winding=delta`, and since Kv frame is unstated keep `Kv_ref=unknown` (don't force `ll`). |
| **Phase R** | note "**No R published**" | **"Phase to Phase resistance 164"** (col mislabeled MΩ → 0.164 Ω) | ❌ **R is published:** 0.164 Ω phase-to-phase (`R_ref=terminal_ll`). With delta, R^φ = 1.5 × 0.164 = 0.246 Ω. CubeMars even prints **Km = 0.67372 Nm/√W** and L = 235 µH, J = 3377 g·cm², pole pairs 21 directly. The motor row can now be fully populated to unlock Km. |

### gearbox `cubemars-ake90-8-kv35-gbx` (gearboxes.csv)
planetary 8:1, output torque 55/170 Nm — ✅ consistent with the page (Reduction Ratio 8:1,
torque = integrated output). No change needed.

## Scope / what was skipped
- **AK/AKH/AKA mechanical-only rows** (13 of them) carry comparison-table specs but **no
  electrical constants** (Kt/Kv/R/winding not individually fetched); nominal KV is in the
  model name. AKH & AKA individual product pages were not opened → `product_url` points at
  the category page.
- **Underwater thrusters (SW/DW/W/TW), G-series gimbal, RI-Potting (RI85-PH/RI75-PH), the
  AKE driver board, and AK-series drivers** were out of scope and not captured.
- **Frameless OD/length** not printed in the RI100/RI80 and RO100/RO80/RO60 spec text (only
  in their 2D-drawing PDFs) → left blank; RI70's ~76 mm is an approximate marketing figure,
  kept in Notes not the Diameter field.
- Multi-voltage AK rows and RI motors: dual/triple-voltage speed sets are recorded at the
  top voltage (48 V) with the full 24/36-V triplet in Notes.
