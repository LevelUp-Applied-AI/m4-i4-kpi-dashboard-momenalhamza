"""Integration 4 — KPI Dashboard: Amman Digital Market Analytics

Extract data from PostgreSQL, compute KPIs, run statistical tests,
and create visualizations for the executive summary.

Usage:
    python analysis.py
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sqlalchemy import create_engine


KPI_KEYS = [
    "monthly_revenue",
    "monthly_revenue_growth_rate",
    "weekly_order_volume",
    "revenue_by_city",
    "average_order_value_by_category",
]


def connect_db():
    """Create a SQLAlchemy engine connected to the amman_market database.

    Returns:
        engine: SQLAlchemy engine instance

    Notes:
        Use DATABASE_URL environment variable if set, otherwise default to:
        postgresql+psycopg://postgres:postgres@localhost:5432/amman_market
    """
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/amman_market",
    )
    return create_engine(database_url)


def extract_data(engine):
    """Extract all required tables from the database into DataFrames.

    Args:
        engine: SQLAlchemy engine connected to amman_market

    Returns:
        dict: mapping of table names to DataFrames
    """
    customers = pd.read_sql("SELECT * FROM customers", engine)
    products = pd.read_sql("SELECT * FROM products", engine)
    orders = pd.read_sql("SELECT * FROM orders", engine)
    order_items = pd.read_sql("SELECT * FROM order_items", engine)

    customers["registration_date"] = pd.to_datetime(customers["registration_date"])
    orders["order_date"] = pd.to_datetime(orders["order_date"])

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
    }


def _prepare_analytic_data(data_dict):
    """Clean and join source tables into analytics-ready DataFrames."""
    customers = data_dict["customers"].copy()
    products = data_dict["products"].copy()
    orders = data_dict["orders"].copy()
    order_items = data_dict["order_items"].copy()

    # Required cleaning from assignment:
    # 1) Exclude cancelled orders
    # 2) Exclude suspicious quantities > 100
    orders = orders[orders["status"] != "cancelled"].copy()
    order_items = order_items[order_items["quantity"] <= 100].copy()

    # Standardize missing city for segmentation
    customers["city"] = customers["city"].fillna("Unknown")

    # Join into line-level analytical table
    line_items = (
        order_items.merge(orders, on="order_id", how="inner")
        .merge(products, on="product_id", how="inner")
        .merge(customers, on="customer_id", how="inner")
    )

    line_items["line_revenue"] = line_items["quantity"] * line_items["unit_price"]
    line_items["order_month"] = line_items["order_date"].dt.to_period("M").dt.to_timestamp()
    line_items["order_week"] = line_items["order_date"].dt.to_period("W").apply(lambda x: x.start_time)
    line_items["registration_month"] = (
        line_items["registration_date"].dt.to_period("M").dt.to_timestamp()
    )

    # Order-level table
    order_level = (
        line_items.groupby(
            ["order_id", "customer_id", "order_date", "city", "status"],
            as_index=False
        )
        .agg(
            order_revenue=("line_revenue", "sum"),
            total_items=("quantity", "sum"),
        )
    )
    order_level["order_month"] = order_level["order_date"].dt.to_period("M").dt.to_timestamp()
    order_level["order_week"] = order_level["order_date"].dt.to_period("W").apply(lambda x: x.start_time)

    # Order-category table for category-level AOV
    order_category = (
        line_items.groupby(["order_id", "category"], as_index=False)
        .agg(category_order_value=("line_revenue", "sum"))
    )

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
        "line_items": line_items,
        "order_level": order_level,
        "order_category": order_category,
    }


def compute_kpis(data_dict):
    """Compute the 5 KPIs defined in kpi_framework.md.

    Args:
        data_dict: dict of DataFrames from extract_data()

    Returns:
        dict: mapping of KPI names to their computed values
    """
    prepared = _prepare_analytic_data(data_dict)
    line_items = prepared["line_items"]
    order_level = prepared["order_level"]
    order_category = prepared["order_category"]

    monthly_revenue = (
        line_items.groupby("order_month", as_index=False)
        .agg(revenue=("line_revenue", "sum"))
        .sort_values("order_month")
    )

    monthly_revenue_growth_rate = monthly_revenue.copy()
    monthly_revenue_growth_rate["growth_rate_pct"] = (
        monthly_revenue_growth_rate["revenue"].pct_change() * 100
    )

    weekly_order_volume = (
        order_level.groupby("order_week", as_index=False)
        .agg(order_count=("order_id", "nunique"))
        .sort_values("order_week")
    )

    revenue_by_city = (
        order_level.groupby("city", as_index=False)
        .agg(
            total_revenue=("order_revenue", "sum"),
            order_count=("order_id", "nunique"),
            average_order_value=("order_revenue", "mean"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    average_order_value_by_category = (
        order_category.groupby("category", as_index=False)
        .agg(
            average_order_value=("category_order_value", "mean"),
            median_order_value=("category_order_value", "median"),
            order_count=("order_id", "nunique"),
        )
        .sort_values("average_order_value", ascending=False)
    )

    return {
        "monthly_revenue": monthly_revenue,
        "monthly_revenue_growth_rate": monthly_revenue_growth_rate,
        "weekly_order_volume": weekly_order_volume,
        "revenue_by_city": revenue_by_city,
        "average_order_value_by_category": average_order_value_by_category,
    }


def run_statistical_tests(data_dict):
    """Run hypothesis tests to validate patterns in the data.

    Args:
        data_dict: dict of DataFrames from extract_data()

    Returns:
        dict: mapping of test names to results
    """
    prepared = _prepare_analytic_data(data_dict)
    order_level = prepared["order_level"]
    order_category = prepared["order_category"]

    results = {}

    # Test 1: T-test for average order value between Amman and Irbid
    amman_values = order_level.loc[order_level["city"] == "Amman", "order_revenue"]
    irbid_values = order_level.loc[order_level["city"] == "Irbid", "order_revenue"]

    if len(amman_values) >= 2 and len(irbid_values) >= 2:
        t_stat, p_value = stats.ttest_ind(
            amman_values,
            irbid_values,
            equal_var=False,
            nan_policy="omit",
        )

        pooled_std = np.sqrt(
            (
                ((len(amman_values) - 1) * amman_values.std(ddof=1) ** 2)
                + ((len(irbid_values) - 1) * irbid_values.std(ddof=1) ** 2)
            )
            / (len(amman_values) + len(irbid_values) - 2)
        )
        cohens_d = (
            (amman_values.mean() - irbid_values.mean()) / pooled_std
            if pooled_std and not np.isnan(pooled_std)
            else np.nan
        )

        results["aov_amman_vs_irbid_ttest"] = {
            "test": "Welch's t-test",
            "statistic": float(t_stat),
            "p_value": float(p_value),
            "effect_size": float(cohens_d) if not np.isnan(cohens_d) else np.nan,
            "interpretation": (
                "Reject H0: average order value differs between Amman and Irbid."
                if p_value < 0.05
                else "Fail to reject H0: no statistically significant difference detected."
            ),
        }

    # Test 2: ANOVA for category-level order value differences
    category_groups = [
        group["category_order_value"].values
        for _, group in order_category.groupby("category")
        if len(group) >= 2
    ]

    if len(category_groups) >= 2:
        f_stat, p_value = stats.f_oneway(*category_groups)

        grand_mean = order_category["category_order_value"].mean()
        ss_between = sum(
            len(group) * (group.mean() - grand_mean) ** 2 for group in category_groups
        )
        ss_total = sum(((group - grand_mean) ** 2).sum() for group in category_groups)
        eta_squared = ss_between / ss_total if ss_total != 0 else np.nan

        results["category_aov_anova"] = {
            "test": "One-way ANOVA",
            "statistic": float(f_stat),
            "p_value": float(p_value),
            "effect_size": float(eta_squared) if not np.isnan(eta_squared) else np.nan,
            "interpretation": (
                "Reject H0: average order value differs across product categories."
                if p_value < 0.05
                else "Fail to reject H0: no statistically significant category difference detected."
            ),
        }

    return results


def create_visualizations(kpi_results, stat_results):
    """Create publication-quality charts for all 5 KPIs.

    Args:
        kpi_results: dict from compute_kpis()
        stat_results: dict from run_statistical_tests()

    Returns:
        None

    Side effects:
        Saves at least 5 PNG files to the output/ directory.
    """
    os.makedirs("output", exist_ok=True)
    sns.set_theme(style="whitegrid", palette="colorblind")

    monthly_revenue = kpi_results["monthly_revenue"]
    monthly_growth = kpi_results["monthly_revenue_growth_rate"]
    weekly_orders = kpi_results["weekly_order_volume"]
    revenue_by_city = kpi_results["revenue_by_city"]
    aov_by_category = kpi_results["average_order_value_by_category"]

    # 1) Monthly revenue line chart
    plt.figure(figsize=(10, 6))
    plt.plot(monthly_revenue["order_month"], monthly_revenue["revenue"], marker="o")
    plt.title("Monthly revenue trend shows how sales moved over time")
    plt.xlabel("Month")
    plt.ylabel("Revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/monthly_revenue.png", dpi=150)
    plt.close()

    # 2) Monthly revenue growth chart
    plt.figure(figsize=(10, 6))
    plt.plot(
        monthly_growth["order_month"],
        monthly_growth["growth_rate_pct"],
        marker="o",
        label="MoM growth %",
    )
    plt.axhline(0, linestyle="--", linewidth=1, label="Zero growth")
    plt.title("Month-over-month revenue growth highlights expansion and slowdown periods")
    plt.xlabel("Month")
    plt.ylabel("Growth rate (%)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/monthly_revenue_growth.png", dpi=150)
    plt.close()

    # 3) Weekly order volume
    plt.figure(figsize=(10, 6))
    plt.plot(weekly_orders["order_week"], weekly_orders["order_count"], marker="o")
    plt.title("Weekly order volume shows the pace of customer demand")
    plt.xlabel("Week")
    plt.ylabel("Number of orders")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/weekly_order_volume.png", dpi=150)
    plt.close()

    # 4) Revenue by city
    plt.figure(figsize=(10, 6))
    sns.barplot(data=revenue_by_city, x="city", y="total_revenue")
    plt.title("Revenue is concentrated more heavily in some cities than others")
    plt.xlabel("City")
    plt.ylabel("Total revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/revenue_by_city.png", dpi=150)
    plt.close()

    # 5) Average order value by category
    plt.figure(figsize=(10, 6))
    sns.barplot(data=aov_by_category, x="category", y="average_order_value")
    plt.title("Average order value differs across product categories")
    plt.xlabel("Product category")
    plt.ylabel("Average order value")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/aov_by_category.png", dpi=150)
    plt.close()

    # 6) Required multi-panel figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(monthly_revenue["order_month"], monthly_revenue["revenue"], marker="o")
    axes[0].set_title("Monthly revenue trend")
    axes[0].set_xlabel("Month")
    axes[0].set_ylabel("Revenue")
    axes[0].tick_params(axis="x", rotation=45)

    top_cities = revenue_by_city.head(8)
    axes[1].bar(top_cities["city"], top_cities["total_revenue"])
    axes[1].set_title("Top cities by revenue")
    axes[1].set_xlabel("City")
    axes[1].set_ylabel("Revenue")
    axes[1].tick_params(axis="x", rotation=45)

    fig.suptitle("KPI dashboard snapshot combines time trend and city concentration")
    fig.tight_layout()
    fig.savefig("output/kpi_dashboard_panel.png", dpi=150)
    plt.close(fig)

    # 7) Required seaborn statistical plot
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=aov_by_category, x="category", y="average_order_value")
    plt.title("Category-level average order values show distribution differences")
    plt.xlabel("Product category")
    plt.ylabel("Average order value")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/category_aov_boxplot.png", dpi=150)
    plt.close()

    # 8) Optional heatmap built from KPI outputs
    city_cat = pd.DataFrame({
        "city": revenue_by_city["city"],
        "revenue_rank": range(1, len(revenue_by_city) + 1),
        "total_revenue": revenue_by_city["total_revenue"],
    }).set_index("city")

    plt.figure(figsize=(8, max(4, len(city_cat) * 0.35)))
    sns.heatmap(city_cat[["total_revenue"]], annot=True, fmt=".1f", cmap="viridis")
    plt.title("Revenue heatmap highlights relative city performance")
    plt.tight_layout()
    plt.savefig("output/revenue_heatmap.png", dpi=150)
    plt.close()


def main():
    """Orchestrate the full analysis pipeline."""
    os.makedirs("output", exist_ok=True)

    engine = connect_db()
    data_dict = extract_data(engine)
    kpi_results = compute_kpis(data_dict)
    stat_results = run_statistical_tests(data_dict)
    create_visualizations(kpi_results, stat_results)

    print("\n=== KPI Summary ===")
    for key, value in kpi_results.items():
        print(f"\n{key}")
        if isinstance(value, pd.DataFrame):
            print(value.head())
        else:
            print(value)

    print("\n=== Statistical Test Results ===")
    for test_name, result in stat_results.items():
        print(f"\n{test_name}")
        for k, v in result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()