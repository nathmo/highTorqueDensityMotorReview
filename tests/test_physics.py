"""Unit tests for the BLDC physics / composition engine.

Run: ``pytest`` from the repo root.
"""

import math

import pytest

import physics as ph


def close(a, b, rel=1e-6):
    return a is not None and b is not None and math.isclose(a, b, rel_tol=rel, abs_tol=1e-12)


# --------------------------------------------------------------------------- #
# Kt frame normalization
# --------------------------------------------------------------------------- #

def test_kt_q_passthrough():
    r = ph.kt_from_kt(0.5, "q", "wye")
    assert not r.unresolved and close(r.value, 0.5)


def test_kt_phase_to_q():
    r = ph.kt_from_kt(0.5, "phase_peak", "wye")
    assert close(r.value, math.sqrt(1.5) * 0.5)  # √(3/2)·Kt^φ


@pytest.mark.parametrize("ref", ["bus", "line_rms", "output", "unknown", ""])
def test_kt_unresolved_refs_return_none(ref):
    """Under-determined frames must NOT be silently converted — no invented value."""
    r = ph.kt_from_kt(0.5, ref, "wye")
    assert r.unresolved and r.value is None


# --------------------------------------------------------------------------- #
# Kv → Kt
# --------------------------------------------------------------------------- #

def test_kv_phase_to_kt_q():
    # Kv=100 rpm/V, phase-referenced. Kb^φ = 1/(100·2π/60); Kt^q = √(3/2)·Kb^φ.
    kb_phi = 1.0 / (100.0 * 2 * math.pi / 60.0)
    r = ph.kt_from_kv(100, "rpm/V", "phase", "unknown")
    assert close(r.value, math.sqrt(1.5) * kb_phi)


def test_kv_ll_wye_vs_delta():
    kb_ll = 1.0 / (100.0 * 2 * math.pi / 60.0)
    wye = ph.kt_from_kv(100, "rpm/V", "ll", "wye")
    delta = ph.kt_from_kv(100, "rpm/V", "ll", "delta")
    assert close(wye.value, math.sqrt(0.5) * kb_ll)
    assert close(delta.value, math.sqrt(1.5) * kb_ll)


def test_kv_ll_unknown_winding_unresolved():
    r = ph.kt_from_kv(100, "rpm/V", "ll", "unknown")
    assert r.unresolved and r.value is None


def test_kv_unknown_unit_unresolved():
    r = ph.kt_from_kv(100, "furlongs/V", "phase", "wye")
    assert r.unresolved


# --------------------------------------------------------------------------- #
# Resistance frame normalization
# --------------------------------------------------------------------------- #

def test_r_phase_passthrough():
    assert close(ph.r_to_phase(0.1, "phase", "wye").value, 0.1)


def test_r_terminal_wye_delta():
    assert close(ph.r_to_phase(0.2, "terminal_ll", "wye").value, 0.1)   # ½·R^ll
    assert close(ph.r_to_phase(0.2, "terminal_ll", "delta").value, 0.3)  # (3/2)·R^ll


def test_r_terminal_unknown_winding_unresolved():
    assert ph.r_to_phase(0.2, "terminal_ll", "unknown").unresolved


# --------------------------------------------------------------------------- #
# Km and its invariances
# --------------------------------------------------------------------------- #

def test_km_formula():
    assert close(ph.motor_constant(0.6, 0.25), 0.6 / 0.5)  # Kt/√R


def test_km_winding_invariance():
    """Rewind n× turns: Kt∝n, R∝n² ⇒ Km = Kt/√R is unchanged."""
    base = ph.motor_constant(0.5, 0.1)
    rewound = ph.motor_constant(0.5 * 3, 0.1 * 9)  # n = 3
    assert close(base, rewound)


def test_km_current_invariance_conceptual():
    # τ/√P = Kt·I / √(I²R) = Kt/√R for any I. Check at two currents.
    kt, r = 0.4, 0.2
    for i in (1.0, 37.0):
        tau, p = kt * i, i * i * r
        assert close(tau / math.sqrt(p), ph.motor_constant(kt, r))


def test_km_none_without_r():
    assert ph.motor_constant(0.5, None) is None
    assert ph.motor_constant(None, 0.1) is None


# --------------------------------------------------------------------------- #
# Thermal current
# --------------------------------------------------------------------------- #

def test_thermal_current():
    # ΔT=100°C, R=0.1Ω, R_th=1.0°C/W ⇒ I=√(100/(0.1·1))=√1000.
    i = ph.thermal_current(0.1, 1.0, 125.0, 25.0)
    assert close(i, math.sqrt(1000.0))


def test_thermal_current_needs_all_inputs():
    assert ph.thermal_current(0.1, None, 125.0) is None
    assert ph.thermal_current(None, 1.0, 125.0) is None


# --------------------------------------------------------------------------- #
# derive_motor
# --------------------------------------------------------------------------- #

def test_derive_motor_full_stack():
    motor = {
        "Kt_raw_Nm_per_A": 0.5, "Kt_ref": "phase_peak", "Winding": "wye",
        "R_raw_ohm": 0.2, "R_ref": "phase",
        "Mass_kg": 0.5,
        "Thermal_Resistance_C_per_W": 1.0, "Max_Winding_Temp_C": 125, "Ambient_ref_C": 25,
    }
    d = ph.derive_motor(motor)
    kt_q = math.sqrt(1.5) * 0.5
    assert close(d.kt_q, kt_q)
    assert close(d.kb_q, kt_q)                      # Kt = Kb (SI)
    assert close(d.kv_q_rpm_per_V, ph.RPM_V_TO_KT / kt_q)  # 9.5493 / Kt identity
    assert close(d.km, kt_q / math.sqrt(0.2))
    assert close(d.km_per_kg, (kt_q / math.sqrt(0.2)) / 0.5)
    assert close(d.i_thermal, math.sqrt((125 - 25) / (0.2 * 1.0)))


def test_derive_motor_unresolved_is_honest():
    motor = {"Kt_raw_Nm_per_A": 2.1, "Kt_ref": "output"}  # vendor output-referenced
    d = ph.derive_motor(motor)
    assert d.kt_unresolved and d.kt_q is None and d.km is None


# --------------------------------------------------------------------------- #
# compose: binding constraint
# --------------------------------------------------------------------------- #

MOTOR = {"motor_id": "m", "Kt_raw_Nm_per_A": 0.1, "Kt_ref": "q", "Peak_Current_A": 30}
DRIVER = {"driver_id": "d", "Cont_Current_A": 10, "Peak_Current_A": 30, "Bus_V_max": 48}


def test_compose_bound_by_driver_current():
    gbx = {"gearbox_id": "g", "Ratio_num": 20, "Eff_Fwd": 0.9,
           "Rated_Output_Torque_Nm": 1000, "Peak_Output_Torque_Nm": 1000}
    c = ph.compose(MOTOR, gbx, DRIVER)
    assert close(c.tau_out_cont, 0.1 * 10 * 20 * 0.9)  # 18 Nm
    assert c.tau_out_cont_bound_by == "driver-current"


def test_compose_bound_by_gearbox_rating():
    gbx = {"gearbox_id": "g", "Ratio_num": 20, "Eff_Fwd": 0.9,
           "Rated_Output_Torque_Nm": 10, "Peak_Output_Torque_Nm": 1000}
    c = ph.compose(MOTOR, gbx, DRIVER)
    assert close(c.tau_out_cont, 10.0)
    assert c.tau_out_cont_bound_by == "gearbox-rated"


def test_compose_noload_speed():
    gbx = {"gearbox_id": "g", "Ratio_num": 20, "Eff_Fwd": 0.9,
           "Rated_Output_Torque_Nm": 1000}
    c = ph.compose(MOTOR, gbx, DRIVER)
    omega_motor = 48 / 0.1                      # rad/s  (Kb=0.1)
    assert close(c.omega_out_noload_rpm, (omega_motor / ph.RAD_S_PER_RPM) / 20)


def test_compose_mass_rollup():
    m = dict(MOTOR, Mass_kg=0.3)
    g = {"gearbox_id": "g", "Ratio_num": 20, "Mass_kg": 0.5}
    d = dict(DRIVER, Mass_kg=0.2)
    c = ph.compose(m, g, d, driver_external=True)
    assert close(c.mass_kg, 1.0)
    c2 = ph.compose(m, g, d, driver_external=False)
    assert close(c2.mass_kg, 0.8)  # driver mass excluded when integrated


def test_compose_unresolved_kt_yields_no_torque_but_still_returns():
    motor = {"motor_id": "m", "Kt_ref": "unknown", "Kt_raw_Nm_per_A": 2.1}
    gbx = {"gearbox_id": "g", "Ratio_num": 20, "Eff_Fwd": 0.9}
    c = ph.compose(motor, gbx, DRIVER)
    assert c.kt_unresolved and c.tau_out_cont is None
    assert any("Kt unresolved" in n for n in c.notes)


# --------------------------------------------------------------------------- #
# km_framed: winding-free terminal path + frame handling
# --------------------------------------------------------------------------- #

def test_km_framed_both_terminal_is_winding_free():
    v_none, m = ph.km_framed(0.272, "terminal_ll", 0.164, "terminal_ll")
    assert close(v_none, 0.272 / math.sqrt(0.164)) and "line-to-line" in m
    v_delta = ph.km_framed(0.272, "terminal_ll", 0.164, "terminal_ll", "delta")[0]
    v_wye = ph.km_framed(0.272, "terminal_ll", 0.164, "terminal_ll", "wye")[0]
    assert close(v_delta, v_none) and close(v_wye, v_none)  # winding cancels


def test_km_framed_phase_and_q():
    assert close(ph.km_framed(0.5, "phase_peak", 0.2, "phase")[0], math.sqrt(1.5) * 0.5 / math.sqrt(0.2))
    assert close(ph.km_framed(0.6, "q", 0.25, "phase")[0], 0.6 / 0.5)


def test_km_framed_needs_winding_or_frame():
    assert ph.km_framed(0.5, "terminal_ll", 0.2, "phase", "unknown")[0] is None  # mixed, no winding
    assert ph.km_framed(2.1, "output", 0.1, "phase")[0] is None                  # output Kt unusable


def test_ke_to_kb_units():
    assert close(ph.ke_to_kb(0.0285, "V/rpm"), 0.0285 * ph.RPM_V_TO_KT)
    assert close(ph.ke_to_kb(28.5, "V/krpm"), 28.5 / 1000 * ph.RPM_V_TO_KT)


# --------------------------------------------------------------------------- #
# derive_motor + cross-check on the real CubeMars AKE90-8 datasheet
# --------------------------------------------------------------------------- #

AKE90 = {
    "Kt_raw_Nm_per_A": 0.27284, "Kt_ref": "terminal_ll",
    "Kv_raw": 35, "Kv_unit": "rpm/V", "Kv_ref": "ll",
    "Ke_raw": 0.0285, "Ke_unit": "V/rpm",
    "R_raw_ohm": 0.164, "R_ref": "terminal_ll",
    "L_raw_H": 235e-6, "Rotor_Inertia_kgm2": 3377.08e-7,
    "Km_vendor_Nm_per_sqrtW": 0.67372,
    "Elec_Time_Const_ms": 1.4329, "Mech_Time_Const_ms": 2.18,
    "Winding": "delta",
}


def test_derive_motor_km_unlocks_when_kt_q_does_not():
    """Terminal Kt+R gives Km even with NO winding, where absolute q-axis Kt can't."""
    terminal_only = {"Kt_raw_Nm_per_A": 0.27284, "Kt_ref": "terminal_ll",
                     "R_raw_ohm": 0.164, "R_ref": "terminal_ll"}  # no Kv, no winding
    d = ph.derive_motor(terminal_only)
    assert d.kt_q is None                      # terminal Kt + no winding → no q-axis Kt
    assert d.km is not None                    # …but Km still resolves (winding-free)
    assert close(d.km, 0.27284 / math.sqrt(0.164), rel=1e-3)
    assert "line-to-line" in d.km_method


def test_cross_check_ake90():
    checks = {c.name: c for c in ph.cross_check_motor(AKE90)}
    assert checks["Kt = 9.5493/Kv"].ok
    assert checks["Kt = Kb (from Ke)"].ok
    assert checks["Km = Kt/√R"].ok
    assert checks["τ_e = L/R"].ok
    assert checks["τ_m = R·J/Kt²"].ok is False   # the known outlier


def test_classify_kt_frame():
    # CubeMars AKE90-8: Kt=0.272, I_peak=72, ratio 8, peak τ=170 → motor Kt
    assert ph.classify_kt_frame(0.272, 72, 8, 170)[0] == "motor"
    # SteadyWin GIM6010-8: Kt=0.47, I_peak=23.4, ratio 8, peak τ=11 → output Kt
    assert ph.classify_kt_frame(0.47, 23.4, 8, 11)[0] == "output"
    assert ph.classify_kt_frame(None, 1, 1, 1)[0] == "unknown"


def test_deduce_missing_fills_from_relations():
    partial = {"Kt_raw_Nm_per_A": 0.27284, "Kt_ref": "terminal_ll",
               "R_raw_ohm": 0.164, "R_ref": "terminal_ll"}
    d = ph.deduce_missing(partial)
    assert "Kv_raw" in d and close(d["Kv_raw"][0], ph.RPM_V_TO_KT / 0.27284)
    assert "Km_Nm_per_sqrtW" in d
