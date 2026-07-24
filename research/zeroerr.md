# ZeroErr eRob Rotary Actuators — Research Notes

Source of truth: manufacturer site **https://www.zeroerr.com/rotary_actuators**
(the old `en.zeroerr.cn` host 301-redirects to `www.zeroerr.com`).

Data captured: 2026-07-23. Values are RAW datasheet figures. Unknowns left blank.

## Scope covered

Full eRob **I/F (integrated / flat) strain-wave family**, one CSV row per size + ratio:

| Model (URL slug) | Datasheet label | Ratios offered | In existing DB? |
|---|---|---|---|
| eRob70F `erob70f` | 70F (ultra-flat) | 14-50 / 80 / 100 | NEW |
| eRob70i `erob70i` | 70H | 14-50 / 80 / 100 / 120 | partial (50,100) |
| eRob80F `erob80f` | 80F (flat) | 17-50 / 100 | yes |
| eRob80i `erob80i` | 80H | 17-50 / 80 / 100 / 120 | partial (50,100) |
| eRob90i `erob90i` | 90H | 20-50 / 80 / 100 / 120 | partial (50,100) |
| eRob110i `erob110i` | 110H | 25-50 / 80 / 100 / 120 / 160 | partial (50,100,160) |
| eRob142i `erob142i` | 142H | 32-50 / 80 / 100 / 120 / 160 | partial (50,100,160) |
| eRob170i `erob170i` | 170H | 40-50 / 80 / 100 / 120 / 160 | NEW |

**32 actuator rows total.** New vs existing DB: whole **eRob70F** and **eRob170i** sizes, plus the **80:1 and 120:1** ratio variants for 70i/80i/90i/110i/142i, and the 80:1 for 170i — none of which were previously captured. Electrical parameters (Kt, Kv, resistance, pole pairs, motor rated/peak current) are all new — the existing DB had none.

### Not captured (out of scope)
The site also lists an **eRob "T" series** (eRob70T/80T/90T/110T/142T) — a separate torque-sensor / different-configuration line, not the I/F family. Left for a separate pass. Its headline numbers overlap the I series (e.g. eRob110T rated 51 Nm / momentary 242 Nm = eRob110i 25-50).

## Common specs (all I/F models)
- Voltage: **48 V (±10%)**; bus min 44 V / max 55 V (over-volt error >55 V; absolute max 60 V).
- IP **IP54** (asterisked/conditional on site).
- Comms: **EtherCAT / CANopen / Modbus**.
- Output encoder: **19-bit** (90i offers **19/20-bit**); dual absolute encoder (motor + output).
- Integrated: PMSM + strain-wave gear + servo driver + brake option + virtual/output torque estimate.

## Torque wording (4 columns on the site — captured exactly)
1. **Rated torque** → `Rated_Torque_Nm`
2. **Peak torque for start and stop** → `Peak_Torque_Nm`
3. **Permissible maximum momentary torque** → `Max_Momentary_Torque_Nm`
4. *Permissible max. value at average load torque* → recorded in **Notes** (no dedicated column).

`Max_Speed_RPM` holds the site's "Max. output rotational speed" (per ratio). `Rated_Speed_RPM` left blank — the site gives no output rated speed; motor rated speed (3000 rpm, or 3100/3300/2000 depending on model) is in Notes.

## Electrical parameters — source and reference frames
No per-ratio electrical data exists on the product pages or in the one-page "Data Sheet" PDF (which is only a torque-range bar chart). All Kt / Kv / R / current / pole data comes from **eRob Rotary Actuator User Manual V3.42, Table 25-1 "Motor Parameter Sheet"** (p.100) and **Table 3-1 "Rated Current of Each Rotary Actuator Model"** (p.9). Both PDFs downloaded to `datasheets/zeroerr/`.

Reference frames **as stated in the manual**:
- **Torque Constant** = **Nm / A_rms** — this is the **MOTOR** constant, *pre-gear*. The eRob **output** torque constant = `Kt_motor × gear_ratio × η_SWG` (eqn 25.1; η typically 50–70%). So `Kt_raw_Nm_per_A` is the motor value, not the joint output value. Winding config (Y/Δ) is **not stated** → `Winding=unknown`.
- **Voltage Constant (Kv)** = **V/kRPM, line-to-line, ±5%**.
- **Resistance** = **line-to-line, ±10%**.
- `Cont_Current_A` / `Peak_Current_A` = motor **Rated / Maximum** current from Table 25-1. The **module/drive** rated current (Table 3-1, the 0x6075 default, set by module heat capacity — explicitly *uncorrelated with rated torque*) is noted per row where it differs.

### Motor version caveat (flagged per row)
Table 25-1 in manual **V3.42** lags the current hardware for several sizes: product pages now list **70i=V5, 80i=V6, 90i=V6**, but the manual's newest documented motor versions are 70=V4_MC2, 80=V5_MC2, 90=V3_MC2. Reported electrical values are the newest **documented** version; the version used is in `Kt_ref`/Notes. **110i=V6_MC2 matches the current page (723 W).** For **142i** the manual's V3_MC1 (26 A) matches Table 3-1; **170i** version is ambiguous (V3_MC1 Kt 0.153 vs V3_MC2 Kt 0.22 — same 1000 W/10-pole motor as 142i) and is flagged.

Motor pole count: 16-pole (**8 pole-pairs**) for 70F/70i/80F/80i/90i/110i; 10-pole (**5 pole-pairs**) for 142i/170i.

## Pricing (we previously had none)
No prices on ZeroErr's own site. Reseller **AIFITLAB** (aifitlab.com) lists model-level "from" prices (config-dependent: ratio, comm protocol, brake, multiturn/torque-sensor). Converted at **1 USD = 0.876 EUR** (xe.com mid-market, 2026-07-23):

| Model | Reseller "from" (USD) | ≈ EUR |
|---|---|---|
| eRob90i | 1,390 | 1,218 |
| eRob110i | 1,450 (base 1,470) | 1,270 |
| eRob142i | 1,530 (base 1,550) | 1,340 |
| eRob170i | 2,300 (base 2,320) | 2,015 |

No reseller price found for 70F / 70i / 80F / 80i (left blank).

## Files
- `datasheets/zeroerr/eRob_i-type_parameter_sheet.pdf` — official "Data Sheet" (torque-range bar chart only; 1 page).
- `datasheets/zeroerr/eRob_User_Manual_V3.42.pdf` — 145 pp; source of all electrical data (Tables 3-1, 25-1).
- `research/zeroerr_specs.csv` — 32 rows.

---

# Cross-check vs existing data

Existing DB rows (`actuators.csv`, 48 V / IP54 / EtherCAT-CANopen-Modbus) vs values re-extracted from the live site + manual. Format: **rated / peak / max-momentary Nm | out-rpm | power W | weight kg | Ø×L**.

**All 14 existing rows MATCH — no torque, speed, power, weight or dimension discrepancies.**

| Row | Existing (our value) | Re-extracted (this pass) | Verdict |
|---|---|---|---|
| eRob70i 14-50 | 7/23/46 · 60 · 100 · 0.82 · 70×71 | 7/23/46 · 60 · 100 · 0.82 · 70×71 | ✓ match |
| eRob70i 14-100 | 10/36/70 · 30 · 100 · 0.82 · 70×71 | 10/36/70 · 30 · 100 · 0.82 · 70×71 | ✓ match |
| eRob80f 17-50 | 11/23/48 · 60 · 126 · 0.89 · 80×57.5 | 11/23/48 · 60 · 126 · 0.89 · 80×57.5 | ✓ match |
| eRob80f 17-100 | 16/37/71 · 30 · 126 · 0.89 · 80×57.5 | 16/37/71 · 30 · 126 · 0.89 · 80×57.5 | ✓ match |
| eRob80i 17-50 | 21/44/91 · 60 · 126 · 1.03 · 80×64.2 | 21/44/91 · 60 · 126 · 1.03 · 80×64.2 | ✓ match |
| eRob80i 17-100 | 31/70/143 · 30 · 126 · 1.03 · 80×64.2 | 31/70/143 · 30 · 126 · 1.03 · 80×64.2 | ✓ match |
| eRob90i 20-50 | 33/73/127 · 60 · 314 · 1.506 · 90×75.9 | 33/73/127 · 60 · 314 · 1.506 · 90×75.9 | ✓ match |
| eRob90i 20-100 | 52/107/191 · 30 · 314 · 1.506 · 90×75.9 | 52/107/191 · 30 · 314 · 1.506 · 90×75.9 | ✓ match |
| eRob110i 25-50 | 51/127/242 · 60 · 723 · 2.57 · 110×80.2 | 51/127/242 · 60 · 723 · 2.57 · 110×80.2 | ✓ match |
| eRob110i 25-100 | 87/204/369 · 30 · 723 · 2.57 | 87/204/369 · 30 · 723 · 2.57 | ✓ match |
| eRob110i 25-160 | 87/229/408 · 18.75 · 723 · 2.57 | 87/229/408 · 18.75 · 723 · 2.57 | ✓ match |
| eRob142i 32-50 | 99/281/497 · 40 · 1000 · 6.49 · 142×133.9 | 99/281/497 · 40 · 1000 · 6.49 · 142×133.9 | ✓ match |
| eRob142i 32-100 | 178/433/841 · 20 · 1000 · 6.49 | 178/433/841 · 20 · 1000 · 6.49 | ✓ match |
| eRob142i 32-160 | 178/484/892 · 12.5 · 1000 · 6.49 | 178/484/892 · 12.5 · 1000 · 6.49 | ✓ match |

### Soft discrepancies worth a note (not errors in our DB — internal ZeroErr inconsistencies)
1. **Chart-mass vs page-mass.** The "Data Sheet" torque chart lists masses **80H = 1.19 kg** and **90H = 1.75 kg**, but the product pages (and our DB) give **80i = 1.03 kg** and **90i = 1.506 kg** (no brake; 90i with-brake = 1.639 kg). Cause: chart likely a different revision/with-brake. We keep the product-page values → **our DB is right.**
2. **80i motor power.** Product page and our DB say **126 W**; manual Table 25-1 says the 80H motor (V5_MC2) DC-link rated power is **146 W** (older V3_MC1 = 200 W). Definition mismatch (nameplate vs DC-link). Kept page value; noted in row.
3. **90i motor power.** Page/DB = **314 W (V6)**; manual's newest documented (V3_MC2) = **293 W**. Version lag. Kept page value.
4. **eRob80i 17-120 max-momentary = 112 Nm** — LOWER than 17-100's 143 Nm. Looks odd but is what the page shows; captured raw and flagged (not our error; new ratio anyway).
5. **Module vs motor rated current** differ slightly by design (e.g. 80i: Table 3-1 module 4.1 A vs Table 25-1 motor 3.4 A; 110i: 18.6 vs 18.9). Both recorded (column = motor; module in Notes).

No changes needed to existing `actuators.csv` / `gearboxes.csv` rows.
