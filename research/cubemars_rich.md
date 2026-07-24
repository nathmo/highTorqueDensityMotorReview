# CubeMars — rich datasheet re-scrape (full electrical parameter set)

Re-scrape of <https://www.cubemars.com/> capturing the **complete per-model spec
table** (motor constant Km, back-EMF constant Ke, inductance, rotor inertia,
mechanical & electrical time constants, back-drive torque, pole pairs, winding,
insulation, dielectric, etc.) that the first pass dropped for lack of columns.

- Deliverable: `research/cubemars_rich.csv` — **43 rows** (22 `actuator`, 21 `motor`).
- Datasheet drawings: **39 PDFs** in `datasheets/cubemars-rich/` (all 2D dimensional
  drawings — CubeMars publishes no standalone spec-sheet PDF; the numeric specs live
  on the product page, the drawing carries dimensions).
- Data captured **2026-07-24**. USD→EUR at **1 USD = 0.876 EUR** (repo convention),
  original USD kept in `price_source`.
- Raw datasheet values only; unknowns left blank. Every product URL kept.

## Units / conventions applied
- `Kt_ref = terminal_ll` for every row (CubeMars quotes Kt Nm/A and Kv rpm/V at the
  motor terminals, line-to-line; resistance is "phase-to-phase" = line-to-line).
- `Ke_raw` kept exactly as printed with `Ke_unit` = the printed label.
- R converted mΩ→Ω, L converted µH→H (and mH→H for AKH & GL60 II), inertia g·cm²→kg·m²
  (×1e-7). Km, time constants left in printed units (Nm/√W, ms).
- Winding recorded as printed (`delta` / `star`; blank where CubeMars omits it).
- For **AK / AKE / AKH / AKA** geared modules: torque/speed/power are **output**
  (post-gearbox); Kt/Kv/Ke/R/L/Km/pole-pairs are **motor-frame** (pre-gearbox) — noted per row.
- Dual/triple-voltage models: speeds recorded at the **top voltage**; the other-voltage
  speed sets are in `Notes`. Currents are DC (ADC) as CubeMars prints.

## Families covered
| Family | Layer | Rows | Full electrical block? |
|---|---|---|---|
| **AK** robotic actuators | actuator | 15 (AK10-9 V3+V2, AK80-9 V3, AK80-8, AK80-6, AK80-64, AK70-10, AK70-9 V3, AK60-39 V3, AK60-6 V3+V1.1 KV80+KV140, AK45-36 V3, AK45-10 V3, AK40-10 V3) | 8 complete; 5 miss elec-time-const; AK45/40 miss time-consts; AK60-6 V1.1 KV140 mechanical-only |
| **AKH** hollow-shaft planetary | actuator | 2 (AKH70-48, AKH70-16) | Km/L/J/Ke + mech-tc (elec-tc not published) |
| **AKA** robotic actuators | actuator | 2 (AKA10-9, AKA60-6) | complete |
| **AKE** quasi-direct-drive | actuator | 3 (AKE90-8, AKE80-8, AKE60-8) | complete |
| **RI** frameless inrunner | motor | 5 (RI100, RI80 V2, RI70, RI60, RI50) | complete |
| **RO** frameless outrunner | motor | 5 (RO100, RO80, RO60 Std; RO50, RO40 Lite) | complete (RO40 Km is a typo, see below) |
| **GL** gimbal | motor | 11 (GL30, GL35, GL40 KV70+KV210, GL60 KV25+KV55, GL80 KV30+KV60, GL100, GL40 II, GL60 II) | 10 complete; GL60 II missing Km/Ke/time-consts |

**33 of 43 rows** have the complete electrical set (Km, L, J, Ke **and both** time
constants). A further **8** have Km/L/J/Ke + mechanical time constant only (CubeMars
omits the electrical time constant on AK80-9, AK70-9, AK60-39, AKH70-48, AKH70-16),
and **3** (AK45-36, AK45-10, AK40-10 V3) publish Km/L/J/Ke but no time constants.
Only **2** rows lack a usable electrical block: **GL60 II** (no Km/Ke/time-consts on
page) and **AK60-6 V1.1 KV140** (comparison-table mechanical specs only).

Newly captured this pass that the first pass had as mechanical-only or blank:
full electrical constants for **AK10-9 V2, AK80-8, AK80-64, AK70-9 V3, AK60-39 V3,
AK45-36/-10 V3, AK40-10 V3, AK60-6 V1.1, AKH70-48/-16, AKA10-9, AKA60-6**; plus the
previously-missing **time constants** for every RI/RO/GL and the **frameless OD×length**
(RI100 Ø104×26, RI80 Ø85×27, RI70 Ø76×24, RO100 Ø113.5×36.2, RO80 Ø92.6×26.4, etc.).

---

## AKE90-8 KV35 cross-check vs user-supplied known-good datasheet
Live product page matches the supplied datasheet on **every** value:

| Field | Known-good | Live page | |
|---|---|---|---|
| Rated torque | 55 Nm | 55 | ✅ |
| Peak torque | 170 Nm | 170 | ✅ |
| Rated speed | 120 rpm | 120 | ✅ |
| No-load speed | 210 rpm | 210 | ✅ |
| Rated current | 21 A(DC) | 21 ADC | ✅ |
| Peak current | 72 A(DC) | 72 ADC | ✅ |
| Weight | 1400 g | 1400 | ✅ |
| Ratio | 8:1 | 8:1 | ✅ |
| Pole pairs | 21 | 21 | ✅ |
| Winding | delta | Delta | ✅ |
| Kt | 0.272 Nm/A | 0.272 | ✅ |
| Kv | 35 rpm/V | 35 | ✅ |
| Back-EMF const | 0.0285 V/rpm | printed "0.0285 **V/krpm**" | ✅ value / ⚠️ unit label |
| R phase-to-phase | 164 mΩ | 164 mΩ (= 0.164 Ω) | ✅ |
| L phase-to-phase | 235 µH | 235 µH | ✅ |
| Rotor inertia | 3377.08 g·cm² | 3377.08 | ✅ |
| Km | 0.67372 Nm/√W | 0.67372 | ✅ |
| Mech time const | 2.18 ms | 2.18 | ✅ |
| Elec time const | 1.4329 ms | 1.4329 | ✅ |
| Insulation class | H | H | ✅ |
| Op temp | −20~50 °C | −20~50 | ✅ |
| Dielectric | 1000 V | 1000V 5mA/2s | ✅ |
| **Back-drive torque** | **9 Nm** | **NOT on live page** | ⚠️ |

Two caveats:
1. **Ke unit label.** The page prints the back-EMF constant as `0.0285 V/krpm`, but
   0.0285 in V/krpm would be physically absurd; the value is really **0.0285 V/rpm**
   (= 28.5 V/krpm), which the internal check confirms (τ_e = L/R = 1.4329 ms and
   Km = Kt/√R = 0.672 both match exactly). Recorded raw = 0.0285, unit = "V/krpm" as
   printed, with the discrepancy noted in the row. The **same V/krpm-that-is-really-V/rpm
   mislabel** appears on **AKA10-9 (0.0167), AKA60-6 (0.0125), GL40 II (0.0115)**.
2. **Back-drive torque 9 Nm** is **not shown on the live AKE90-8 page** (nor on the
   AKE80/AKE60 pages) — it must come from a PDF datasheet. Left blank (not invented);
   flagged here. Everything else on the live page reproduces the datasheet exactly.

The earlier `cubemars_specs.csv` R-column "MΩ" mislabel is confirmed resolved: the live
AKE90-8 page now prints **"Phase-to-Phase Resistance 164 mΩ"** (0.164 Ω), and a separate
row gives insulation resistance 1000V 10 MΩ.

---

## Internal-consistency checks (Kt≈9.5493/Kv, Km≈Kt/√R, τ_e≈L/R)
Computed for every row. **Km≈Kt/√R and τ_e≈L/R hold to <2% for essentially all models**
— i.e. the printed Kt, R, L, Km and electrical time constant are mutually self-consistent.
Genuine failures and their cause:

- **RO40 KV140 Lite — Km printed 0.52 Nm/√W is wrong (~+900%).** Kt/√R = 0.068/√1.7 =
  **0.052**; the printed 0.52 is a missing-decimal typo. All other RO40 values are consistent.
- **AK45-36 V3.0 KV80 — Km printed 0.15 vs Kt/√R = 0.082 (+83%).** Either R (1800 mΩ) is
  overstated or Km (0.15) was carried over from sister AK45/AK60-39 units; the two cannot
  both be right. Flagged; both recorded as printed.
- **AKE60-8 & AK60-6 V3.0 — τ_e off ~39%.** AKE60-8 prints elec-tc 1.7 ms > mech-tc 1.2 ms
  (unusual; τ_e should be the shorter one) while L/R = 1.22 ms; AK60-6 V3 prints elec-tc
  0.69 ms vs L/R = 1.14 ms. Look like mech/elec-tc label swaps or an R/L rounding; recorded
  as printed and flagged.

**Kt ≈ 9.5493/Kv fails systematically (RI motors +26…42%, AK70-10/AK80-8/AK10-9 V2 +24…29%,
AK60-6 V1.1 KV80 −35%, RO100/RO60 +13…15%).** This is **not** a per-model error: CubeMars'
`Kv` (rpm/V) is a **nominal no-load speed rating**, not the strict reciprocal of the measured
`Kt`/`Ke`. Wherever both a measured Kt and R/L exist, the Km and τ_e relations still close,
so Kt itself is trustworthy; only the round-number Kv label is loose. Ke and Kv are likewise
non-reciprocal on these pages (e.g. RI100 Ke 10.47 V/krpm ⇒ 95.5 rpm/V vs printed Kv 105).
Treat CubeMars `Kv` as nominal.

## Per-model gaps (what could not be found)
- **AK80-9 V3, AK70-9 V3, AK60-39 V3, AKH70-48, AKH70-16:** electrical time constant not
  published (mechanical time constant is). AK80-9's printed "mech tc 0.725 ms" numerically
  equals L/R, so it may actually be the electrical constant mislabeled.
- **AK45-36 V3, AK45-10 V3, AK40-10 V3:** no time constants and **no winding type** published.
- **AK60-6 V1.1 KV140:** only the on-page comparison-table mechanical specs; no separate
  electrical constants and no standalone price (page price is the KV80 variant).
- **AKE90-8 / AKE80-8 / AKE60-8 / AKA60-6:** back-drive torque not on page. AKE are QDD
  modules — **no encoder, no driver board** (sold separately) so no communication interface.
- **RI & RO & GL:** back-drive torque not published (frameless/gimbal); slot counts not
  published; IP rating only on GL (all IP45) — GL40 II and GL60 II omit even that.
- **GL60 II KV28:** the odd one out — **no Ke, no Km, no time constants, no winding type,
  no insulation/op-temp** on the page; it prints "Winding Resistance 5.8 Ω / Line Inductance
  6 mH" (recorded 5.8 Ω / 6 mH) and 24N28P (28 pole pairs). Has its own GL-II integrated driver.
- **Model-name KV vs spec-table Kv mismatches** (spec value recorded, title noted):
  GL30 title KV290/spec 255, GL35 KV100/82.5, GL60 KV25/21.5, GL80 KV30/27, GL100 KV10/9.3,
  RO40 KV140/141.
- **Data typos flagged in-row:** RO50 Lite peak current 0.9 A (< 3.4 A rated); RO40 Km 0.52.
- **AK70-9 V3 units anomaly:** page renders R as "475 **Ω**" and L as "408 **mH**" (both
  off by 10³); the published Km 0.23 = Kt/√R only with R = **475 mΩ**, and sister AK models
  use mΩ/µH — recorded R = 0.475 Ω, L = 408 µH with the anomaly noted.

## Out of scope / not captured
Underwater thrusters (SW/DW/W/TW), the AKE/AK/GL-II driver boards, RI-Potting (RI85-PH/RI75-PH),
G-series gimbals, and cables — same exclusions as the first pass.
