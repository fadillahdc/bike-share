from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide"
)

# =========================
# PALET WARNA
# Hanya dua warna: biru = informasi utama (fokus), abu-abu = pembanding.
# Warna dipilih agar kontras di tema terang maupun gelap Streamlit.
# =========================
HIGHLIGHT = "#2F80ED"
MUTED = "#8A93A0"

# Jumlah observasi minimum agar rata-rata suatu kategori dianggap representatif
MIN_SAMPLE = 30

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    data_path = Path(__file__).parent / "main_data.csv"
    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

# =========================
# HEADER
# =========================
st.title("🚲 Bike Sharing Dashboard")
st.markdown(
    "Dashboard interaktif untuk mengeksplorasi pola penyewaan sepeda berdasarkan "
    "waktu, musim, cuaca, dan tipe pengguna. Arahkan kursor ke grafik untuk melihat "
    "detail, dan gunakan zoom untuk memperbesar area tertentu."
)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("⚙️ Filter & Pengaturan")

    st.markdown("### Filter Data")

    selected_year = st.multiselect(
        "Pilih Tahun",
        options=sorted(df["year"].unique()),
        default=sorted(df["year"].unique())
    )

    selected_season = st.multiselect(
        "Pilih Musim",
        options=sorted(df["season"].unique()),
        default=sorted(df["season"].unique())
    )

    selected_weather = st.multiselect(
        "Pilih Kondisi Cuaca",
        options=sorted(df["weather_condition"].unique()),
        default=sorted(df["weather_condition"].unique())
    )

    selected_day_type = st.multiselect(
        "Pilih Tipe Hari",
        options=sorted(df["day_type"].unique()),
        default=sorted(df["day_type"].unique())
    )

    date_min = df["date"].min()
    date_max = df["date"].max()

    selected_date_range = st.date_input(
        "Pilih Rentang Tanggal",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max
    )

    st.markdown("---")
    st.markdown("### Pilih Visualisasi")

    chart_options = {
        "Tren Penyewaan Bulanan": "monthly_trend",
        "Rata-rata Penyewaan Berdasarkan Musim": "season_chart",
        "Rata-rata Penyewaan Berdasarkan Cuaca": "weather_chart",
        "Pola Penyewaan per Jam": "hourly_pattern",
        "Perbandingan Casual vs Registered": "user_type_chart",
        "Penyewaan Berdasarkan Hari dalam Seminggu": "weekday_chart"
    }

    selected_charts = st.multiselect(
        "Grafik yang Ditampilkan",
        options=list(chart_options.keys()),
        default=list(chart_options.keys())[:4]
    )

    st.markdown("---")
    st.info(
        "Gunakan filter untuk mempersempit data, lalu pilih sendiri grafik yang ingin dianalisis."
    )

# =========================
# FILTER DATA
# =========================
filtered_df = df[
    (df["year"].isin(selected_year)) &
    (df["season"].isin(selected_season)) &
    (df["weather_condition"].isin(selected_weather)) &
    (df["day_type"].isin(selected_day_type))
].copy()

# Filter tanggal: aman jika user baru memilih start date tanpa end date
try:
    start_date, end_date = selected_date_range
    filtered_df = filtered_df[
        (filtered_df["date"] >= pd.to_datetime(start_date)) &
        (filtered_df["date"] <= pd.to_datetime(end_date))
    ]
except (TypeError, ValueError):
    st.warning(
        "Lengkapi start date dan end date pada filter tanggal. "
        "Sementara ini data ditampilkan untuk seluruh rentang tanggal."
    )

if filtered_df.empty:
    st.warning("Tidak ada data yang sesuai dengan filter yang dipilih.")
    st.stop()

# =========================
# METRIC CARDS
# =========================
daily_total = filtered_df.groupby("date")["total_rentals"].sum()
total_rentals = int(filtered_df["total_rentals"].sum())
avg_daily_rentals = int(daily_total.mean())
avg_hourly_rentals = round(filtered_df["total_rentals"].mean(), 2)

top_season = (
    filtered_df.groupby("season")["total_rentals"]
    .mean()
    .sort_values(ascending=False)
    .index[0]
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Penyewaan", f"{total_rentals:,}")
col2.metric("Rata-rata Harian", f"{avg_daily_rentals:,}")
col3.metric("Rata-rata per Jam", f"{avg_hourly_rentals}")
col4.metric("Musim Terbaik", top_season)

st.markdown("---")

# =========================
# HELPER VISUALISASI
# =========================
def base_layout(fig, title, height=420):
    """Layout seragam; warna teks/latar mengikuti tema Streamlit."""
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left", font=dict(size=16)),
        height=height,
        margin=dict(l=10, r=10, t=90, b=10),
        showlegend=False,
    )
    return fig


def ranking_title(data, x, y, unit):
    """Judul berupa pesan utama grafik (takeaway), dihitung dari data terfilter."""
    ranked = data.sort_values(y, ascending=False)
    top = ranked.iloc[0]
    if len(ranked) == 1:
        return f"{top[x]}: {top[y]:,.0f} {unit}"
    bottom = ranked.iloc[-1]
    ratio = top[y] / bottom[y] if bottom[y] else float("inf")
    return (
        f"{top[x]} tertinggi ({top[y]:,.0f} {unit}), "
        f"{ratio:.1f}x dibanding {bottom[x]} ({bottom[y]:,.0f})"
    )


def highlight_bar(data, x, y, title, hover_label, fmt=",.0f"):
    """Bar chart: nilai tertinggi diberi warna aksen, lainnya abu-abu."""
    max_val = data[y].max()
    colors = [HIGHLIGHT if v == max_val else MUTED for v in data[y]]

    fig = go.Figure(
        go.Bar(
            x=data[x],
            y=data[y],
            marker_color=colors,
            text=data[y],
            texttemplate=f"%{{text:{fmt}}}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=f"<b>%{{x}}</b><br>{hover_label}: %{{y:{fmt}}}<extra></extra>",
        )
    )
    base_layout(fig, title)
    fig.update_yaxes(visible=False, range=[0, max_val * 1.15])
    fig.update_xaxes(title=None)
    return fig


def show(fig):
    st.plotly_chart(fig)

# =========================
# CHART FUNCTIONS
# =========================
def show_monthly_trend(data):
    st.subheader("📈 Tren Penyewaan Bulanan")
    monthly = (
        data.groupby(["year", "month"])["total_rentals"]
        .sum()
        .reset_index()
        .sort_values(["year", "month"])
    )
    monthly["period"] = pd.to_datetime(
        monthly["year"].astype(str) + "-" + monthly["month"].astype(str) + "-01"
    )

    peak = monthly.loc[monthly["total_rentals"].idxmax()]
    peak_value = int(peak["total_rentals"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=monthly["period"],
            y=monthly["total_rentals"],
            mode="lines+markers",
            line=dict(color=MUTED, width=3),
            marker=dict(color=MUTED, size=7),
            hovertemplate="<b>%{x|%b %Y}</b><br>Total: %{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[peak["period"]],
            y=[peak["total_rentals"]],
            mode="markers+text",
            marker=dict(color=HIGHLIGHT, size=13),
            text=[f"{peak['period']:%b %Y}: {peak_value:,}"],
            textposition="top center",
            textfont=dict(color=HIGHLIGHT, size=13),
            hovertemplate="<b>%{x|%b %Y}</b><br>Total: %{y:,.0f}<extra></extra>",
        )
    )
    base_layout(fig, f"Penyewaan memuncak pada {peak['period']:%B %Y} ({peak_value:,} penyewaan)", height=450)
    fig.update_xaxes(title=None, tickformat="%b %Y")
    fig.update_yaxes(title="Total Penyewaan per Bulan", range=[0, monthly["total_rentals"].max() * 1.15])
    show(fig)


def show_season_chart(data):
    st.subheader("🌤️ Rata-rata Penyewaan Berdasarkan Musim")
    st.caption("Satuan: rata-rata penyewaan per jam.")
    season_avg = (
        data.groupby("season")["total_rentals"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    show(highlight_bar(
        season_avg, "season", "total_rentals",
        ranking_title(season_avg, "season", "total_rentals", "per jam"),
        "Rata-rata per jam", fmt=",.0f"
    ))


def show_weather_chart(data):
    st.subheader("🌦️ Rata-rata Penyewaan Berdasarkan Cuaca")
    st.caption("Satuan: rata-rata penyewaan per jam.")
    stats = (
        data.groupby("weather_condition")["total_rentals"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "total_rentals", "count": "n_hours"})
        .sort_values("total_rentals", ascending=False)
        .reset_index(drop=True)
    )

    # Kategori dengan data terlalu sedikit tidak dipakai untuk perbandingan pada judul
    reliable = stats[stats["n_hours"] >= MIN_SAMPLE]
    title_source = reliable if not reliable.empty else stats
    show(highlight_bar(
        stats, "weather_condition", "total_rentals",
        ranking_title(title_source, "weather_condition", "total_rentals", "per jam"),
        "Rata-rata per jam", fmt=",.0f"
    ))

    small = stats[stats["n_hours"] < MIN_SAMPLE]
    for _, row in small.iterrows():
        st.caption(
            f"⚠️ Catatan: kondisi **{row['weather_condition']}** hanya memiliki "
            f"{int(row['n_hours'])} jam data pada filter ini, sehingga rata-ratanya "
            f"kurang representatif dan tidak dipakai pada perbandingan di judul."
        )


def show_hourly_pattern(data):
    st.subheader("🕒 Pola Penyewaan per Jam")
    st.caption("Satuan: rata-rata penyewaan per jam.")
    hourly = (
        data.groupby(["hour", "day_type"])["total_rentals"]
        .mean()
        .reset_index()
    )

    day_types = sorted(hourly["day_type"].unique())
    # Fokus: hari kerja (aksen). Tipe hari lain menjadi pembanding (abu-abu).
    focus = next((d for d in day_types if "Kerja" in d), day_types[0])

    fig = go.Figure()
    for day_type in sorted(day_types, key=lambda d: d == focus):  # fokus digambar paling atas
        sub = hourly[hourly["day_type"] == day_type]
        is_focus = day_type == focus
        fig.add_trace(
            go.Scatter(
                x=sub["hour"],
                y=sub["total_rentals"],
                mode="lines",
                name=day_type,
                line=dict(color=HIGHLIGHT if is_focus else MUTED, width=3.5 if is_focus else 2.5),
                hovertemplate=f"<b>{day_type}</b><br>Jam %{{x}}:00<br>"
                              "Rata-rata: %{y:,.0f}<extra></extra>",
            )
        )

    # Anotasi puncak pagi dan sore pada garis fokus
    focus_df = hourly[hourly["day_type"] == focus]
    peaks = []
    for part in (focus_df[focus_df["hour"] < 12], focus_df[focus_df["hour"] >= 12]):
        if not part.empty:
            peaks.append(part.loc[part["total_rentals"].idxmax()])
    for p in peaks:
        fig.add_trace(
            go.Scatter(
                x=[p["hour"]], y=[p["total_rentals"]],
                mode="markers+text",
                marker=dict(color=HIGHLIGHT, size=11),
                text=[f"{int(p['hour']):02d}:00 ({p['total_rentals']:,.0f})"],
                textposition="top center",
                textfont=dict(color=HIGHLIGHT, size=13),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    if len(peaks) == 2:
        title = (
            f"{focus} memiliki dua puncak: pukul {int(peaks[0]['hour']):02d}:00 "
            f"dan {int(peaks[1]['hour']):02d}:00"
        )
    else:
        title = "Pola rata-rata penyewaan per jam sepanjang hari"

    base_layout(fig, title, height=450)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title=None),
        hovermode="x unified",
    )
    fig.update_xaxes(title="Jam", dtick=1)
    fig.update_yaxes(title="Rata-rata Penyewaan per Jam", rangemode="tozero")
    show(fig)


def show_user_type_chart(data):
    st.subheader("👥 Perbandingan Pengguna Casual vs Registered")
    user_type = data[["casual_users", "registered_users"]].sum().reset_index()
    user_type.columns = ["user_type", "total"]
    user_type["user_type"] = user_type["user_type"].map({
        "casual_users": "Casual",
        "registered_users": "Registered",
    })
    top = user_type.sort_values("total", ascending=False).iloc[0]
    share = top["total"] / user_type["total"].sum() * 100
    show(highlight_bar(
        user_type, "user_type", "total",
        f"Pengguna {top['user_type']} menyumbang {share:.0f}% dari total penyewaan",
        "Total penyewaan", fmt=",.0f"
    ))


def show_weekday_chart(data):
    st.subheader("📅 Penyewaan Berdasarkan Hari dalam Seminggu")
    st.caption("Satuan: rata-rata penyewaan per jam.")

    weekday_order = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    weekday_avg = (
        data.groupby("weekday")["total_rentals"]
        .mean()
        .reindex(weekday_order)
        .dropna()
        .reset_index()
    )
    show(highlight_bar(
        weekday_avg, "weekday", "total_rentals",
        ranking_title(weekday_avg, "weekday", "total_rentals", "per jam"),
        "Rata-rata per jam", fmt=",.0f"
    ))

# =========================
# SHOW CHARTS BASED ON CHOICE
# =========================
chart_functions = {
    "monthly_trend": show_monthly_trend,
    "season_chart": show_season_chart,
    "weather_chart": show_weather_chart,
    "hourly_pattern": show_hourly_pattern,
    "user_type_chart": show_user_type_chart,
    "weekday_chart": show_weekday_chart,
}

if not selected_charts:
    st.info("Pilih minimal satu grafik dari sidebar untuk ditampilkan.")
else:
    for chart_name in selected_charts:
        chart_functions[chart_options[chart_name]](filtered_df)
        st.markdown("---")

# =========================
# INSIGHT SECTION
# =========================
season_avg = (
    filtered_df.groupby("season")["total_rentals"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

weather_avg = (
    filtered_df.groupby("weather_condition")["total_rentals"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

user_totals = filtered_df[["casual_users", "registered_users"]].sum()
dominant_user = "registered" if user_totals["registered_users"] >= user_totals["casual_users"] else "casual"

st.subheader("📝 Insight Ringkas")
st.markdown(f"""
- Total penyewaan pada data terfilter mencapai **{total_rentals:,}**.
- Rata-rata penyewaan harian berada di angka **{avg_daily_rentals:,}**.
- Musim dengan rata-rata penyewaan tertinggi adalah **{season_avg.iloc[0]['season']}**.
- Kondisi cuaca paling mendukung penyewaan adalah **{weather_avg.iloc[0]['weather_condition']}**.
- Pada data terfilter, pengguna **{dominant_user}** berkontribusi lebih besar dibanding tipe pengguna lainnya.
""")