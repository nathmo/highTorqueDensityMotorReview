"""Interactive explorer for the component-layered motor dataset.

Four layers, joined at runtime:
  motors.csv     — frameless / standalone motors (intrinsic constants)
  gearboxes.csv  — reduction stages (ratio, efficiency, backlash)
  drivers.csv    — motor controllers (current / voltage limits)
  actuators.csv  — commercial integrated actuators + FKs to their components

The physics (frame normalization to q-axis, Km, composition) lives in physics.py.
Derived quantities are computed live and never written back to the CSVs.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import physics as ph

HERE = Path(__file__).parent

st.set_page_config(
    page_title="Motor / Gearbox / Driver / Actuator Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
def _first_number(value) -> float | None:
    if pd.isna(value):
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else None


def _max_number(value) -> float | None:
    """For ranges like '12-19' or '12-48' take the upper bound."""
    if pd.isna(value):
        return None
    nums = re.findall(r"\d+(?:\.\d+)?", str(value))
    return max(map(float, nums)) if nums else None


def _classify_reducer(raw: str) -> str:
    if pd.isna(raw):
        return "unknown"
    text = str(raw).lower()
    if "none" in text or "frameless" in text:
        return "direct / frameless"
    if "strain wave" in text or "harmonic" in text:
        return "strain wave / harmonic"
    if "planetary" in text:
        return "planetary"
    if "integrated" in text:
        return "integrated (unspecified)"
    return raw


def _to_num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #
def _ragged_rows(path: Path) -> list[tuple[int, int, int]]:
    """Return (line_no, field_count, expected) for rows that don't match the header."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            return []
        width = len(header)
        return [
            (i, len(row), width)
            for i, row in enumerate(reader, start=2)
            if row and len(row) != width
        ]


def _read_csv(name: str) -> pd.DataFrame:
    """Read a dataset CSV, reporting tokenizer errors as readable app content.

    A stray comma in an unquoted free-text column (Notes, Source, ...) makes
    pandas raise a bare ParserError, whose message Streamlit Cloud redacts.
    Pinpoint the offending lines and render them instead of crashing blind.
    """
    path = HERE / name
    try:
        return pd.read_csv(path)
    except pd.errors.ParserError:
        detail = "; ".join(
            f"line {line} has {got} fields, expected {want}"
            for line, got, want in _ragged_rows(path)
        )
        st.error(
            f"`{name}` could not be parsed: {detail or 'malformed CSV'}. "
            "A comma inside an unquoted field is the usual cause — wrap the "
            "value in double quotes."
        )
        st.stop()


ESTIMATION_PAIRS = [
    ("Rated_Torque_Nm_num", "Peak_Torque_Nm_num"),
    ("Peak_Torque_Nm_num", "Max_Momentary_Torque_Nm_num"),
    ("Rated_Speed_RPM_num", "Max_Speed_RPM_num"),
]


@st.cache_data
def load_actuators() -> tuple[pd.DataFrame, dict]:
    df = _read_csv("actuators.csv")
    parsers = {
        "Voltage_V": _max_number,
        "Rated_Torque_Nm": _first_number,
        "Peak_Torque_Nm": _max_number,
        "Max_Momentary_Torque_Nm": _first_number,
        "Rated_Speed_RPM": _first_number,
        "Max_Speed_RPM": _first_number,
        "Rated_Power_W": _first_number,
        "Weight_kg": _first_number,
        "Diameter_mm": _first_number,
        "Length_mm": _first_number,
        "Price_EUR": _first_number,
        "Output_Kt_Nm_per_A": _first_number,
    }
    for col, fn in parsers.items():
        df[col + "_num"] = df[col].apply(fn)

    df["Label"] = df["manufacturer"] + " — " + df["model"]
    df["ReducerFamily"] = df["Reducer"].apply(_classify_reducer)
    df["Volume_cm3"] = (
        3.14159 * (df["Diameter_mm_num"] / 20) ** 2 * (df["Length_mm_num"] / 10)
    )

    # Synthetic (median-ratio) estimation of missing torque/speed values.
    ratios_info: dict[tuple[str, str], dict] = {}
    for col in {c for pair in ESTIMATION_PAIRS for c in pair}:
        df[col + "_filled"] = df[col]
        df[col + "_is_est"] = False
    for col_a, col_b in ESTIMATION_PAIRS:
        both = df.dropna(subset=[col_a, col_b])
        both = both[both[col_a] > 0]
        if len(both) < 2:
            continue
        ratio = float((both[col_b] / both[col_a]).median())
        ratios_info[(col_a, col_b)] = {"ratio": ratio, "n": len(both)}
        fa, fb = col_a + "_filled", col_b + "_filled"
        flag_a, flag_b = col_a + "_is_est", col_b + "_is_est"
        mask_a = df[fa].isna() & df[fb].notna()
        df.loc[mask_a, fa] = df.loc[mask_a, fb] / ratio
        df.loc[mask_a, flag_a] = True
        mask_b = df[fb].isna() & df[fa].notna()
        df.loc[mask_b, fb] = df.loc[mask_b, fa] * ratio
        df.loc[mask_b, flag_b] = True

    df["Nm_per_kg_rated_num"] = df["Rated_Torque_Nm_num"] / df["Weight_kg_num"]
    df["Nm_per_kg_peak_num"] = df["Peak_Torque_Nm_num"] / df["Weight_kg_num"]
    return df, ratios_info


MOTOR_STR_TAGS = ["Kt_ref", "Kv_unit", "Kv_ref", "Kb_ref", "R_ref", "Winding"]
MOTOR_NUM = [
    "Kt_raw_Nm_per_A", "Kv_raw", "Kb_raw_Vs_per_rad", "R_raw_ohm", "L_raw_H",
    "Rotor_Inertia_kgm2", "Pole_Pairs", "Thermal_Resistance_C_per_W",
    "Max_Winding_Temp_C", "Ambient_ref_C", "Cont_Current_A", "Peak_Current_A",
    "Voltage_rated_V", "Mass_kg", "Diameter_mm", "Length_mm", "Price_EUR",
    "Km_vendor_Nm_per_sqrtW", "Ke_raw", "Elec_Time_Const_ms", "Mech_Time_Const_ms",
    "Backdrive_Torque_Nm", "Rated_Current_A", "No_Load_Speed_RPM",
]


@st.cache_data
def load_motors() -> pd.DataFrame:
    df = _read_csv("motors.csv")
    df = _to_num(df, MOTOR_NUM)
    for c in MOTOR_STR_TAGS:
        if c in df.columns:
            df[c] = df[c].fillna("")
    df["source_type"] = df.get("source_type", "").fillna("")
    df["is_example"] = df["source_type"].str.lower().eq("example")
    df["Label"] = df["manufacturer"] + " — " + df["model"]

    rows = [ph.derive_motor(rec).as_dict() for rec in df.to_dict("records")]
    dd = pd.DataFrame(rows, index=df.index)
    return pd.concat([df, dd], axis=1)


GEARBOX_NUM = [
    "Ratio_num", "Eff_Fwd", "Eff_Back", "Backlash_arcmin",
    "Rated_Output_Torque_Nm", "Peak_Output_Torque_Nm", "Max_Input_Speed_RPM",
    "Mass_kg", "Diameter_mm", "Length_mm", "Price_EUR",
]


@st.cache_data
def load_gearboxes() -> pd.DataFrame:
    df = _read_csv("gearboxes.csv")
    df = _to_num(df, GEARBOX_NUM)
    df["Label"] = df["manufacturer"] + " — " + df["model"]
    return df


DRIVER_NUM = ["Cont_Current_A", "Peak_Current_A", "Bus_V_min", "Bus_V_max", "Mass_kg", "Price_EUR"]


@st.cache_data
def load_drivers() -> pd.DataFrame:
    df = _read_csv("drivers.csv")
    df = _to_num(df, DRIVER_NUM)
    df["Label"] = df["manufacturer"] + " — " + df["model"]
    return df


act_df, RATIOS_INFO = load_actuators()
motor_df = load_motors()
gbx_df = load_gearboxes()
drv_df = load_drivers()


# --------------------------------------------------------------------------- #
# Shared scatter helpers (from the original app)
# --------------------------------------------------------------------------- #
def _fmt(value, unit=""):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1f}{unit}"


def _build_scatter_fig(sub, x_col, y_col, x_label, y_label, log_x, log_y,
                       size_col, color_col, title, hover_name="Label"):
    fig = px.scatter(
        sub, x=x_col, y=y_col, color=color_col, hover_name=hover_name,
        size=size_col, size_max=26, log_x=log_x, log_y=log_y,
        labels={x_col: x_label, y_col: y_label}, title=title,
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color="rgba(0,0,0,0.4)")))
    fig.update_layout(
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def scatter(data, x_col, y_col, *, x_label, y_label, key, size_col=None,
            color_col="manufacturer", both_scales=True, log_x=False, log_y=False,
            hover_name="Label"):
    sub = data.dropna(subset=[x_col, y_col])
    if size_col:
        sub = sub.dropna(subset=[size_col])
    if sub.empty:
        st.info("No data available for this combination of filters.")
        return
    if both_scales:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                _build_scatter_fig(sub, x_col, y_col, x_label, y_label, False, False,
                                   size_col, color_col, "Linear", hover_name),
                width="stretch", key=f"{key}_linear")
        with c2:
            st.plotly_chart(
                _build_scatter_fig(sub, x_col, y_col, x_label, y_label, True, True,
                                   size_col, color_col, "Log–log", hover_name),
                width="stretch", key=f"{key}_loglog")
    else:
        st.plotly_chart(
            _build_scatter_fig(sub, x_col, y_col, x_label, y_label, log_x, log_y,
                               size_col, color_col, "", hover_name),
            width="stretch", key=key)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
st.sidebar.header("About")
st.sidebar.markdown(
    "Component-layered explorer for BLDC **motors**, **gearboxes**, **drivers** "
    "and integrated **actuators**, plus a **builder** that composes a motor × "
    "gearbox × driver and benchmarks it against commercial actuators."
)
st.sidebar.markdown(
    "**Data integrity:** raw datasheet values are stored with an explicit "
    "reference-frame tag. Anything derived (q-axis Kt, Km, composed torque) is "
    "computed live from the paper's exact conversions — never invented. Rows "
    "whose frame is undetermined are flagged, not guessed."
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "Tables: [motors.csv](./motors.csv) · [gearboxes.csv](./gearboxes.csv) · "
    "[drivers.csv](./drivers.csv) · [actuators.csv](./actuators.csv)  \n"
    "Model reference: *ModelBLDC.pdf* (Lee et al., arXiv:2310.00080)  \n"
    "Engine: [physics.py](./physics.py)"
)

st.title("Motor · Gearbox · Driver · Actuator Explorer")

tab_overview, tab_motors, tab_gbx, tab_drivers, tab_act, tab_builder = st.tabs(
    ["Overview", "Motors", "Gearboxes", "Drivers", "Actuators", "Builder"]
)


# =========================================================================== #
# OVERVIEW
# =========================================================================== #
with tab_overview:
    st.subheader("What this is")
    st.markdown(
        """
Four separable layers you can compare on their own terms, then combine:

| Layer | Governed by | Key metric |
|---|---|---|
| **Motor** | electromagnetics + thermal | **Km = Kt/√R** (winding- & current-invariant) |
| **Gearbox** | mechanics | ratio, forward/back efficiency, backlash |
| **Driver** | power electronics | continuous / peak current, bus voltage |
| **Actuator** | all three, in series | output Nm/kg, Nm/€, the binding constraint |

The single most portable figure of merit for a motor is the **motor constant**
`Km = Kt/√R = τ/√P_copper` — independent of how it's wound or driven. Continuous
torque then follows from thermal limits: `τ_cont = Km·√(ΔT / R_th)`. Everything
else on a datasheet is downstream of the intrinsic set {Kt=Kb, R, L, J, R_th}.
"""
    )

    st.subheader("Frame-resolution coverage")
    st.caption(
        "The paper's core warning: a Kt or Kv is meaningless without its reference "
        "frame. This is how much of the current motor data resolves to the q-axis."
    )
    real = motor_df[~motor_df["is_example"]]
    n_real = len(real)
    n_kt = int(real["kt_q"].notna().sum())
    n_r = int(real["r_phase"].notna().sum())
    n_km = int(real["km"].notna().sum())
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Motors (real)", n_real)
    c2.metric("Kt → q-axis resolved", f"{n_kt}/{n_real}")
    c3.metric("Phase R known", f"{n_r}/{n_real}")
    c4.metric("Km computable", f"{n_km}/{n_real}")
    c5.metric("Actuators", len(act_df))
    if n_km:
        st.success(
            f"**{n_km}/{n_real} real motors resolve to Km.** Note Km ({n_km}) exceeds "
            f"absolute q-axis Kt ({n_kt}): the identity **Km = Kt/√R is winding-free "
            "when Kt and R are both line-to-line** (the wye/delta factors cancel), so a "
            "terminal Kt+R pair (e.g. CubeMars) yields Km with **no** winding assumption. "
            "Where the frame is still unstated (output-/RMS-referenced, unknown winding), "
            "Km stays blank — nothing is assumed."
        )
    else:
        st.warning("No real motor resolves to Km yet — add a terminal Kt + R pair to unlock.")


# =========================================================================== #
# MOTORS
# =========================================================================== #
with tab_motors:
    st.subheader("Motor components")
    st.caption(
        "Frameless / standalone motors and motors extracted from commercial "
        "actuators. Only **Km** (not Kt or Kv alone) is comparable across motors — "
        "winding is a free design choice that trades Kt for speed but leaves Km fixed."
    )
    mdf = motor_df

    st.markdown("**q-axis normalization & Km**")
    view_cols = {
        "Label": "Motor", "source_type": "Source type",
        "Kt_raw_Nm_per_A": "Kt raw", "Kt_ref": "Kt ref",
        "Kv_raw": "Kv raw", "Kv_ref": "Kv ref", "Winding": "Winding",
        "R_raw_ohm": "R raw", "R_ref": "R ref",
        "kt_q": "Kt_q (Nm/A)", "kv_q_rpm_per_V": "Kv_q (rpm/V)",
        "r_phase": "R_phase (Ω)", "km": "Km (Nm/√W)", "km_method": "Km method",
        "km_per_kg": "Km/kg", "Km_vendor_Nm_per_sqrtW": "Km (vendor)",
        "i_thermal": "I_thermal (A)", "kt_note": "resolution note",
    }
    show = mdf[[c for c in view_cols if c in mdf.columns]].rename(columns=view_cols)
    st.dataframe(
        show.style.format({
            "Kt_q (Nm/A)": "{:.4f}", "Kv_q (rpm/V)": "{:.2f}", "R_phase (Ω)": "{:.4f}",
            "Km (Nm/√W)": "{:.3f}", "Km/kg": "{:.3f}", "Km (vendor)": "{:.3f}",
            "I_thermal (A)": "{:.1f}",
        }, na_rep="—"),
        width="stretch", hide_index=True,
    )

    km_avail = mdf.dropna(subset=["km"])
    if not km_avail.empty:
        st.markdown("**Motor constant Km (higher = more torque per √watt of heat)**")
        fig = px.bar(
            km_avail.sort_values("km"), x="km", y="Label", color="source_type",
            orientation="h", labels={"km": "Km (Nm/√W)", "Label": ""},
        )
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch", key="motor_km_bar")

        km_kg = km_avail.dropna(subset=["km_per_kg", "Mass_kg"])
        if not km_kg.empty:
            scatter(km_kg, "Mass_kg", "km", x_label="Mass (kg)", y_label="Km (Nm/√W)",
                    key="motor_km_mass", color_col="source_type", both_scales=False)
    else:
        st.info("No motor resolves to Km yet — see the coverage note on the Overview tab.")

    st.markdown("**Datasheet self-consistency check**")
    st.caption(
        "Independent physics relations that should all agree on a trustworthy "
        "datasheet — `Kt=9.5493/Kv`, `Kt=Kb` (via Ke), `Km=Kt/√R`, `τ_e=L/R`, "
        "`τ_m=R·J/Kt²`. Agreement builds trust; a lone miss flags a bad or "
        "oddly-defined value. Missing fields are deduced from the rest."
    )
    checkable = [r for r in mdf.to_dict("records") if ph.cross_check_motor(r)]
    if not checkable:
        st.info("No motor has enough published constants to cross-check yet.")
    else:
        labels = [r["Label"] for r in checkable]
        default = next((l for l in labels if "AKE90" in l), labels[0])
        pick = st.selectbox("Motor to check", labels, index=labels.index(default),
                            key="motor_check_pick")
        row = next(r for r in checkable if r["Label"] == pick)
        checks = ph.cross_check_motor(row)
        cdf = pd.DataFrame([{
            "Relation": c.name,
            "Predicted": c.predicted if c.predicted is not None else float("nan"),
            "Stated": c.stated if c.stated is not None else float("nan"),
            "Unit": c.unit,
            "Match": "✓" if c.ok else ("✗" if c.ok is False else "—"),
            "Note": c.note,
        } for c in checks])
        n_ok = sum(c.ok is True for c in checks)
        st.dataframe(
            cdf.style.format({"Predicted": "{:.5g}", "Stated": "{:.5g}"}, na_rep="—"),
            width="stretch", hide_index=True,
        )
        st.caption(f"**{n_ok}/{len(checks)} relations agree.**")
        ded = ph.deduce_missing(row)
        if ded:
            st.caption("**Deduced from other fields:** " + "  ·  ".join(
                f"{k} ≈ {v[0]:.4g} _({v[1]})_" for k, v in ded.items()))

    st.markdown("**Kt ↔ Kv consistency check** (fleet view)")
    st.caption("For rows publishing both, in a single frame Kt should equal 9.5493/Kv.")
    both = mdf.dropna(subset=["Kt_raw_Nm_per_A", "Kv_raw"]).copy()
    if both.empty:
        st.info("No motor publishes both a raw Kt and a raw Kv.")
    else:
        both["Kt implied by Kv (9.55/Kv)"] = ph.RPM_V_TO_KT / both["Kv_raw"]
        both["ratio raw/implied"] = both["Kt_raw_Nm_per_A"] / both["Kt implied by Kv (9.55/Kv)"]
        st.dataframe(
            both[["Label", "Kt_raw_Nm_per_A", "Kv_raw", "Kt implied by Kv (9.55/Kv)", "ratio raw/implied"]]
            .rename(columns={"Kt_raw_Nm_per_A": "Kt raw", "Kv_raw": "Kv raw"})
            .style.format({"Kt raw": "{:.4f}", "Kt implied by Kv (9.55/Kv)": "{:.4f}",
                           "ratio raw/implied": "{:.3f}"}, na_rep="—"),
            width="stretch", hide_index=True,
        )


# =========================================================================== #
# GEARBOXES
# =========================================================================== #
with tab_gbx:
    st.subheader("Gearbox components")
    st.caption(
        "Reduction stages, mostly extracted from integrated actuators. Torque "
        "columns marked as *integrated limit* are the parent actuator's output "
        "rating (which may be motor-limited), not the gearbox's standalone spec."
    )
    types = sorted(gbx_df["Type"].dropna().unique())
    sel_types = st.multiselect("Gearbox type", types, default=types)
    gsub = gbx_df[gbx_df["Type"].isin(sel_types)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Gearboxes", len(gsub))
    c2.metric("Ratio range", f"{_fmt(gsub['Ratio_num'].min())}–{_fmt(gsub['Ratio_num'].max())}:1")
    c3.metric("With backlash spec", int(gsub["Backlash_arcmin"].notna().sum()))

    st.markdown("**Reduction ratio vs rated output torque** (bubble = backlash)")
    scatter(gsub, "Ratio_num", "Rated_Output_Torque_Nm",
            x_label="Reduction ratio (:1)", y_label="Rated output torque (Nm)",
            size_col=None, color_col="Type", key="gbx_ratio_torque", both_scales=True)

    st.dataframe(
        gsub[["Label", "Type", "Ratio_num", "Eff_Fwd", "Backlash_arcmin",
              "Rated_Output_Torque_Nm", "Peak_Output_Torque_Nm", "parent_actuator_id"]]
        .rename(columns={"Ratio_num": "Ratio", "Eff_Fwd": "η fwd",
                         "Backlash_arcmin": "Backlash (arcmin)",
                         "Rated_Output_Torque_Nm": "Rated out (Nm)",
                         "Peak_Output_Torque_Nm": "Peak out (Nm)"}),
        width="stretch", hide_index=True,
    )


# =========================================================================== #
# DRIVERS
# =========================================================================== #
with tab_drivers:
    st.subheader("Driver / controller components")
    st.caption(
        "Motor controllers. Sometimes bundled inside an actuator, sometimes "
        "separate. In the builder, the driver's continuous current can be the "
        "binding constraint on output torque."
    )
    st.dataframe(
        drv_df[["Label", "source_type", "Cont_Current_A", "Peak_Current_A",
                "Bus_V_min", "Bus_V_max", "Control", "Comms", "Source"]]
        .rename(columns={"Cont_Current_A": "I cont (A)", "Peak_Current_A": "I peak (A)",
                         "Bus_V_min": "Vbus min", "Bus_V_max": "Vbus max"}),
        width="stretch", hide_index=True,
    )
    if drv_df["Cont_Current_A"].notna().any():
        fig = px.bar(
            drv_df.dropna(subset=["Peak_Current_A"]).sort_values("Peak_Current_A"),
            x="Peak_Current_A", y="Label", color="source_type", orientation="h",
            labels={"Peak_Current_A": "Peak current (A)", "Label": ""},
        )
        fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch", key="drv_current")


# =========================================================================== #
# ACTUATORS  (full analysis, ported from the original app)
# =========================================================================== #
NUMERIC_COLUMNS = {
    "Rated torque (Nm)": "Rated_Torque_Nm_num",
    "Peak torque (Nm)": "Peak_Torque_Nm_num",
    "Max momentary torque (Nm)": "Max_Momentary_Torque_Nm_num",
    "Rated speed (RPM)": "Rated_Speed_RPM_num",
    "Max speed (RPM)": "Max_Speed_RPM_num",
    "Rated power (W)": "Rated_Power_W_num",
    "Weight (kg)": "Weight_kg_num",
    "Diameter (mm)": "Diameter_mm_num",
    "Length (mm)": "Length_mm_num",
    "Price (EUR)": "Price_EUR_num",
    "Nm/kg (rated)": "Nm_per_kg_rated_num",
    "Nm/kg (peak)": "Nm_per_kg_peak_num",
    "Volume (cm³)": "Volume_cm3",
}
NONE = "(none)"
_NUMERIC_KEYS = list(NUMERIC_COLUMNS)


def _axis_picker(prefix, default_num, default_den):
    cA, cB = st.columns(2)
    with cA:
        num = st.selectbox(f"{prefix} — numerator", _NUMERIC_KEYS, index=default_num, key=f"{prefix}_num")
        num_sqrt = st.checkbox("Take √ of numerator", key=f"{prefix}_num_sqrt")
    with cB:
        den = st.selectbox(f"{prefix} — divide by (optional)", [NONE] + _NUMERIC_KEYS,
                           index=0 if default_den is None else default_den + 1, key=f"{prefix}_den")
        den_sqrt = st.checkbox("Take √ of denominator", key=f"{prefix}_den_sqrt")
    return num, den, num_sqrt, den_sqrt


def _resolve_axis(data, num, den, num_sqrt, den_sqrt, col_name):
    num_col = NUMERIC_COLUMNS[num]
    num_series = data[num_col] ** 0.5 if num_sqrt else data[num_col]
    num_label = f"√({num})" if num_sqrt else num
    if den == NONE:
        data[col_name] = num_series
        return num_label, col_name
    den_col = NUMERIC_COLUMNS[den]
    den_series = data[den_col] ** 0.5 if den_sqrt else data[den_col]
    den_label = f"√({den})" if den_sqrt else den
    data[col_name] = num_series / den_series.replace(0, pd.NA)
    return f"{num_label} / {den_label}", col_name


def _range_filters(data: pd.DataFrame, key_prefix: str) -> pd.Series:
    """Render a min/max slider per numeric field inside an expander; return a
    boolean mask over ``data``.

    A field left at its full range is a no-op. Narrowing a field drops rows whose
    value falls outside the band; rows with **no** published value for that field
    are kept (there's not enough info to cut them). Stored slider values are clamped
    to the current data bounds so upstream filters can't push a slider out of range.
    """
    mask = pd.Series(True, index=data.index)
    with st.expander("▸ Range filters — narrow any field to cut rows, then it replots",
                     expanded=False):
        st.caption(
            "Every field starts at its full range. Drag a handle inward to remove "
            "rows outside it (e.g. too heavy / too slow / too expensive). Rows with "
            "no published value for a narrowed field are kept."
        )
        active = []
        cols = st.columns(3)
        for i, (label, col) in enumerate(NUMERIC_COLUMNS.items()):
            series = pd.to_numeric(data[col], errors="coerce")
            valid = series.dropna()
            if valid.empty:
                continue
            lo, hi = float(valid.min()), float(valid.max())
            target = cols[i % 3]
            if lo >= hi:
                target.caption(f"{label}: single value ({lo:g})")
                continue
            k = f"{key_prefix}_rf_{col}"
            if k in st.session_state:  # clamp any stored value into the new bounds
                v = st.session_state[k]
                st.session_state[k] = (min(max(float(v[0]), lo), hi),
                                       min(max(float(v[1]), lo), hi))
                sel = target.slider(label, lo, hi, key=k)
            else:
                sel = target.slider(label, lo, hi, (lo, hi), key=k)
            if sel[0] > lo or sel[1] < hi:
                mask &= series.between(sel[0], sel[1]) | series.isna()
                active.append(f"{label} ∈ [{sel[0]:g}, {sel[1]:g}]")
        if active:
            st.caption("**Active cuts:** " + "  ·  ".join(active))
        else:
            st.caption("_No cuts active — full range on every field._")
    return mask


with tab_act:
    st.subheader("Commercial integrated actuators")

    fc1, fc2, fc3 = st.columns([2, 2, 3])
    with fc1:
        mfrs = sorted(act_df["manufacturer"].dropna().unique())
        sel_mfrs = st.multiselect("Manufacturer", mfrs, default=mfrs)
    with fc2:
        reducer_families = sorted(act_df["ReducerFamily"].dropna().unique())
        sel_red = st.multiselect("Reducer family", reducer_families, default=reducer_families)
    with fc3:
        max_mass = float(act_df["Weight_kg_num"].max() or 10)
        mass_range = st.slider("Weight range (kg)", 0.0, max_mass, (0.0, max_mass), 0.1)

    o1, o2 = st.columns(2)
    exclude_no_weight = o1.checkbox("Hide rows with missing weight", value=False)
    use_estimates = o2.checkbox(
        "Fill missing torque/speed via median ratio", value=False,
        help="Rough order-of-magnitude fill for plotting; flagged and excluded from rankings.",
    )

    filtered = act_df[
        act_df["manufacturer"].isin(sel_mfrs) & act_df["ReducerFamily"].isin(sel_red)
    ].copy()
    mask_mass = (
        filtered["Weight_kg_num"].between(*mass_range)
        | (filtered["Weight_kg_num"].isna() & (not exclude_no_weight))
    )
    filtered = filtered[mask_mass]

    ESTIMATABLE_COLS = [
        "Rated_Torque_Nm_num", "Peak_Torque_Nm_num", "Max_Momentary_Torque_Nm_num",
        "Rated_Speed_RPM_num", "Max_Speed_RPM_num",
    ]
    est_flag_cols = [c + "_is_est" for c in ESTIMATABLE_COLS]
    if use_estimates:
        for col in ESTIMATABLE_COLS:
            filtered[col] = filtered[col + "_filled"]
        filtered["Nm_per_kg_rated_num"] = filtered["Rated_Torque_Nm_num"] / filtered["Weight_kg_num"]
        filtered["Nm_per_kg_peak_num"] = filtered["Peak_Torque_Nm_num"] / filtered["Weight_kg_num"]
        filtered["Synthetic"] = filtered[est_flag_cols].any(axis=1)
    else:
        filtered["Synthetic"] = False

    st.caption(f"{len(filtered)} / {len(act_df)} actuators shown")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Entries", len(filtered))
    k2.metric("Max rated Nm/kg", _fmt(filtered["Nm_per_kg_rated_num"].max()))
    k3.metric("Max peak Nm/kg", _fmt(filtered["Nm_per_kg_peak_num"].max()))
    k4.metric("Max rated torque (Nm)", _fmt(filtered["Rated_Torque_Nm_num"].max()))

    (a_t, a_d, a_s, a_geo, a_rank, a_custom, a_crank, a_table) = st.tabs(
        ["Torque vs cost/mass", "Density vs power", "Torque vs speed", "Geometry",
         "Rankings", "Custom explorer", "Custom rankings", "Data table"]
    )

    with a_t:
        st.markdown("**Rated torque vs Weight** — continuous is the honest sizing number.")
        scatter(filtered, "Weight_kg_num", "Rated_Torque_Nm_num",
                x_label="Weight (kg)", y_label="Rated torque (Nm)", key="a_torque_rated_weight")
        st.markdown("**Peak torque vs Weight**")
        scatter(filtered, "Weight_kg_num", "Peak_Torque_Nm_num",
                x_label="Weight (kg)", y_label="Peak torque (Nm)", key="a_torque_peak_weight")
        st.markdown("**Rated torque vs Price**")
        scatter(filtered, "Price_EUR_num", "Rated_Torque_Nm_num",
                x_label="Price (€)", y_label="Rated torque (Nm)", key="a_torque_rated_price")

    with a_d:
        st.markdown("**Torque density (rated Nm/kg) vs Rated power** — bubble = weight.")
        scatter(filtered, "Rated_Power_W_num", "Nm_per_kg_rated_num",
                x_label="Rated power (W)", y_label="Rated Nm/kg",
                size_col="Weight_kg_num", key="a_density_rated_power")
        st.markdown("**Rated vs Peak density (distance above y=x = peak headroom)**")
        st.caption("Strain-wave actuators sit far above the diagonal: the gearbox caps "
                   "continuous torque well below the short-burst limit.")
        scatter(filtered, "Nm_per_kg_rated_num", "Nm_per_kg_peak_num",
                x_label="Rated Nm/kg", y_label="Peak Nm/kg", key="a_density_rated_vs_peak")

    with a_s:
        st.markdown("**Rated torque vs Max output speed**")
        scatter(filtered, "Max_Speed_RPM_num", "Rated_Torque_Nm_num",
                x_label="Max output speed (RPM)", y_label="Rated torque (Nm)", key="a_speed_rated")
        st.markdown("**Rated power vs Weight**")
        scatter(filtered, "Weight_kg_num", "Rated_Power_W_num",
                x_label="Weight (kg)", y_label="Rated power (W)", key="a_power_weight")

    with a_geo:
        st.markdown("**Rated torque vs Volume (π·(Ø/2)²·L)**")
        scatter(filtered, "Volume_cm3", "Rated_Torque_Nm_num",
                x_label="Approx. volume (cm³)", y_label="Rated torque (Nm)", key="a_torque_volume")
        st.markdown("**Diameter vs Length** (bubble = weight)")
        scatter(filtered, "Diameter_mm_num", "Length_mm_num",
                x_label="Diameter (mm)", y_label="Length (mm)",
                size_col="Weight_kg_num", key="a_diam_len")

    with a_rank:
        ranked = filtered[~filtered["Synthetic"]] if use_estimates else filtered
        if use_estimates:
            st.caption("Synthetic rows excluded — only published values are ranked.")
        st.markdown("**Top rated torque density (Nm/kg, continuous)**")
        top = ranked.dropna(subset=["Nm_per_kg_rated_num"]).nlargest(15, "Nm_per_kg_rated_num")
        fig = px.bar(top.iloc[::-1], x="Nm_per_kg_rated_num", y="Label", color="manufacturer",
                     orientation="h", labels={"Nm_per_kg_rated_num": "Rated Nm/kg", "Label": ""})
        fig.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch", key="a_rank_rated")

        st.markdown("**Rated torque per € (value)**")
        val = ranked.dropna(subset=["Rated_Torque_Nm_num", "Price_EUR_num"]).copy()
        val["Nm_per_EUR"] = val["Rated_Torque_Nm_num"] / val["Price_EUR_num"]
        val = val.nlargest(15, "Nm_per_EUR")
        if val.empty:
            st.info("No rows with both rated torque and price.")
        else:
            fig = px.bar(val.iloc[::-1], x="Nm_per_EUR", y="Label", color="manufacturer",
                         orientation="h", labels={"Nm_per_EUR": "Nm per €", "Label": ""})
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch", key="a_rank_value")

    with a_custom:
        st.markdown("**Pick any X / Y (ratios supported)**")
        st.markdown("**X axis**")
        x_num, x_den, x_ns, x_ds = _axis_picker("X", 6, None)
        st.markdown("**Y axis**")
        y_num, y_den, y_ns, y_ds = _axis_picker("Y", 0, None)
        cc = st.columns(3)
        size_key = cc[0].selectbox("Bubble size", [NONE] + _NUMERIC_KEYS)
        color_key = cc[1].selectbox("Color by", ["manufacturer", "ReducerFamily", "IP"], index=0)
        show_both = cc[2].checkbox("Linear + log-log", value=True)
        rf_mask = _range_filters(filtered, "custom")
        pdf = filtered[rf_mask].copy()
        st.caption(f"**{int(rf_mask.sum())} of {len(filtered)}** actuators pass the range filters.")
        xl, xc = _resolve_axis(pdf, x_num, x_den, x_ns, x_ds, "__x")
        yl, yc = _resolve_axis(pdf, y_num, y_den, y_ns, y_ds, "__y")
        size_col = NUMERIC_COLUMNS[size_key] if size_key != NONE else None
        scatter(pdf, xc, yc, x_label=xl, y_label=yl, size_col=size_col,
                color_col=color_key, both_scales=show_both, log_x=True, log_y=True, key="a_custom")

    with a_crank:
        st.markdown("**Rank by any metric or ratio**")
        rank_source = filtered[~filtered["Synthetic"]] if use_estimates else filtered
        m_num, m_den, m_ns, m_ds = _axis_picker("Rank", 10, None)
        rc1, rc2 = st.columns(2)
        top_n = rc1.number_input("How many", 3, 50, 15, 1, key="a_rank_n")
        order = rc2.radio("Order", ["Highest first", "Lowest first"], horizontal=True, key="a_rank_order")
        rf_mask = _range_filters(rank_source, "crank")
        rdf = rank_source[rf_mask].copy()
        st.caption(f"**{int(rf_mask.sum())} of {len(rank_source)}** rows pass the range filters.")
        ml, mc = _resolve_axis(rdf, m_num, m_den, m_ns, m_ds, "__rank")
        rdf = rdf.dropna(subset=[mc])
        if rdf.empty:
            st.info("No rows have values for the selected metric.")
        else:
            asc = order == "Lowest first"
            top = rdf.nsmallest(int(top_n), mc) if asc else rdf.nlargest(int(top_n), mc)
            plot_order = top.sort_values(mc, ascending=not asc)
            fig = px.bar(plot_order, x=mc, y="Label", orientation="h",
                         labels={mc: ml, "Label": ""})
            fig.update_traces(marker_color="#4C78A8")
            fig.update_yaxes(categoryorder="array", categoryarray=plot_order["Label"].tolist())
            fig.update_layout(height=max(360, 28 * len(plot_order) + 80),
                              margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch", key="a_crank_chart")

    with a_table:
        cols = ["manufacturer", "model", "Reducer", "Voltage_V", "Rated_Torque_Nm",
                "Peak_Torque_Nm", "Rated_Speed_RPM", "Max_Speed_RPM", "Rated_Power_W",
                "Weight_kg", "Nm_per_kg_rated_num", "Nm_per_kg_peak_num",
                "motor_id", "gearbox_id", "driver_id", "IP", "Communication",
                "Price_EUR", "Source"]
        st.dataframe(filtered[[c for c in cols if c in filtered.columns]],
                     width="stretch", hide_index=True)
        st.download_button("Download filtered actuators CSV",
                           filtered[[c for c in cols if c in filtered.columns]].to_csv(index=False).encode("utf-8"),
                           file_name="actuators_filtered.csv", mime="text/csv")


# =========================================================================== #
# BUILDER
# =========================================================================== #
with tab_builder:
    st.subheader("Compose an actuator: motor × gearbox × driver")
    st.caption(
        "Build a synthetic actuator from components and benchmark it against the "
        "commercial cloud. Output continuous torque is min(electromagnetic/thermal, "
        "gearbox rating, driver current) — the builder tells you which term binds."
    )

    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        # default to the first motor whose Kt/Km actually resolves (a real demo)
        _def_m = next((i for i, v in enumerate(motor_df["km"].notna()) if v), 0)
        m_label = st.selectbox("Motor", motor_df["Label"].tolist(), index=_def_m)
        motor_row = motor_df[motor_df["Label"] == m_label].iloc[0].to_dict()
    with bc2:
        g_label = st.selectbox("Gearbox", gbx_df["Label"].tolist())
        gbx_row = gbx_df[gbx_df["Label"] == g_label].iloc[0].to_dict()
    with bc3:
        d_opts = [NONE] + drv_df["Label"].tolist()
        d_label = st.selectbox("Driver", d_opts, index=0)
        drv_row = None if d_label == NONE else drv_df[drv_df["Label"] == d_label].iloc[0].to_dict()

    oc1, oc2, oc3 = st.columns(3)
    default_eff = float(gbx_row.get("Eff_Fwd")) if pd.notna(gbx_row.get("Eff_Fwd")) else {
        "strain_wave": 0.80, "planetary": 0.95, "cycloidal": 0.85,
    }.get(str(gbx_row.get("Type")), 0.90)
    eff = oc1.slider("Forward gear efficiency (assumed)", 0.3, 1.0, default_eff, 0.01,
                     help="Datasheet η is usually unpublished — set your assumption here.")
    vdefault = 48.0
    if drv_row and pd.notna(drv_row.get("Bus_V_max")):
        vdefault = float(drv_row["Bus_V_max"])
    elif pd.notna(motor_row.get("Voltage_rated_V")):
        vdefault = float(motor_row["Voltage_rated_V"])
    vbus = oc2.number_input("Bus voltage (V)", 6.0, 200.0, vdefault, 1.0)
    driver_external = oc3.checkbox("Driver is external (add its mass)", value=True)

    gbx_row = dict(gbx_row, Eff_Fwd=eff)
    comp = ph.compose(motor_row, gbx_row, drv_row, bus_voltage_V=vbus,
                      driver_external=driver_external)

    if comp.kt_unresolved:
        st.warning(
            "This motor's Kt does not resolve to the q-axis (missing frame/winding), "
            "so torque can't be computed. Notes: " + "; ".join(comp.notes)
        )
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cont. output torque", _fmt(comp.tau_out_cont, " Nm"))
        m2.metric("Peak output torque", _fmt(comp.tau_out_peak, " Nm"))
        m3.metric("No-load output speed", _fmt(comp.omega_out_noload_rpm, " rpm"))
        m4.metric("Total mass", _fmt(comp.mass_kg, " kg"))
        m5, m6, m7, m8 = st.columns(4)
        m5.metric("Rated Nm/kg", _fmt(comp.nm_per_kg_cont))
        m6.metric("Km (motor)", _fmt(comp.km))
        m7.metric("Usable cont. current", _fmt(comp.i_cont, " A"))
        m8.metric("Price (Σ known)", _fmt(comp.price_eur, " €"))

        st.info(
            f"**Continuous torque bound by: `{comp.tau_out_cont_bound_by}`** "
            f"(cont. current from *{comp.i_cont_source or 'n/a'}*). "
            + ("Notes: " + "; ".join(comp.notes) if comp.notes else "")
        )

        # Usable output envelope overlaid on the commercial cloud. We deliberately
        # do NOT draw the intrinsic V/R stall line — that current is never
        # deliverable by the drive, and extrapolating to it is exactly the naive
        # move the paper warns against. Caps shown are the driver/thermal/gearbox
        # limited continuous and peak torques, bounded by the no-load speed.
        cloud = act_df.dropna(subset=["Max_Speed_RPM_num", "Rated_Torque_Nm_num"])
        omega0 = comp.omega_out_noload_rpm
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cloud["Max_Speed_RPM_num"], y=cloud["Rated_Torque_Nm_num"],
            mode="markers", name="commercial actuators (rated)",
            marker=dict(color="rgba(120,120,120,0.5)", size=8),
            text=cloud["Label"], hovertemplate="%{text}<br>%{x} rpm, %{y} Nm<extra></extra>",
        ))
        if omega0:
            if comp.tau_out_peak:
                fig.add_trace(go.Scatter(
                    x=[0, omega0], y=[comp.tau_out_peak, comp.tau_out_peak], mode="lines",
                    name="peak cap (this build)", line=dict(color="#E45756", dash="dash")))
            if comp.tau_out_cont:
                fig.add_trace(go.Scatter(
                    x=[0, omega0], y=[comp.tau_out_cont, comp.tau_out_cont], mode="lines",
                    name="continuous cap (this build)", line=dict(color="#54A24B")))
            fig.add_trace(go.Scatter(
                x=[omega0], y=[0], mode="markers+text", name="no-load speed",
                marker=dict(color="#4C78A8", size=11, symbol="x"),
                text=["no-load"], textposition="top center"))
        if comp.tau_out_cont:
            fig.add_trace(go.Scatter(
                x=[0], y=[comp.tau_out_cont], mode="markers", name="composed (cont.)",
                marker=dict(color="#54A24B", size=14, symbol="star")))
        fig.update_layout(
            height=460, xaxis_title="Output speed (rpm)", yaxis_title="Output torque (Nm)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.35),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, width="stretch", key="builder_envelope")
