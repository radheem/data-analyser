# Specification: Grafana Stat Panels & International Currency Formatting

## Overview
This track introduces two major visualization enhancements to our dynamic Grafana dashboard pipeline:
1. **Stat Panels:** A new `stat` chart type optimized for displaying singular aggregate numbers (e.g., Total Spend).
2. **Intelligent Unit Formatting:** Support for dynamic Y-axis and value formatting, specifically designed to gracefully handle global currency ISO codes and standard units without requiring the agent to memorize internal Grafana configuration strings.

## Functional Requirements
1. **Stat Panel Generator:**
   - Implement `generate_stat_panel` in `grafana_generators.py`.
   - The panel must support an optional background sparkline if timeseries data is supplied.
   - Map requests for `chart_type="stat"` in the `create_multi_chart_dashboard` and `add_chart_to_dashboard` tools to this new generator.
2. **Intelligent Unit Normalization:**
   - Implement a new helper function `normalize_grafana_unit(unit_str)` in `grafana_generators.py`.
   - **Currencies:** If exactly 3 letters are provided (e.g., `"USD"`, `"EUR"`, `"gbp"`), it must be normalized to Grafana's expected currency format: `"currencyUSD"`, `"currencyEUR"`, `"currencyGBP"`.
   - **Standard Units:** Standard strings like `"percent"`, `"short"`, or `"bytes"` should be passed through.
   - **Default:** If no unit is provided, default to `"short"`.
3. **Generator Integration:**
   - Update `generate_bar_chart_panel`, `generate_line_chart_panel`, `generate_pie_chart_panel`, and the new `generate_stat_panel` to accept an optional `unit: str` parameter.
   - Inject the normalized unit into the Grafana JSON schema (`fieldConfig.defaults.unit`).
4. **Tool Signature Updates:**
   - Update the MCP tool signatures for `create_multi_chart_dashboard` and `add_chart_to_dashboard` to document and accept the new optional `unit` parameter within the chart configuration schemas.

## Non-Functional Requirements
- Maintain backward compatibility: Existing dashboard creation requests lacking the `unit` parameter should gracefully default to `"short"`.
- Ensure tests cover both standard unit mappings and dynamic currency mappings (e.g., `"JPY" -> "currencyJPY"`).

## Acceptance Criteria
- A dashboard can be successfully created with a `"stat"` panel.
- Passing `unit="EUR"` to a Bar Chart correctly renders the Y-axis using the Euro currency format (`currencyEUR`).
- Passing `unit="percent"` to a Line Chart correctly renders the Y-axis as percentages.
- The unit normalizer robustly handles case variations (e.g., `"usd"` vs `"USD"`).