# HW01-B SQL Performance and Metabase

## Database object

- Schema: `student_ali_ghanbari`
- Materialized view: `student_ali_ghanbari.mv_airbnb_neighbourhood_summary`
- Dashboard SQL file: `sql/02_create_materialized_view.sql`

## Runtime comparison

```text
                 query  best_seconds  avg_seconds  speedup_vs_baseline_best
 baseline_direct_query        4.0088       4.6152                    1.0000
materialized_view_read        3.0535       3.6891                    1.3129
```

## What changed

The baseline query computes listing, calendar, review, and neighbourhood aggregations directly from `core` tables. The optimized path stores that neighbourhood-level result in a materialized view and adds indexes on neighbourhood, listing count, and average price so Metabase can read a small prepared object instead of repeating the full joins and aggregations.

## Metabase

- URL: http://185.50.38.163:33012
- Intended dashboard name: `QBC12 HW01 - ali_ghanbari - Airbnb Ops`
- Cards to create from `student_ali_ghanbari.mv_airbnb_neighbourhood_summary`: listings by neighbourhood, average price by neighbourhood, review activity by neighbourhood, availability rate by neighbourhood, and top neighbourhoods table.
- Screenshot path: `screenshots/metabase_dashboard.png`
- Local API status: login was tested successfully, but a later metadata API call timed out, so dashboard creation is documented for the shared UI/API instead of required for the notebook assertions.
