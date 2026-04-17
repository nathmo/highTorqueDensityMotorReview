"""Interactive explorer for the high-torque-density motor dataset."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

CSV_PATH = Path(__file__).parent / "motors.csv"


st.set_page_config(
    page_title="High Torque Density Motor Review",
    layout="wide",
    initial_sidebar_state="expanded",
)


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


# Pairs used to fill missing torque/speed values via median cross-ratios.
# For each (A, B): compute ratio = median(B / A) on rows where both exist,
# then fill missing A from B (A = B / ratio) and missing B from A (B = A * ratio).
ESTIMATION_PAIRS = [
    ("Rated_Torque_Nm_num", "Peak_Torque_Nm_num"),
    ("Peak_Torque_Nm_num", "Max_Momentary_Torque_Nm_num"),
    ("Rated_Speed_RPM_num", "Max_Speed_RPM_num"),
]


@st.cache_data
def load_data() -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(CSV_PATH)

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
        "Nm_per_kg_rated": _first_number,
        "Nm_per_kg_peak": _max_number,
    }
    for col, fn in parsers.items():
        df[col + "_num"] = df[col].apply(fn)

    df["Label"] = df["Manufacturer"] + " — " + df["Model"]
    df["ReducerFamily"] = df["Reducer"].apply(_classify_reducer)

    # Derived helper: volume proxy (cylinder)
    if {"Diameter_mm_num", "Length_mm_num"}.issubset(df.columns):
        df["Volume_cm3"] = (
            3.14159 * (df["Diameter_mm_num"] / 20) ** 2 * (df["Length_mm_num"] / 10)
        )

    # ---- Synthetic (median-ratio) estimation of missing values ----
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

        filled_a, filled_b = col_a + "_filled", col_b + "_filled"
        flag_a, flag_b = col_a + "_is_est", col_b + "_is_est"

        mask_a = df[filled_a].isna() & df[filled_b].notna()
        df.loc[mask_a, filled_a] = df.loc[mask_a, filled_b] / ratio
        df.loc[mask_a, flag_a] = True

        mask_b = df[filled_b].isna() & df[filled_a].notna()
        df.loc[mask_b, filled_b] = df.loc[mask_b, filled_a] * ratio
        df.loc[mask_b, flag_b] = True

    # Nm/kg can now be back-derived from filled torque + weight when missing.
    df["Nm_per_kg_rated_num_filled"] = df["Nm_per_kg_rated_num"].fillna(
        df["Rated_Torque_Nm_num_filled"] / df["Weight_kg_num"]
    )
    df["Nm_per_kg_peak_num_filled"] = df["Nm_per_kg_peak_num"].fillna(
        df["Peak_Torque_Nm_num_filled"] / df["Weight_kg_num"]
    )
    df["Nm_per_kg_rated_num_is_est"] = (
        df["Nm_per_kg_rated_num"].isna() & df["Nm_per_kg_rated_num_filled"].notna()
    )
    df["Nm_per_kg_peak_num_is_est"] = (
        df["Nm_per_kg_peak_num"].isna() & df["Nm_per_kg_peak_num_filled"].notna()
    )

    return df, ratios_info


df, RATIOS_INFO = load_data()

# Columns that get swapped to their "_filled" version when estimation is on.
ESTIMATABLE_COLS = [
    "Rated_Torque_Nm_num",
    "Peak_Torque_Nm_num",
    "Max_Momentary_Torque_Nm_num",
    "Rated_Speed_RPM_num",
    "Max_Speed_RPM_num",
    "Nm_per_kg_rated_num",
    "Nm_per_kg_peak_num",
]

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


# -------------------- Sidebar --------------------
st.sidebar.header("Filters")

mfrs = sorted(df["Manufacturer"].dropna().unique())
sel_mfrs = st.sidebar.multiselect("Manufacturer", mfrs, default=mfrs)

reducer_families = sorted(df["ReducerFamily"].dropna().unique())
sel_red = st.sidebar.multiselect(
    "Reducer family", reducer_families, default=reducer_families
)

min_mass, max_mass = 0.0, float(df["Weight_kg_num"].max() or 10)
mass_range = st.sidebar.slider(
    "Weight range (kg)",
    min_value=float(min_mass),
    max_value=float(max_mass),
    value=(float(min_mass), float(max_mass)),
    step=0.1,
)

exclude_no_weight = st.sidebar.checkbox(
    "Hide rows with missing weight", value=False
)

use_estimates = st.sidebar.checkbox(
    "Fill missing torque/speed via median ratio",
    value=False,
    help=(
        "When a motor only publishes one of (rated, peak) torque — or one of "
        "(rated, max) speed — estimate the other using the dataset median "
        "ratio. Useful for plots; rows with synthetic values are flagged in "
        "the data table and excluded from the rankings tab."
    ),
)

filtered = df[
    df["Manufacturer"].isin(sel_mfrs)
    & df["ReducerFamily"].isin(sel_red)
].copy()
mask_mass = (
    filtered["Weight_kg_num"].between(*mass_range)
    | (filtered["Weight_kg_num"].isna() & (not exclude_no_weight))
)
filtered = filtered[mask_mass]

est_flag_cols = [c + "_is_est" for c in ESTIMATABLE_COLS]
if use_estimates:
    for col in ESTIMATABLE_COLS:
        filtered[col] = filtered[col + "_filled"]
filtered["Synthetic"] = (
    filtered[est_flag_cols].any(axis=1) if use_estimates else False
)

st.sidebar.markdown(f"**{len(filtered)} / {len(df)} rows shown**")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Source PDF: [Design Moteur.pdf](./Design%20Moteur.pdf)  \n"
    "Raw data: [motors.csv](./motors.csv)  \n"
    "Repo README: [README.md](./README.md)"
)


# -------------------- Header --------------------
st.title("High Torque Density Motor Review")
st.markdown(
    "Interactive explorer for BLDC motors and integrated rotary actuators. "
    "Use the sidebar to filter by manufacturer, reducer family, and weight."
)

if use_estimates:
    n_syn_rows = int(filtered["Synthetic"].sum())
    lines = [
        f"**Synthetic values enabled** — {n_syn_rows} row(s) in the current "
        "selection contain at least one value filled from the dataset median "
        "ratio. Treat these as rough order-of-magnitude estimates.",
        "",
        "Ratios (median B / A) used:",
    ]
    labels = {
        "Rated_Torque_Nm_num": "rated torque",
        "Peak_Torque_Nm_num": "peak torque",
        "Max_Momentary_Torque_Nm_num": "max-momentary torque",
        "Rated_Speed_RPM_num": "rated speed",
        "Max_Speed_RPM_num": "max speed",
    }
    for (a, b), info in RATIOS_INFO.items():
        lines.append(
            f"- {labels[b]} ≈ **{info['ratio']:.2f}× {labels[a]}** "
            f"(n = {info['n']} motors with both published)"
        )
    lines.append(
        "\nCaveat: strain-wave actuators typically have a much larger "
        "peak/rated gap than the fleet median, so their synthetic values will "
        "be pessimistic for peak and optimistic for rated."
    )
    st.info("\n".join(lines))

with st.expander("Torque nomenclature — read once before comparing numbers"):
    st.markdown(
        """
- **Rated / nominal torque** — continuous torque at rated speed with a 60 °C
  rise. Use this for duty cycles.
- **Peak torque** — short-duration torque for accelerations / start-stop.
  ZeroErr and Maxon HPJ-DT list this as *repetitive peak*.
- **Max momentary torque** (ZeroErr) — emergency one-shot limit. Can be ~2× the
  repetitive peak. **Don't design against it.**
- **"Max torque"** on CubeMars AKE / summary lines — ambiguous, usually peak
  with no continuous rating published.
"""
    )


# -------------------- KPI header --------------------
def _fmt(value, unit=""):
    if pd.isna(value):
        return "—"
    return f"{value:.1f}{unit}"


k1, k2, k3, k4 = st.columns(4)
k1.metric("Entries", len(filtered))
k2.metric(
    "Max rated Nm/kg",
    _fmt(filtered["Nm_per_kg_rated_num"].max()),
)
k3.metric(
    "Max peak Nm/kg",
    _fmt(filtered["Nm_per_kg_peak_num"].max()),
)
k4.metric(
    "Max rated torque (Nm)",
    _fmt(filtered["Rated_Torque_Nm_num"].max()),
)


# -------------------- Plot helper --------------------
def _build_scatter_fig(
    sub: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    log_x: bool,
    log_y: bool,
    size_col: str | None,
    color_col: str,
    title: str,
):
    fig = px.scatter(
        sub,
        x=x_col,
        y=y_col,
        color=color_col,
        hover_name="Label",
        hover_data={
            "Reducer": True,
            "Rated_Torque_Nm": True,
            "Peak_Torque_Nm": True,
            "Weight_kg": True,
            "Rated_Power_W": True,
            x_col: False,
            y_col: False,
        },
        size=size_col,
        size_max=28,
        log_x=log_x,
        log_y=log_y,
        labels={x_col: x_label, y_col: y_label},
        title=title,
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color="rgba(0,0,0,0.4)")))
    fig.update_layout(
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def scatter(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    *,
    x_label: str,
    y_label: str,
    key: str,
    size_col: str | None = None,
    color_col: str = "Manufacturer",
    both_scales: bool = True,
    log_x: bool = False,
    log_y: bool = False,
):
    """Render a scatter. When ``both_scales`` is true, display linear + log-log
    side-by-side. Otherwise render a single figure with the supplied axes."""
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
                _build_scatter_fig(
                    sub, x_col, y_col, x_label, y_label,
                    False, False, size_col, color_col, "Linear",
                ),
                width="stretch",
                key=f"{key}_linear",
            )
        with c2:
            st.plotly_chart(
                _build_scatter_fig(
                    sub, x_col, y_col, x_label, y_label,
                    True, True, size_col, color_col, "Log–log",
                ),
                width="stretch",
                key=f"{key}_loglog",
            )
    else:
        st.plotly_chart(
            _build_scatter_fig(
                sub, x_col, y_col, x_label, y_label,
                log_x, log_y, size_col, color_col, "",
            ),
            width="stretch",
            key=key,
        )


# -------------------- Tabs --------------------
tab_torque, tab_density, tab_speed, tab_size, tab_rankings, tab_custom, tab_table = st.tabs(
    [
        "Torque vs cost / mass",
        "Density vs power",
        "Torque vs speed",
        "Geometry",
        "Rankings",
        "Custom explorer",
        "Data table",
    ]
)

with tab_torque:
    st.subheader("Rated torque vs Weight")
    st.caption(
        "Continuous / nominal torque — the honest sizing number. The log-log "
        "panel reveals the near-linear scaling between mass and continuous torque."
    )
    scatter(
        filtered,
        "Weight_kg_num",
        "Rated_Torque_Nm_num",
        x_label="Weight (kg)",
        y_label="Rated torque (Nm)",
        key="torque_rated_weight",
    )

    st.subheader("Peak torque vs Weight")
    st.caption("Short-duration / repetitive peak.")
    scatter(
        filtered,
        "Weight_kg_num",
        "Peak_Torque_Nm_num",
        x_label="Weight (kg)",
        y_label="Peak torque (Nm)",
        key="torque_peak_weight",
    )

    st.subheader("Rated torque vs Price")
    scatter(
        filtered,
        "Price_EUR_num",
        "Rated_Torque_Nm_num",
        x_label="Price (€)",
        y_label="Rated torque (Nm)",
        key="torque_rated_price",
    )

    st.subheader("Peak torque vs Price")
    scatter(
        filtered,
        "Price_EUR_num",
        "Peak_Torque_Nm_num",
        x_label="Price (€)",
        y_label="Peak torque (Nm)",
        key="torque_peak_price",
    )

with tab_density:
    st.subheader("Torque density (rated Nm/kg) vs Rated power")
    st.caption(
        "Upper-right corner = best at turning watts into sustained torque per kg. "
        "Bubble size = weight."
    )
    scatter(
        filtered,
        "Rated_Power_W_num",
        "Nm_per_kg_rated_num",
        x_label="Rated power (W)",
        y_label="Rated Nm/kg",
        size_col="Weight_kg_num",
        key="density_rated_power",
    )

    st.subheader("Torque density (peak Nm/kg) vs Rated power")
    scatter(
        filtered,
        "Rated_Power_W_num",
        "Nm_per_kg_peak_num",
        x_label="Rated power (W)",
        y_label="Peak Nm/kg",
        size_col="Weight_kg_num",
        key="density_peak_power",
    )

    st.subheader("Rated vs Peak density (ratio = headroom)")
    st.caption(
        "Points far above the diagonal y=x have large peak-over-rated headroom — "
        "typical of strain-wave actuators whose gearbox limits the continuous "
        "torque far below the short-burst limit."
    )
    scatter(
        filtered,
        "Nm_per_kg_rated_num",
        "Nm_per_kg_peak_num",
        x_label="Rated Nm/kg",
        y_label="Peak Nm/kg",
        key="density_rated_vs_peak",
    )

with tab_speed:
    st.subheader("Rated torque vs Max output speed")
    st.caption(
        "Top-right is harder physics — high torque AND high speed at the output. "
        "High-ratio harmonic actuators cluster low-speed / high-torque."
    )
    scatter(
        filtered,
        "Max_Speed_RPM_num",
        "Rated_Torque_Nm_num",
        x_label="Max output speed (RPM)",
        y_label="Rated torque (Nm)",
        key="speed_rated_torque",
    )

    st.subheader("Peak torque vs Max output speed")
    scatter(
        filtered,
        "Max_Speed_RPM_num",
        "Peak_Torque_Nm_num",
        x_label="Max output speed (RPM)",
        y_label="Peak torque (Nm)",
        key="speed_peak_torque",
    )

    st.subheader("Rated power vs Weight")
    scatter(
        filtered,
        "Weight_kg_num",
        "Rated_Power_W_num",
        x_label="Weight (kg)",
        y_label="Rated power (W)",
        key="speed_power_weight",
    )

with tab_size:
    st.subheader("Weight vs Diameter")
    scatter(
        filtered,
        "Diameter_mm_num",
        "Weight_kg_num",
        x_label="Diameter (mm)",
        y_label="Weight (kg)",
        key="size_weight_diameter",
    )

    st.subheader("Rated torque vs Volume (cm³)")
    st.caption("Volume = π · (Ø/2)² · L, approximated from outer diameter and length.")
    scatter(
        filtered,
        "Volume_cm3",
        "Rated_Torque_Nm_num",
        x_label="Approx. volume (cm³)",
        y_label="Rated torque (Nm)",
        key="size_torque_volume",
    )

    st.subheader("Diameter vs Length")
    scatter(
        filtered,
        "Diameter_mm_num",
        "Length_mm_num",
        x_label="Diameter (mm)",
        y_label="Length (mm)",
        size_col="Weight_kg_num",
        key="size_diameter_length",
    )

with tab_rankings:
    # Rankings stay honest: always use raw (non-synthetic) values here.
    ranked = filtered[~filtered["Synthetic"]] if use_estimates else filtered
    if use_estimates:
        st.caption(
            "Rankings use raw published values only — synthetic rows are "
            "excluded to avoid ranking motors by estimates."
        )
    st.subheader("Top rated torque density (Nm/kg, continuous)")
    top_rated = (
        ranked.dropna(subset=["Nm_per_kg_rated_num"])
        .nlargest(15, "Nm_per_kg_rated_num")
    )
    fig = px.bar(
        top_rated.iloc[::-1],
        x="Nm_per_kg_rated_num",
        y="Label",
        color="Manufacturer",
        orientation="h",
        labels={"Nm_per_kg_rated_num": "Rated Nm/kg", "Label": ""},
    )
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch", key="rank_rated_density")

    st.subheader("Top peak torque density (Nm/kg)")
    top_peak = (
        ranked.dropna(subset=["Nm_per_kg_peak_num"])
        .nlargest(15, "Nm_per_kg_peak_num")
    )
    fig = px.bar(
        top_peak.iloc[::-1],
        x="Nm_per_kg_peak_num",
        y="Label",
        color="Manufacturer",
        orientation="h",
        labels={"Nm_per_kg_peak_num": "Peak Nm/kg", "Label": ""},
    )
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch", key="rank_peak_density")

    st.subheader("Rated torque per € (value)")
    val = ranked.dropna(subset=["Rated_Torque_Nm_num", "Price_EUR_num"]).copy()
    val["Nm_per_EUR"] = val["Rated_Torque_Nm_num"] / val["Price_EUR_num"]
    val = val.nlargest(15, "Nm_per_EUR")
    if val.empty:
        st.info("No rows with both rated torque and price — only MAB Robotics "
                "published prices in this dataset.")
    else:
        fig = px.bar(
            val.iloc[::-1],
            x="Nm_per_EUR",
            y="Label",
            color="Manufacturer",
            orientation="h",
            labels={"Nm_per_EUR": "Nm per €", "Label": ""},
        )
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch", key="rank_value")

with tab_custom:
    st.subheader("Pick any X / Y combination (ratios supported)")
    st.caption(
        "Each axis can be a single variable or a ratio of two. "
        "Example: **Rated torque / Weight** on Y vs **Rated power** on X gives "
        "torque density vs power. Set **Price (EUR)** on Y over **Rated power / Weight** "
        "on X to see price vs power density."
    )

    NONE = "(none)"
    numeric_keys = list(NUMERIC_COLUMNS)

    def _axis_picker(prefix: str, default_num: int, default_den: int | None):
        cA, cB = st.columns(2)
        with cA:
            num = st.selectbox(
                f"{prefix} — numerator",
                numeric_keys,
                index=default_num,
                key=f"{prefix}_num",
            )
            num_sqrt = st.checkbox(
                "Take √ of numerator",
                key=f"{prefix}_num_sqrt",
            )
        with cB:
            den = st.selectbox(
                f"{prefix} — divide by (optional)",
                [NONE] + numeric_keys,
                index=0 if default_den is None else default_den + 1,
                key=f"{prefix}_den",
            )
            den_sqrt = st.checkbox(
                "Take √ of denominator",
                key=f"{prefix}_den_sqrt",
                disabled=False,
            )
        return num, den, num_sqrt, den_sqrt

    def _resolve_axis(
        data: pd.DataFrame,
        num: str,
        den: str,
        num_sqrt: bool,
        den_sqrt: bool,
        col_name: str,
    ):
        """Attach a computed column to data and return (label, column_name)."""
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

    st.markdown("**X axis**")
    x_num, x_den, x_num_sqrt, x_den_sqrt = _axis_picker(
        "X", default_num=6, default_den=None
    )
    st.markdown("**Y axis**")
    y_num, y_den, y_num_sqrt, y_den_sqrt = _axis_picker(
        "Y", default_num=0, default_den=None
    )

    c3, c4, c5 = st.columns(3)
    with c3:
        size_key = st.selectbox("Bubble size", [NONE] + numeric_keys)
    with c4:
        color_key = st.selectbox(
            "Color by",
            ["Manufacturer", "ReducerFamily", "IP"],
            index=0,
        )
    with c5:
        show_both = st.checkbox(
            "Show linear + log-log side by side", value=True,
            help="When unchecked, a single chart uses the log toggles below.",
        )

    plot_df = filtered.copy()
    x_label, x_col = _resolve_axis(
        plot_df, x_num, x_den, x_num_sqrt, x_den_sqrt, "__x_custom"
    )
    y_label, y_col = _resolve_axis(
        plot_df, y_num, y_den, y_num_sqrt, y_den_sqrt, "__y_custom"
    )
    size_col = NUMERIC_COLUMNS[size_key] if size_key != NONE else None

    if show_both:
        scatter(
            plot_df,
            x_col,
            y_col,
            x_label=x_label,
            y_label=y_label,
            size_col=size_col,
            color_col=color_key,
            both_scales=True,
            key="custom",
        )
    else:
        c6, c7 = st.columns(2)
        with c6:
            log_x = st.checkbox("Log X", value=True, key="custom_logx")
        with c7:
            log_y = st.checkbox("Log Y", value=True, key="custom_logy")
        scatter(
            plot_df,
            x_col,
            y_col,
            x_label=x_label,
            y_label=y_label,
            size_col=size_col,
            color_col=color_key,
            both_scales=False,
            log_x=log_x,
            log_y=log_y,
            key="custom_single",
        )

with tab_table:
    st.subheader("Filtered dataset")
    if use_estimates:
        st.caption(
            "`Synthetic` is True when any shown torque/speed value for that row "
            "was filled in from the dataset median ratio rather than the source."
        )
    display_cols = [
        "Manufacturer",
        "Model",
        "Reducer",
        "Voltage_V",
        "Rated_Torque_Nm",
        "Peak_Torque_Nm",
        "Max_Momentary_Torque_Nm",
        "Rated_Speed_RPM",
        "Max_Speed_RPM",
        "Rated_Power_W",
        "Weight_kg",
        "Diameter_mm",
        "Length_mm",
        "Nm_per_kg_rated",
        "Nm_per_kg_peak",
        "IP",
        "Communication",
        "Price_EUR",
        "Source",
        "Notes",
    ]
    if use_estimates:
        display_cols = ["Synthetic"] + display_cols
        # Render numeric estimates back into the string columns so they show up.
        table = filtered[display_cols].copy()
        est_display = {
            "Rated_Torque_Nm": "Rated_Torque_Nm_num_filled",
            "Peak_Torque_Nm": "Peak_Torque_Nm_num_filled",
            "Max_Momentary_Torque_Nm": "Max_Momentary_Torque_Nm_num_filled",
            "Rated_Speed_RPM": "Rated_Speed_RPM_num_filled",
            "Max_Speed_RPM": "Max_Speed_RPM_num_filled",
            "Nm_per_kg_rated": "Nm_per_kg_rated_num_filled",
            "Nm_per_kg_peak": "Nm_per_kg_peak_num_filled",
        }
        for raw_col, filled_col in est_display.items():
            flag_col = filled_col.replace("_filled", "_is_est")
            mask = filtered[flag_col].fillna(False)
            table.loc[mask, raw_col] = filtered.loc[mask, filled_col].map(
                lambda v: "—" if pd.isna(v) else f"≈{v:.2f}"
            )
    else:
        table = filtered[display_cols]
    st.dataframe(table, width="stretch", hide_index=True)

    st.download_button(
        "Download filtered data as CSV",
        table.to_csv(index=False).encode("utf-8"),
        file_name="motors_filtered.csv",
        mime="text/csv",
    )
