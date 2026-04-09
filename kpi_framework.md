# KPI Framework — Amman Digital Market

Identify five KPIs for the Amman Digital Market. Make sure there are at least two KPIs that are measured over time as well as one KPI that is measured for cohorts.

---

## KPI 1

- Title: Monthly Revenue
- Description: Total monthly revenue obtained from completed orders.
- Formula: sum (quantity * unit_price) for each month
- Source: order_items.quantity, products.unit_price, orders.order_date
- Base value: January = 5,878, February = 4,313
- Analysis: The level of revenue differs from one month to another, experiencing a fall in February.
---

## KPI 2
- Indicator: Revenue Growth Rate (Monthly)
- Definition: The percentage change in the revenue between two months.
- Formula for computation: ((Revenue Current Month – Revenue Previous Month) / Revenue Previous Month) * 100
- Source: Monthly Revenue
- References: February: -26.6% | March: 10.4%
- Information: It indicates the changes in the revenue level and the expansion or contraction of the business.
---

## KPI 3
Weekly Number of Orders Completed

- Description: The total number of orders completed on a weekly basis. This measure gives an idea about the level of demand and the engagement of clients during any point in time.

- Formula: Unique values of orders.order_id grouped by week.

- Sources: orders.order_id and orders.order_date.

- Baseline: Approximately 5-7 orders completed per week.

- Importance: Indicates demand consistency and trends in customer engagement levels.

---

## KPI 4
- Metric Name: Revenue Per City
- Description: Total revenue from customers per city.
- Formula: Sum order revenue, segregated by city.
- Source (tables/columns): customers.city, order_items.quantity, products.unit_price.
- Initial Value: Amman = 31,438; Unknown = 15,109; Irbid = 14,501.
- Insights: Provides insight into the most successful cities and identifies data quality issues.
---

## KPI 5

- Name: Average Order Value per Category
- Definition: The revenue per order on average within each category of products sold.
- Formula: Revenue per product category ÷ Orders per product category
- Data source/Columns (tables): products.category, order_items.quantity, products.unit_price
- Baseline values: Books ≈ 140.9, Electronics ≈ 104.8, Sports ≈ 55.4
- Interpretation: Determines which product categories make the most valuable sales.

---
