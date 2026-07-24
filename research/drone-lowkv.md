# Drone / gimbal BLDC motors for robotics — research notes

Bare motors (`layer=motor`) sold direct that are **robotics-suitable**: low-KV,
high-torque, or gimbal-pancake frameless/outrunner types. Data is RAW datasheet
values only; unknowns left blank. Specs live in `drone-lowkv_specs.csv`
(19 motors: 12 T-Motor, 5 iPower, 2 MAD).

## KV cutoff applied

**Inclusion rule:** KV ≤ ~200 rpm/V **OR** the motor is a gimbal/direct-drive
pancake **OR** a large-format high-torque outrunner marketed for heavy lift /
direct drive. Small high-KV racing/FPV motors (T-Motor F/R-series, SunnySky X/R
2204–2216, etc.) were **excluded**. Every captured motor is ≤ 130 rpm/V; the
gimbal motors are 26–68 rpm/V (many don't publish KV at all).

## KV reference convention

No vendor here states line-to-line vs phase for KV, so **every row is
`Kv_ref=unknown`**. Drone motors quote KV line-to-line by convention but rarely
say so — do not assume `ll`. Same for resistance: T-Motor/iPower call it
"internal resistance" with no frame stated → **`R_ref=unknown`** (very likely a
phase-to-phase / line-to-line measurement, but unconfirmed).

## Which brands publish R and pole data (needed for Km)

| Brand | KV | Phase R | Poles (NxP) | Weight | Winding | Km-ready? |
|---|---|---|---|---|---|---|
| **T-Motor** (U / MN / GB) | yes | **yes** ("internal resistance") | **yes** (36N42P, 12N14P) | yes | no | R + poles present; only winding (wye/delta) missing |
| **iPower** (GBM / GM) | sometimes | **yes** | **yes** (24N22P, 12N14P, 36N42P) | yes | **GBM5208H states "Star"=wye** | best-documented; one row even gives L (1.75 mH) |
| **MAD Components** (M40/M50) | yes | **no** | yes (36N30P) | yes (M40 only) | no | R never published → no Km |
| SunnySky | yes | rarely | rarely | yes | no | not captured (see below) |
| QS Motor | yes | rarely | — | yes | no | not captured (see below) |

**Takeaway for Km:** T-Motor and iPower are the two brands that give phase R +
pole count. Once a winding assumption (wye/delta) and Kv frame are resolved,
their `Km = Kt/√R` becomes computable. MAD publishes torque/thrust/power but no
R, so Km stays blocked. iPower is the single best source (R + poles + stator
size + winding on GBM5208H + inductance on GBM4008H).

## Per-brand summary

### T-Motor — tmotor.com (12 rows, highest-value)
- **U-series (U8/U10/U12/U13 II):** low-KV efficiency/power outrunners, all
  **36N42P (21 pole pairs)**, all publish internal resistance (18–170 mΩ) and
  weight. KV 65–130. Peak current/power are stated as **180 s ratings**, not
  continuous — recorded as `Peak_Current_A`, continuous left blank. No torque
  ratings (thrust only), except U13 II KV130 lists 10 Nm at its 100 % throttle
  operating point (an operating-point value, not a rated spec).
- **Antigravity MN-series (MN8017 KV120, MN1005 V2 KV90):** pancake outrunners,
  also 36N42P, R published (45 / 168 mΩ).
- **GB gimbal (GB54-1 KV33, GB54-2 KV26, GB85-1):** hollow-shaft gimbal
  outrunners; R published (13–15.6 Ω); "max torque" values are ambiguous
  holding/stall figures. GB54-2 R left blank (reseller "150 Ω" looks like a
  typo for ~15 Ω). GB85-1 KV not published.
- Prices are on the store product pages (USD); no downloadable PDF datasheets —
  specs are HTML tables on each product page.

### iPower Motor — ipowermotor.com (5 rows, best electrical documentation)
- **GBM / GM gimbal outrunners.** Publish internal resistance, NxP config,
  stator OD×thickness, weight, winding turns. **GBM5208H-180T explicitly states
  "Star style" winding = wye** — the only confirmed winding in the whole set.
  GBM4008H-150T gives KV 68, R 6.7 Ω, and static inductance 1.75 mH.
- Most GBM models are specified by winding **turns (T)**, not KV — so KV is
  often blank. GM5208-12 gives no-load 456–504 rpm @ 20 V (≈23–25 rpm/V) but
  isn't vendor-labelled as KV, so `Kv_raw` left blank.

### MAD Components — mad-motor.com (2 rows, big low-KV)
- **M40C30 / M50C35:** very large heavy-lift / manned-drone / paramotor
  outrunners. Low KV (34–80). Publish **max power** (20–25 kW), **max torque**
  (48 / 60 Nm), thrust, and **36N30P** config; M40 gives weight 3.46 kg and
  151.4×81 mm. **No phase resistance and no per-KV electrical breakdown** —
  same frame is offered in KV 10/35/43/50/55/62/80, so one representative row
  per model rather than fabricated per-KV rows.

### SunnySky — NOT captured (out of scope after cutoff)
- The V "high-efficiency" multirotor line (V4014, V5208, V5210…) bottoms out
  around **KV 320–400** — above the ~200 cutoff. Their low-KV offerings are
  small gimbal motors (GB2208, R≈0.14 Ω) aimed at GoPro-class cameras, too
  small to be robotics direct-drive. No SunnySky motor met the inclusion rule.

### QS Motor — NOT captured (needs a dedicated pass)
- qsmotor.com is dominated by e-bike/scooter **hub motors** and mid-drives.
  Several are genuinely low-KV / high-torque and some robot projects use them,
  but the public specs are vehicle-oriented (rated for hub geometry) and I did
  not find clean bare-motor KV/R/pole datasheets in this pass. Flagged as a
  candidate for a follow-up dig rather than recording uncertain values.

## Datasheets

No vendor here publishes a downloadable PDF datasheet for these motors — specs
are HTML tables on the product pages. A robotshop CDN PDF for GB54-1 exists but
is bot-blocked (returns an HTML block page), so `datasheet_local` is blank for
every row and the product/spec URL is kept in `product_url` + `Source`.
`datasheets/drone-lowkv/` was created but holds no files.

## U8 KV100 cross-check (vs our reference row)

Our DB `tmotor-u8-kv100`: Kv=100 rpm/V, treated line-to-line, **delta assumed**
(per Lee et al. 2023 App. F worked example, *not* confirmed by T-Motor), no R.

Current published product **U8 II KV100** (store.tmotor.com/goods-561):

| Field | Published | Our DB | Match? |
|---|---|---|---|
| KV | **100 rpm/V** | 100 | ✅ matches |
| Kv frame | not stated | assumed `ll` | ⚠️ vendor never says line-to-line |
| Phase R | **170 ± 5 mΩ** | (blank) | 🆕 fills a gap — DB had no R |
| Poles | **36N42P → 21 pole pairs** | (blank) | 🆕 new data |
| Weight | **272 g** | (blank) | 🆕 new data |
| Winding | **not stated by T-Motor** | delta (assumed) | ⚠️ delta is unconfirmed |

**Verdict:** our KV=100 matches T-Motor's published value. The **delta winding
and line-to-line frame are our assumptions, not vendor-stated.** New from this
pass: R ≈ 0.170 Ω and 21 pole pairs — enough to compute Km for the U8 *once a
winding is chosen* (T-Motor still doesn't disclose wye/delta). Note the sibling
U8 II Pro / U8 II Lite KV100 quote a lower 134–141 mΩ, so R depends on the exact
U8 variant; the original paper's U8 may differ slightly from today's U8 II.
