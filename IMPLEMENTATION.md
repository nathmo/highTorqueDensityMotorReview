## The one metric to rule them all: the motor constant `Km`

A permanent-magnet motor's whole electromechanical behavior comes from a tiny
intrinsic set: **Kt = Kb** (torque = back-EMF constant, in SI, one frame), **R**
(phase resistance), **L**, **J**, and the thermal pair **R_th / ΔT**. Everything on
a datasheet is downstream of these.

The single most portable figure of merit is the **motor constant**:

```
Km = Kt / √R = τ / √(P_copper)     [Nm/√W]
```

- **current-invariant** — `τ/√P = Kt·I/√(I²R) = Kt/√R`, independent of operating point;
- **winding-invariant** — rewind n× turns: `Kt∝n`, `R∝n²`, so `Km` is unchanged.
  This is why comparing motors by `Kt` or `Kv` alone is meaningless — only `Km` is honest;
- it sets continuous torque via thermal limits: **`τ_cont = Km·√(ΔT / R_th)`**.

Related identities used throughout: `Kt = Kb`, `Kv = 1/Kb`, and
`Kt[Nm/A] = 9.5493 / Kv[rpm/V]` — all valid **only within one reference frame**.

## Reference frames

The paper's core warning: a `Kt`, `Kv`, or `R` is meaningless without knowing its
**reference frame** (phase φ / line-to-line / q-axis / bus / RMS) and **winding**
(wye/delta). Vendors each pick a different one (paper Table IV: Maxon uses phase
current, T-Motor bus current, Kollmorgen q-axis, Parker RMS…).

**Data convention:** each electrical constant is stored as a **raw value + an
explicit reference tag** (`Kt_raw_Nm_per_A` + `Kt_ref`, `R_raw_ohm` + `R_ref`, …).
The app normalizes everything to the **q-axis** on the fly using the paper's exact
conversions (`Kt^q=√(3/2)·Kt^φ`; wye `R^φ=½R^ll`, delta `R^φ=(3/2)R^ll`; etc.).
When a conversion is under-determined (unknown frame/winding) the value is left
**unresolved and flagged — never guessed**. All derived quantities are computed
live and never written back to the CSVs.

## Data model (four joined CSVs)

| File | One row per | Notes |
|---|---|---|
| [motors.csv](motors.csv) | frameless / standalone motor | intrinsic constants + frame tags; `source_type` = `standalone` / `extracted` / `example` |
| [gearboxes.csv](gearboxes.csv) | reduction stage | ratio, forward/back efficiency, backlash; mostly extracted from actuators |
| [drivers.csv](drivers.csv) | motor controller | continuous/peak current, bus voltage |
| [actuators.csv](actuators.csv) | commercial integrated actuator | published specs + FKs `motor_id`/`gearbox_id`/`driver_id` |

Components can be **standalone** or **extracted** from a commercial actuator
(`parent_actuator_id`). Rows tagged `example` are clearly-labeled synthetic teaching
fixtures (they exercise the Km/thermal/builder paths) and are excluded from
real-product comparisons.

## The builder (composition engine)

Pick a motor + gearbox + driver → a synthetic actuator, overlaid on the commercial
cloud. Output continuous torque is

```
τ_cont = min( Kt^q · I_cont · N · η_fwd ,  gearbox rated ,  driver-limited )
```

and the builder reports **which term binds** (motor-thermal vs gearbox-rated vs
driver-current) — the real reason an actuator is limited where it is, and why
strain-wave actuators show huge peak-over-rated headroom (the gearbox caps the
continuous torque far below the motor's short-burst limit).

The physics lives in [physics.py](physics.py) (pure functions, no Streamlit
dependency); unit tests in [tests/test_physics.py](tests/test_physics.py):

```bash
pytest            # 27 tests: frame conversions, Km invariances, composition, unresolved→None
```

## Reading the torque columns (actuators)

Datasheets use inconsistent wording — don't compare numbers blindly.

- **Rated / nominal torque** — continuous torque at rated speed with a 60 °C rise.
  The only number suitable for sizing against a duty cycle.
- **Peak torque** — short-duration torque for accelerations / start-stop
  (ZeroErr and Maxon HPJ-DT call this *repetitive peak*).
- **Max momentary torque** — emergency one-shot limit; can be ~2× the repetitive
  peak. **Do not design around it.**
- **"Max torque"** (CubeMars AKE, catalog summaries) — ambiguous, usually peak with
  no continuous rating published.

## Illustrative ranking — highest continuous torque density (Nm/kg)

1. MAB MA-p-100-30 — **45.5** (50 Nm cont., 1.1 kg, planetary 30:1)
2. MyActuator EPS-RH-25-100 — **44.6** (108 Nm, 2.42 kg, harmonic 100:1)
3. MyActuator RMD-X15-P20-450 — **41.4** (145 Nm, 3.50 kg, 72 V)
4. Maxon HEJ 90 — **37.5** (75 Nm, 2.00 kg)
5. MyActuator RMD-X12-P20-320 — **35.4** (85 Nm, 2.40 kg)

`Km`-based rankings need phase `R`, which datasheets rarely publish — coverage is
sparse today and the app reports exactly how much resolves. This is the datasheet
gap the paper describes; fill `R_raw_ohm` + `R_ref` (+ `Winding`) on a motor to
unlock its `Km`.

## Model limits (what the physics ignores)

Iron/core losses, magnetic saturation (peak-Kt droop), saliency/reluctance torque,
trapezoidal drive, and temperature drift of `R`/magnets are all omitted. The
intrinsic constants describe the **frameless motor**; a commercial actuator's rated
torque is usually **gearbox-limited**, so motor `Km` and actuator Nm/kg are related
but not the same story.

## Sources

- Soceboz FL102HSV series — guesstimate
- CubeMars — <https://www.cubemars.com/fr>
- RSL-ETH DynaDrive — <https://rsl.ethz.ch/robots-media/actuators/DynaDrives.html>
- MAB Robotics — <https://www.mabrobotics.pl/product-page/ma-h>
- ZeroErr eRob — <https://en.zeroerr.cn/rotary_actuators>
- Maxon HEJ / HPJ-DT — <https://global.maxongroup.com/high-efficiency-joints>
- MyActuator — <https://www.myactuator.com/product>
- Modeling — Lee et al., *How to Model Brushless Electric Motors…*, arXiv:2310.00080

## Supplier data (2026-07)

An 8-agent sweep of **direct-sale** vendors populated the DB: CubeMars, MyActuator,
ZeroErr, MAB, RobStride, SteadyWin, Unitree/mjbots/HEBI, Maxon (drone low-KV motors
held in `research/` for later). Raw findings live in `research/*_specs.csv` (unified
34-column schema) + `research/_consolidated.csv`; datasheets are cached in
`datasheets/<supplier>/`. Every ingested row keeps its `product_url` / datasheet path.
### The winding-free Km unlock

Almost no vendor states the Kt/Kv reference frame, so absolute q-axis Km looks impossible.
But **`Km = Kt/√R` is winding-free whenever Kt and R are *both* line-to-line (terminal)** —
the wye/delta factors provably cancel. This is exact, not an assumption, and it took CubeMars
from 0 → 40 motors with a real, comparable Km. `physics.py` `km_framed()` applies it; the
Motors tab shows the frame path per row. Verified on the CubeMars AKE90-8 sheet, whose
published Km (0.674) equals Kt/√R_ll to 5 digits.

### Datasheet self-consistency validator

`physics.py` `cross_check_motor()` runs independent relations — `Kt=9.5493/Kv`, `Kt=Kb`
(via Ke), `Km=Kt/√R`, `τ_e=L/R`, `τ_m=R·J/Kt²` — and the Motors tab shows a ✓/✗ badge plus
values *deduced* from the rest. On AKE90-8, four agree to 4–5 digits; `τ_m` is the lone
outlier (~3×, convention-dependent). Rich fields (`Ke`, `L`, `J`, time constants, back-drive
torque) now have schema columns; vendor-published Km stays in `Km_vendor_Nm_per_sqrtW`.

## Status / roadmap

Implemented: `kt↔kv` link, `Km = Kt/√R`, per-layer explorers, gear ratio + forward
efficiency in composition, mass & price roll-up, thermal continuous-current limit,
binding-constraint reporting, extracted motor/gearbox split from commercial actuators.

Open: back-drive efficiency `η_back`; efficiency-map (η) plots; resolve the Kt/Kv frame
per vendor (email queries) to unlock `Km` on real motors; second-wave suppliers
(drone low-KV ingest, LKMTech, Faradyi, Dynamixel/Feetech serial-bus servos).
