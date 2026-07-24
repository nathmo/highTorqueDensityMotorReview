# MAB Robotics — direct-sale product specs

**Manufacturer:** MAB Robotics, Poznań, Poland (EU). Site: https://www.mabrobotics.pl — sells direct with € prices listed on-page.
**Captured:** 2026-07-23. Source data file: `research/mab-robotics_specs.csv` (13 rows).

## Summary

MAB's catalogue is organised in two layers:

- **MD-series motor controllers (drivers).** The **MD80 v3.0** is a bare, highly-integrated brushless
  motor *controller* (a ~55 mm disc PCB, 15 g), **not a motor**. It has up to 48 V DC, 80 A peak, FDCAN
  up to 8 Mbps, an onboard 14-bit absolute encoder, and aux connectors for external MAB ring encoders /
  RS422 / brake. Variants: FDCAN (**€220**), CANopen (**€220**), 60 VDC (**€269**), 60 VDC CANopen (**€269**).
  The smaller **MD20 v1.0** is up to 48 V / 20 A / Ø35 mm / 6 g (**€169**).
  None of these publish Kt/Kv/R/pole-pairs — those belong to whatever motor you bolt them to.
- **MA-series integrated actuators** = a frameless BLDC + reducer + MD-series driver in one IP66 housing.
  - **MA-H** harmonic (Ø73×62, 0.54 kg, €1609) — configurable 50:1/80:1/100:1.
  - **MA-hs-h-IP66** hollow-shaft harmonic (Ø102×91, 1.25 kg, from €2599) — 28/60 Nm, 90 rpm, 50:1.
  - **MA-p-100-IP66** planetary 9:1 (Ø103×79.6, 1.1 kg, €1559) — KV60 and KV100 winding options.
  - **MA-p-100-30** planetary 30:1 (Ø98×67, 1.1 kg, €897.56) — 50/150 Nm.
  - Smaller planetaries found beyond scope: **MA-p-45-10** (€303.41), **MA-p-45-36** (€357.26),
    **MA-p-40-10** (€279.69).

**Torque wording:** every MA spec is stated as "X/Y Nm (rated / peak)". MA-H is stated only as a
combined range "4–151 Nm (rated/peak)" and "35–100 RPM" across its three gear ratios — no per-ratio split
is published. No **momentary** torque figure is published for any product.

**Electrical constants:** MAB does **not** publish Kt, phase resistance, inductance, or pole-pair counts
for any product. The only motor-electrical hint is the MA-p-100 **KV60 / KV100** winding names, which
imply motor Kv ≈ 60 / 100 rpm/V (reference frame + winding topology unstated → `Kv_ref=unknown`).

**Datasheets / PDFs:** MAB publishes **no downloadable PDF datasheets**. Product pages list "Additional
documents: 3D model, MD-series motor controller documentation" (the MD docs are an online manual, not a
per-product PDF). `datasheets/mab-robotics/` was created but is **empty**; `datasheet_url` / `datasheet_local`
are blank for all rows. Specs above were read from the live product pages' embedded data.

**Rated power (W):** not published on any current product page. The pre-existing DB carried 250 W (MA-hs-h)
and 105 W (MA-H); these could not be re-verified and are left blank here.

### Fetch notes (method / caveats)
- Product pages are a Wix SPA behind bot protection. `curl` returns the full server-rendered product JSON
  on ~1 of N tries (retry loop used); `WebFetch` 404s on `/product-page/*` SPA routes. Prices were
  cross-confirmed against the pages' schema.org `Offer` / catalog `ItemList` JSON-LD (the machine-readable
  price Google Shopping reads).
- **MD80 v3.0 60VDC** product page never rendered for curl during this session; its 60 V/80 A/Ø55/16 g
  specs come from the MD-series overview page and its **€269** price from the schema.org catalog Offer.
- **MA-hs-h-IP66** real slug is `ma-hs-ip66` (the guessed `ma-hs-h-ip66` 404s).

## Cross-check vs existing data

Existing rows are in `actuators.csv`. Findings:

| Existing row | Field | Our value (our DB) | Source value (mabrobotics.pl 2026-07-23) | Verdict |
|---|---|---|---|---|
| MA-hs-h-IP66 | torque / speed / mass / size / IP / gear | 28/60 Nm, 90 rpm, 1.25 kg, 102×91, IP66, harmonic 50:1 | **identical** | ✅ match |
| MA-hs-h-IP66 | price | €2599 | base config **€2599**; also €2969 / €3299; schema.org headline €3299 | ⚠️ €2599 is the valid *base* price, still listed. Page default / JSON-LD now shows €3299. Recommend noting the €2599–€3299 config range. |
| MA-hs-h-IP66 | power | 250 W | **not published** on page | ⚠️ unverifiable — leave blank or mark source-unknown |
| MA-hs-h-IP66 | encoder | "Dual 17-bit" | "17-bit absolute encoders on motor side and output shaft" | ✅ match |
| MA-H | torque / speed / gear | **15/32 Nm, 66 rpm, 50:1** | page gives only a **range**: 4–151 Nm (rated/peak), 35–100 rpm, across **50:1/80:1/100:1** | ❌ mismatch/unverifiable. The current public page does NOT publish a single 15/32 Nm @ 66 rpm @ 50:1 config. Our numbers are plausibly an older/specific-config datasheet but cannot be confirmed. Flag for review. |
| MA-H | price / mass / size / IP | €1609, 0.54 kg, 73×62, IP66 | **identical** | ✅ match |
| MA-H | power | 105 W | **not published** | ⚠️ unverifiable |
| MA-p-100-IP66 (KV60) | 18/48 Nm, 228 rpm, 9:1, 1.1 kg, 103×79.6, €1559 | **identical** | ✅ match |
| MA-p-100-IP66 (KV100) | 15/38 Nm, 421 rpm, 9:1, 1.1 kg, 103×79.6, €1559 | **identical** | ✅ match |
| MA-p-100-30 | 50/150 Nm, 96 rpm, 30:1, 1.1 kg, 98×67, €897.56 | **identical** (IP correctly blank — page states none) | ✅ match |

### Other flags
- **MD80 is mis-scoped as a "frameless BLDC motor."** It is a bare motor *controller* (driver). It has no
  motor Kt/Kv/R/pole-pairs. Recorded here as `layer=driver`. MAB's actual frameless motors are separate
  series (Ri / Ro / R / G / GL torque & gimbal motors) not covered by the original scope.
- **MD80 price ambiguity:** the product page shows both `161,11 €` and `220,00 €`; the schema.org Offer and
  category listing both say **220**, so €220 is recorded. The 161,11 € tile also appears on every actuator
  page (a site-wide related item), so it is treated as noise, not the MD80 price.
- **New direct-sale products found** (not in existing DB): MD80 CANopen / 60VDC / 60VDC-CANopen, MD20 v1.0
  (+CANopen), MA-p-40-10, MA-p-45-10, MA-p-45-36 (all captured here), plus — not captured in detail —
  MA-p-60-IP66, MA-p-80-IP66, and MA-D-HS-gl30/35/40/60/80/100 direct-drive hollow-shaft gimbal actuators
  (€424–493 range in JSON-LD).
