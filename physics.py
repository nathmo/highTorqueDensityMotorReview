"""BLDC motor physics: reference-frame normalization + component composition.

All conversions follow Lee et al., "How to Model Brushless Electric Motors for the
Design of Lightweight Robotic Systems" (arXiv:2310.00080), hereafter *the paper*.
Equation numbers below refer to that paper.

Design rules (mirrors the project's data-integrity policy):
  * We convert *raw datasheet values* to a single consistent frame (the q-axis)
    using only the paper's exact, deterministic conversions.
  * When a conversion is under-determined (unknown reference frame or, where it
    matters, unknown winding), we return ``None`` and set a ``*_unresolved``
    flag. We NEVER fabricate a value.

Everything operates on plain dicts / floats so it composes cleanly with pandas
and with hand-written tests. Inputs may be ``None`` or NaN; helpers tolerate both.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Optional

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

SQRT_3_2: float = math.sqrt(1.5)          # √(3/2) ≈ 1.2247  (phase→q factor)
SQRT_1_2: float = math.sqrt(0.5)          # √(1/2) ≈ 0.7071  (wye ll-Kv factor)
RPM_V_TO_KT: float = 60.0 / (2.0 * math.pi)  # 9.5493  Kt[Nm/A] = this / Kv[rpm/V]
RAD_S_PER_RPM: float = 2.0 * math.pi / 60.0

# Accepted reference tags (kept as plain strings so the CSV stays human-editable).
KT_REFS = ("phase_peak", "q", "line_rms", "bus", "output", "unknown")
KV_REFS = ("ll", "phase", "unknown")
KV_UNITS = ("rpm/V", "rad_s/V")
R_REFS = ("phase", "terminal_ll", "unknown")
WINDINGS = ("wye", "delta", "unknown")


# --------------------------------------------------------------------------- #
# Small numeric helpers (None/NaN tolerant)
# --------------------------------------------------------------------------- #

def _num(x) -> Optional[float]:
    """Coerce to float, mapping None / NaN / '' / non-numeric to None."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _norm_tag(x) -> str:
    """Normalize a reference/winding tag to a lowercase string.

    Empty / None / pandas-NaN (whose ``str()`` is ``'nan'``) all map to 'unknown'
    so missing CSV cells never masquerade as a real reference frame.
    """
    if x is None:
        return "unknown"
    s = str(x).strip().lower()
    return s if s and s not in ("nan", "none") else "unknown"


def _pos(x: Optional[float]) -> Optional[float]:
    """Return x only if it is a strictly positive number, else None."""
    return x if (x is not None and x > 0) else None


# --------------------------------------------------------------------------- #
# Frame normalization to the q-axis
# --------------------------------------------------------------------------- #

@dataclass
class Resolved:
    """Result of a frame conversion. ``value is None`` ⇒ under-determined."""
    value: Optional[float] = None
    source: str = ""          # which raw field / path produced it
    note: str = ""            # human-readable explanation (esp. when unresolved)

    @property
    def unresolved(self) -> bool:
        return self.value is None


def kt_phi_to_q(kt_raw: float) -> float:
    """Kt referenced to phase-current amplitude I^φ → q-axis Kt (eq. 55/56)."""
    return SQRT_3_2 * kt_raw


def kt_from_kt(kt_raw, kt_ref, winding) -> Resolved:
    """Normalize a datasheet torque constant to the q-axis frame.

    Deterministic only for ``phase_peak`` and ``q``. ``line_rms``/``bus``/
    ``output``/``unknown`` are left unresolved on purpose — see module docstring.
    """
    val = _pos(_num(kt_raw))
    ref = _norm_tag(kt_ref)
    if val is None:
        return Resolved(None, "Kt", "no raw Kt")
    if ref == "q":
        return Resolved(val, "Kt(q)", "already q-axis")
    if ref == "phase_peak":
        return Resolved(kt_phi_to_q(val), "Kt(phase→q)", "Kt^q = √(3/2)·Kt^φ")
    return Resolved(
        None, "Kt",
        f"Kt reference '{ref}' is not deterministically convertible to q-axis",
    )


def kt_from_kv(kv_raw, kv_unit, kv_ref, winding) -> Resolved:
    """Derive q-axis Kt from a velocity constant Kv (eq. 52/53 + Kt=Kb).

    * phase-referenced Kv → Kt^q = √(3/2)·Kb^φ   (winding-agnostic)
    * line-to-line Kv     → wye: (1/√2)·Kb^ll ; delta: √(3/2)·Kb^ll (winding needed)
    """
    val = _pos(_num(kv_raw))
    unit = _norm_tag(kv_unit)
    ref = _norm_tag(kv_ref)
    wind = _norm_tag(winding)
    if val is None:
        return Resolved(None, "Kv", "no raw Kv")

    # Kv → Kb (V·s/rad), regardless of frame: Kb = 1 / Kv_[rad/s per V].
    if unit in ("rpm/v", "rpm_v", "rpm/V".lower()):
        kv_rads = val * RAD_S_PER_RPM
    elif unit in ("rad_s/v", "rad/s/v", "rad_s_v"):
        kv_rads = val
    else:
        return Resolved(None, "Kv", f"unknown Kv unit '{unit}'")
    kb = 1.0 / kv_rads  # V·s/rad in the *same* frame as the reported Kv

    if ref == "phase":
        return Resolved(SQRT_3_2 * kb, "Kv(phase→q)", "Kt^q = √(3/2)·Kb^φ")
    if ref == "ll":
        if wind == "wye":
            return Resolved(SQRT_1_2 * kb, "Kv(ll,wye→q)", "Kt^q = (1/√2)·Kb^ll")
        if wind == "delta":
            return Resolved(SQRT_3_2 * kb, "Kv(ll,delta→q)", "Kt^q = √(3/2)·Kb^ll")
        return Resolved(
            None, "Kv",
            "line-to-line Kv needs winding (wye/delta) to reach q-axis",
        )
    return Resolved(None, "Kv", f"Kv reference '{ref}' not convertible")


def r_to_phase(r_raw, r_ref, winding) -> Resolved:
    """Normalize a datasheet resistance to *phase* resistance (eq. 50/51)."""
    val = _pos(_num(r_raw))
    ref = _norm_tag(r_ref)
    wind = _norm_tag(winding)
    if val is None:
        return Resolved(None, "R", "no raw R")
    if ref == "phase":
        return Resolved(val, "R(phase)", "already phase")
    if ref in ("terminal_ll", "terminal", "ll"):
        if wind == "wye":
            return Resolved(0.5 * val, "R(ll,wye→phase)", "R^φ = ½·R^ll")
        if wind == "delta":
            return Resolved(1.5 * val, "R(ll,delta→phase)", "R^φ = (3/2)·R^ll")
        return Resolved(
            None, "R", "terminal R needs winding (wye/delta) to reach phase R"
        )
    return Resolved(None, "R", f"R reference '{ref}' not convertible")


def resolve_kt_q(motor: dict) -> Resolved:
    """Best q-axis Kt for a motor row: prefer a direct Kt, fall back to Kv."""
    wind = motor.get("Winding")
    r = kt_from_kt(motor.get("Kt_raw_Nm_per_A"), motor.get("Kt_ref"), wind)
    if not r.unresolved:
        return r
    r2 = kt_from_kv(
        motor.get("Kv_raw"), motor.get("Kv_unit"), motor.get("Kv_ref"), wind
    )
    if not r2.unresolved:
        return r2
    # Surface the more informative of the two failure notes.
    note = r.note if _num(motor.get("Kt_raw_Nm_per_A")) is not None else r2.note
    return Resolved(None, "Kt/Kv", note or "no resolvable Kt or Kv")


# --------------------------------------------------------------------------- #
# Derived motor quantities
# --------------------------------------------------------------------------- #

def motor_constant(kt_q: Optional[float], r_phase: Optional[float]) -> Optional[float]:
    """Motor constant Km = Kt / √R  [Nm/√W] from *already-q-axis* Kt and phase R."""
    kt = _pos(_num(kt_q))
    r = _pos(_num(r_phase))
    if kt is None or r is None:
        return None
    return kt / math.sqrt(r)


def km_framed(kt, kt_ref, r, r_ref, winding=None) -> tuple[Optional[float], str]:
    """Physical motor constant Km = Kt_q/√R_phase [Nm/√W] from *raw* Kt & R in their
    stated frames — using winding only when the frames actually require it.

    Exact identity that unlocks most data: when BOTH Kt and R are line-to-line
    (terminal) quantities, the wye/delta factors cancel, so ``Km = Kt/√R`` with **no
    winding assumption** (verified on CubeMars, whose published Km equals Kt/√R_ll to
    5 digits). Every branch here is an exact conversion — never an assumed frame — so
    this stays within the project's "strict" policy.

    Returns ``(km, method)``; ``km is None`` when the frames can't yield Km without an
    unknown winding, or Kt/R are missing / in an unusable frame (output, bus, …).
    """
    kt = _pos(_num(kt))
    r = _pos(_num(r))
    if kt is None or r is None:
        return None, "missing Kt or R"
    ktr, rr, w = _norm_tag(kt_ref), _norm_tag(r_ref), _norm_tag(winding)
    term = ("terminal_ll", "ll", "line", "terminal")

    if ktr in term and rr in term:  # winding-free exact case
        return kt / math.sqrt(r), "Kt/√R, both line-to-line (winding-free)"

    if ktr in ("q", "rms"):
        kt_q = kt
    elif ktr == "phase_peak":
        kt_q = SQRT_3_2 * kt
    elif ktr in term:
        if w == "delta":
            kt_q = SQRT_3_2 * kt
        elif w == "wye":
            kt_q = SQRT_1_2 * kt
        else:
            return None, "line-to-line Kt needs winding for Km"
    else:
        return None, f"Kt frame '{ktr}' not usable for Km"

    if rr == "phase":
        r_ph = r
    elif rr in term:
        if w == "delta":
            r_ph = 1.5 * r
        elif w == "wye":
            r_ph = 0.5 * r
        else:
            return None, "line-to-line R needs winding for Km"
    else:
        return None, f"R frame '{rr}' not usable for Km"

    return kt_q / math.sqrt(r_ph), "Kt_q/√R_phase"


def thermal_current(
    r_phase: Optional[float],
    r_thermal: Optional[float],
    max_winding_temp: Optional[float],
    ambient_temp: Optional[float] = 25.0,
) -> Optional[float]:
    """Steady-state Joule-limited continuous current I = √(ΔT / (R·R_th))."""
    r = _pos(_num(r_phase))
    rth = _pos(_num(r_thermal))
    tmax = _num(max_winding_temp)
    tamb = _num(ambient_temp)
    if r is None or rth is None or tmax is None:
        return None
    if tamb is None:
        tamb = 25.0
    dt = tmax - tamb
    if dt <= 0:
        return None
    return math.sqrt(dt / (r * rth))


@dataclass
class MotorDerived:
    kt_q: Optional[float] = None            # Nm/A, q-axis
    kt_source: str = ""
    kt_unresolved: bool = True
    kt_note: str = ""
    kb_q: Optional[float] = None            # V·s/rad  (= kt_q in SI)
    kv_q_rpm_per_V: Optional[float] = None  # implied no-load speed constant
    r_phase: Optional[float] = None         # Ω
    r_unresolved: bool = True
    r_note: str = ""
    km: Optional[float] = None              # Nm/√W
    km_method: str = ""                     # how km was obtained (frame path)
    km_per_kg: Optional[float] = None       # Nm/√W/kg
    i_thermal: Optional[float] = None       # A, Joule-limited continuous

    def as_dict(self) -> dict:
        return asdict(self)


def derive_motor(motor: dict) -> MotorDerived:
    """Compute the q-axis / Km stack for one motor row (all live, none written back)."""
    kt = resolve_kt_q(motor)
    r = r_to_phase(motor.get("R_raw_ohm"), motor.get("R_ref"), motor.get("Winding"))

    out = MotorDerived(
        kt_q=kt.value, kt_source=kt.source, kt_unresolved=kt.unresolved, kt_note=kt.note,
        r_phase=r.value, r_unresolved=r.unresolved, r_note=r.note,
    )
    if kt.value is not None:
        out.kb_q = kt.value  # Kt = Kb in SI, consistent frame (eq. 73)
        out.kv_q_rpm_per_V = RPM_V_TO_KT / kt.value
    # Km from raw Kt & R via their frames (handles the winding-free terminal case);
    # fall back to resolved q-axis Kt + phase R when raw Kt is absent (Kv-only rows).
    km, method = km_framed(motor.get("Kt_raw_Nm_per_A"), motor.get("Kt_ref"),
                           motor.get("R_raw_ohm"), motor.get("R_ref"), motor.get("Winding"))
    if km is None and kt.value is not None and r.value is not None:
        km, method = motor_constant(kt.value, r.value), "Kt_q(resolved)/√R_phase"
    out.km, out.km_method = km, method
    mass = _pos(_num(motor.get("Mass_kg")))
    if out.km is not None and mass is not None:
        out.km_per_kg = out.km / mass
    out.i_thermal = thermal_current(
        r.value,
        motor.get("Thermal_Resistance_C_per_W"),
        motor.get("Max_Winding_Temp_C"),
        motor.get("Ambient_ref_C"),
    )
    return out


# --------------------------------------------------------------------------- #
# Datasheet self-consistency: cross-check & deduce
# --------------------------------------------------------------------------- #

def ke_to_kb(ke_raw, ke_unit) -> Optional[float]:
    """Back-EMF constant Ke → Kb [V·s/rad]. Accepts V/rpm (default) or V/krpm."""
    ke = _pos(_num(ke_raw))
    if ke is None:
        return None
    u = _norm_tag(ke_unit)
    per_rpm = ke / 1000.0 if "krpm" in u else ke     # → V per rpm
    return per_rpm * RPM_V_TO_KT                      # V per rpm → V·s/rad


@dataclass
class Check:
    name: str
    predicted: Optional[float]
    stated: Optional[float]
    ok: Optional[bool]           # None ⇒ not enough data to compare
    unit: str = ""
    note: str = ""


def _cmp(name, predicted, stated, unit="", tol=0.03, note="") -> Check:
    pred, st = _num(predicted), _num(stated)
    ok = None
    if pred is not None and st is not None:
        ok = abs(pred) < 1e-12 if st == 0 else abs(pred - st) / abs(st) <= tol
    return Check(name, pred, st, ok, unit, note)


def cross_check_motor(motor: dict) -> list:
    """Return the datasheet self-consistency checks that CAN be evaluated for this
    row. Each relation is independent physics, so agreement builds trust and a lone
    failure flags a bad/oddly-defined value (e.g. τ_m conventions)."""
    kt = _num(motor.get("Kt_raw_Nm_per_A"))
    kv = _num(motor.get("Kv_raw"))
    r = _num(motor.get("R_raw_ohm"))
    l = _num(motor.get("L_raw_H"))
    j = _num(motor.get("Rotor_Inertia_kgm2"))
    kb_from_ke = ke_to_kb(motor.get("Ke_raw"), motor.get("Ke_unit"))
    km_calc, _ = km_framed(kt, motor.get("Kt_ref"), r, motor.get("R_ref"), motor.get("Winding"))
    checks = []
    # Kv/Ke are frequently NOMINAL no-load ratings, not the strict reciprocal of the
    # measured Kt — so these two get a loose tolerance. The R-based relations
    # (Km, τ_e) are the reliable ones and stay tight; they catch real typos.
    if kt and kv:
        checks.append(_cmp("Kt = 9.5493/Kv", RPM_V_TO_KT / kv, kt, "Nm/A", tol=0.15,
                           note="Kv is often a nominal rating, not exactly 1/Kt"))
    if kb_from_ke is not None and kt:
        checks.append(_cmp("Kt = Kb (from Ke)", kb_from_ke, kt, "Nm/A", tol=0.15,
                           note="Ke≈1/Kv; nominal"))
    km_v = _num(motor.get("Km_vendor_Nm_per_sqrtW"))
    if km_calc is not None and km_v is not None:
        checks.append(_cmp("Km = Kt/√R", km_calc, km_v, "Nm/√W", tol=0.03))
    if l and r:
        checks.append(_cmp("τ_e = L/R", l / r * 1000, motor.get("Elec_Time_Const_ms"),
                           "ms", tol=0.05))
    if r and j and kt:
        checks.append(_cmp("τ_m = R·J/Kt²", r * j / (kt * kt) * 1000,
                           motor.get("Mech_Time_Const_ms"), "ms", tol=0.10,
                           note="convention-sensitive; a lone miss here is common"))
    return checks


def classify_kt_frame(kt, current, ratio, torque, eff: float = 0.9) -> tuple[str, str]:
    """Decide whether a published Kt is MOTOR- or OUTPUT-referenced, using the
    vendor's own numbers: a motor Kt satisfies τ ≈ Kt·I·N·η, an output Kt satisfies
    τ ≈ Kt·I. Evidence-based disambiguation (no assumed frame) — this is how we
    confirmed CubeMars Kt is motor-level and SteadyWin's is output-level.

    Returns (``"motor"`` | ``"output"`` | ``"ambiguous"`` | ``"unknown"``, detail).
    """
    kt = _pos(_num(kt))
    i = _pos(_num(current))
    n = _pos(_num(ratio))
    t = _pos(_num(torque))
    if None in (kt, i, n, t):
        return "unknown", "insufficient data (need Kt, current, ratio, torque)"
    out, mot = kt * i, kt * i * n * eff
    e_out, e_mot = abs(out - t) / t, abs(mot - t) / t
    if e_out <= 0.2 and e_out < e_mot:
        return "output", f"Kt·I={out:.3g} ≈ τ={t:.3g}"
    if e_mot <= 0.25 and e_mot < e_out:
        return "motor", f"Kt·I·N·η={mot:.3g} ≈ τ={t:.3g}"
    return "ambiguous", f"Kt·I={out:.3g}, Kt·I·N·η={mot:.3g}, τ={t:.3g}"


def deduce_missing(motor: dict) -> dict:
    """Fill values derivable from other published fields. Returns {field: (value,
    from)}. Never overwrites a present value — only fills genuine blanks."""
    out = {}
    kt = _num(motor.get("Kt_raw_Nm_per_A"))
    kv = _num(motor.get("Kv_raw"))
    r = _num(motor.get("R_raw_ohm"))
    l = _num(motor.get("L_raw_H"))
    if kt and not kv:
        out["Kv_raw"] = (RPM_V_TO_KT / kt, "9.5493/Kt")
    if kv and not kt:
        out["Kt_raw_Nm_per_A"] = (RPM_V_TO_KT / kv, "9.5493/Kv")
    km_calc, method = km_framed(kt, motor.get("Kt_ref"), r, motor.get("R_ref"), motor.get("Winding"))
    if km_calc is not None and _num(motor.get("Km_vendor_Nm_per_sqrtW")) is None:
        out["Km_Nm_per_sqrtW"] = (km_calc, method)
    if l and r and _num(motor.get("Elec_Time_Const_ms")) is None:
        out["Elec_Time_Const_ms"] = (l / r * 1000, "L/R")
    return out


# --------------------------------------------------------------------------- #
# Composition: motor × gearbox × driver → actuator
# --------------------------------------------------------------------------- #

def _min_known(*vals) -> tuple[Optional[float], Optional[int]]:
    """min() over the positive, non-None values; also return the argmin index."""
    best_v: Optional[float] = None
    best_i: Optional[int] = None
    for i, v in enumerate(vals):
        f = _pos(_num(v))
        if f is None:
            continue
        if best_v is None or f < best_v:
            best_v, best_i = f, i
    return best_v, best_i


@dataclass
class Composed:
    # inputs (echoed for provenance)
    motor_id: str = ""
    gearbox_id: str = ""
    driver_id: str = ""
    # motor stack
    kt_q: Optional[float] = None
    km: Optional[float] = None
    kt_unresolved: bool = True
    # currents actually usable
    i_cont: Optional[float] = None
    i_cont_source: str = ""      # which component limited continuous current
    i_peak: Optional[float] = None
    # output mechanics
    ratio: Optional[float] = None
    eff_fwd: Optional[float] = None
    tau_out_cont: Optional[float] = None
    tau_out_cont_bound_by: str = ""   # "motor-thermal" | "driver-current" | "gearbox-rated"
    tau_out_peak: Optional[float] = None
    tau_out_peak_bound_by: str = ""
    omega_out_noload_rpm: Optional[float] = None
    # system
    mass_kg: Optional[float] = None
    price_eur: Optional[float] = None
    nm_per_kg_cont: Optional[float] = None
    nm_per_eur_cont: Optional[float] = None
    notes: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def compose(
    motor: dict,
    gearbox: dict,
    driver: Optional[dict] = None,
    *,
    bus_voltage_V: Optional[float] = None,
    driver_external: bool = True,
) -> Composed:
    """Combine a motor + gearbox (+ optional driver) into a composite actuator.

    Output continuous torque is the *minimum* of the electromagnetic/thermal
    capability and the gearbox's rated output — the binding term is reported so
    the UI can say *why* an actuator is limited where it is.
    """
    driver = driver or {}
    md = derive_motor(motor)
    c = Composed(
        motor_id=str(motor.get("motor_id", "") or ""),
        gearbox_id=str(gearbox.get("gearbox_id", "") or ""),
        driver_id=str(driver.get("driver_id", "") or ""),
        kt_q=md.kt_q, km=md.km, kt_unresolved=md.kt_unresolved,
    )

    N = _pos(_num(gearbox.get("Ratio_num")))
    eff = _pos(_num(gearbox.get("Eff_Fwd")))
    c.ratio, c.eff_fwd = N, eff

    # ---- usable continuous current: min(driver cont, motor thermal, motor cont)
    i_cont, i_src = _min_known(
        driver.get("Cont_Current_A"),
        md.i_thermal,
        motor.get("Cont_Current_A"),
    )
    c.i_cont = i_cont
    c.i_cont_source = ["driver-current", "motor-thermal", "motor-current"][i_src] if i_src is not None else ""

    i_peak, _ = _min_known(driver.get("Peak_Current_A"), motor.get("Peak_Current_A"))
    c.i_peak = i_peak

    # ---- continuous output torque: electromagnetic capability vs gearbox rating
    tau_em_cont = None
    if md.kt_q is not None and i_cont is not None and N is not None:
        e = eff if eff is not None else 1.0
        tau_em_cont = md.kt_q * i_cont * N * e
    gbx_rated = _pos(_num(gearbox.get("Rated_Output_Torque_Nm")))
    tau_c, which = _min_known(tau_em_cont, gbx_rated)
    if tau_c is not None:
        c.tau_out_cont = tau_c
        if which == 0:
            c.tau_out_cont_bound_by = c.i_cont_source or "motor-electromagnetic"
        else:
            c.tau_out_cont_bound_by = "gearbox-rated"

    # ---- peak output torque
    tau_em_peak = None
    if md.kt_q is not None and i_peak is not None and N is not None:
        e = eff if eff is not None else 1.0
        tau_em_peak = md.kt_q * i_peak * N * e
    gbx_peak = _pos(_num(gearbox.get("Peak_Output_Torque_Nm")))
    tau_p, whichp = _min_known(tau_em_peak, gbx_peak)
    if tau_p is not None:
        c.tau_out_peak = tau_p
        c.tau_out_peak_bound_by = "motor-electromagnetic" if whichp == 0 else "gearbox-peak"

    # ---- no-load output speed from bus voltage
    vbus = _pos(_num(bus_voltage_V)) or _pos(_num(driver.get("Bus_V_max"))) \
        or _pos(_num(motor.get("Voltage_rated_V")))
    if md.kb_q is not None and vbus is not None and N is not None:
        omega_motor = vbus / md.kb_q          # rad/s at the motor
        c.omega_out_noload_rpm = (omega_motor / RAD_S_PER_RPM) / N

    # ---- mass / price roll-up
    masses = [motor.get("Mass_kg"), gearbox.get("Mass_kg")]
    if driver_external:
        masses.append(driver.get("Mass_kg"))
    mvals = [m for m in (_num(x) for x in masses) if m is not None]
    c.mass_kg = sum(mvals) if mvals else None

    prices = [_num(motor.get("Price_EUR")), _num(gearbox.get("Price_EUR"))]
    if driver_external:
        prices.append(_num(driver.get("Price_EUR")))
    pvals = [p for p in prices if p is not None]
    c.price_eur = sum(pvals) if pvals else None

    if c.tau_out_cont is not None and c.mass_kg:
        c.nm_per_kg_cont = c.tau_out_cont / c.mass_kg
    if c.tau_out_cont is not None and c.price_eur:
        c.nm_per_eur_cont = c.tau_out_cont / c.price_eur

    if md.kt_unresolved:
        c.notes.append(f"Kt unresolved: {md.kt_note}")
    if eff is None:
        c.notes.append("gearbox forward efficiency unknown — assumed 1.0 for τ")
    return c
