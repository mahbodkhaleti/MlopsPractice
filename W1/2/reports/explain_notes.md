# Baseline EXPLAIN Notes

1. The baseline query aggregates the full `core.calendar_day` table twice: once for the first 30 days and once for the 365-day availability rate. That is the largest repeated cost in the dashboard query.
2. Reviews are aggregated from `core.review` before joining to listings, which is correct, but it is still work Metabase would repeat on every dashboard load without a prepared summary object.
3. The final grouping happens at neighbourhood grain, so the dashboard only needs a small neighbourhood-level result. A materialized view is appropriate because it stores that expensive join and aggregation once.

## Plan timing

- Planning Time: 2.080 ms
- Execution Time: 929.844 ms

## Representative scans

```text
->  Index Scan using neighbourhood_name_key on neighbourhood n  (cost=0.14..12.47 rows=22 width=36) (actual time=0.038..0.092 rows=22 loops=1)
->  Parallel Seq Scan on calendar_day  (cost=0.00..40306.33 rows=1593833 width=9) (actual time=0.022..134.219 rows=1275067 loops=3)
->  Index Only Scan using idx_calendar_date on calendar_day calendar_day_1  (cost=0.43..80005.43 rows=3825200 width=4) (actual time=0.038..0.039 rows=1 loops=1)
->  Bitmap Heap Scan on calendar_day cd  (cost=5808.91..37614.79 rows=425022 width=13) (actual time=21.386..83.141 rows=314400 loops=1)
->  Bitmap Index Scan on idx_calendar_date  (cost=0.00..5702.65 rows=425022 width=0) (actual time=19.313..19.314 rows=314400 loops=1)
->  Seq Scan on listing l  (cost=0.00..321.00 rows=3292 width=21) (actual time=53.940..56.844 rows=5874 loops=1)
->  Subquery Scan on rc  (cost=13549.41..13658.66 rows=5462 width=16) (actual time=97.820..100.667 rows=9383 loops=1)
->  Parallel Seq Scan on review  (cost=0.00..10303.85 rows=208785 width=8) (actual time=0.049..27.211 rows=167028 loops=3)
```

## Representative joins

```text
Join Filter: (l.neighbourhood_id = n.neighbourhood_id)
Rows Removed by Join Filter: 123354
->  Hash Right Join  (cost=110059.16..110368.03 rows=3308 width=85) (actual time=879.987..891.382 rows=5874 loops=1)
->  Hash Left Join  (cost=58079.66..58352.30 rows=3300 width=61) (actual time=363.671..377.177 rows=5874 loops=1)
->  Hash Right Join  (cost=44352.73..44616.71 rows=3300 width=53) (actual time=260.886..272.612 rows=5874 loops=1)
```
