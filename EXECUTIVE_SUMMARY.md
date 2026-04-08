# Executive Summary — Amman Digital Market Analytics

## Top Findings

1. Revenue dropped significantly by 26.6% in February compared to January before gradually recovering in the following months.
2. Amman generated the highest revenue (31,438), outperforming all other cities, while a large portion of revenue (15,109) comes from unknown locations.
3. Product categories show strong differences in customer spending, with Books having the highest average order value (~140.9) and Sports the lowest (~55.4).
4. Statistical testing confirms that differences across product categories are significant (p-value ≈ 0), while no significant difference exists between Amman and Irbid (p = 0.52).

## Supporting Data

- Finding 1:
  - KPI: Monthly Revenue & Monthly Growth Rate
  - Evidence: February growth = -26.6%
  - Chart: `monthly_revenue.png`, `monthly_revenue_growth.png`

- Finding 2:
  - KPI: Revenue by City
  - Evidence:
    - Amman = 31,438
    - Unknown = 15,109
  - Chart: `revenue_by_city.png`

- Finding 3:
  - KPI: Average Order Value by Category
  - Evidence:
    - Books ≈ 140.9
    - Electronics ≈ 104.8
    - Sports ≈ 55.4
  - Chart: `aov_by_category.png`, `category_aov_boxplot.png`

- Finding 4:
  - Statistical Tests:
    - ANOVA (category differences): p ≈ 2.1e-52 → Significant
    - T-test (Amman vs Irbid): p = 0.52 → Not significant

## Recommendations

1. Focus marketing and promotions on high-value categories such as Books and Electronics to maximize revenue impact.
2. Improve customer data collection to reduce "Unknown" city values and enable more accurate geographic analysis.
3. Investigate the cause of the February revenue drop to identify seasonal patterns or operational issues.
4. Expand successful strategies used in Amman to other cities with growth potential.