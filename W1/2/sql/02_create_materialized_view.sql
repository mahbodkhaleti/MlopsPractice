
DROP MATERIALIZED VIEW IF EXISTS "student_ali_ghanbari".mv_airbnb_neighbourhood_summary;

CREATE MATERIALIZED VIEW "student_ali_ghanbari".mv_airbnb_neighbourhood_summary AS
with date_bounds as (
    select min(date) as start_date
    from core.calendar_day
),
calendar_30 as (
    select
        cd.listing_id,
        avg(cd.price) filter (where cd.price is not null) as avg_calendar_price_30,
        avg(case when cd.available then 1.0 else 0.0 end) as availability_30_rate
    from core.calendar_day cd
    cross join date_bounds db
    where cd.date >= db.start_date
      and cd.date < db.start_date + interval '30 days'
    group by cd.listing_id
),
calendar_365 as (
    select
        listing_id,
        avg(case when available then 1.0 else 0.0 end) as availability_365_rate
    from core.calendar_day
    group by listing_id
),
review_counts as (
    select
        listing_id,
        count(*)::bigint as total_reviews
    from core.review
    group by listing_id
)
select
    n.name as neighbourhood,
    count(*)::bigint as num_listings,
    round(avg(l.listing_price)::numeric, 2) as avg_price,
    round(percentile_cont(0.5) within group (order by l.listing_price)::numeric, 2) as median_price,
    round(avg(l.minimum_nights)::numeric, 2) as avg_minimum_nights,
    coalesce(sum(rc.total_reviews), 0)::bigint as total_reviews,
    round(avg(coalesce(rc.total_reviews, 0))::numeric, 2) as reviews_per_listing,
    round(avg(c30.availability_30_rate)::numeric, 4) as availability_30_rate,
    round(avg(c365.availability_365_rate)::numeric, 4) as availability_365_rate
from core.listing l
join core.neighbourhood n on n.neighbourhood_id = l.neighbourhood_id
left join calendar_30 c30 on c30.listing_id = l.listing_id
left join calendar_365 c365 on c365.listing_id = l.listing_id
left join review_counts rc on rc.listing_id = l.listing_id
where l.listing_price is not null
  and l.listing_price > 0
group by n.name
order by num_listings desc, neighbourhood;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_airbnb_neighbourhood_summary_neighbourhood
ON "student_ali_ghanbari".mv_airbnb_neighbourhood_summary (neighbourhood);

CREATE INDEX IF NOT EXISTS idx_mv_airbnb_neighbourhood_summary_num_listings
ON "student_ali_ghanbari".mv_airbnb_neighbourhood_summary (num_listings DESC);

CREATE INDEX IF NOT EXISTS idx_mv_airbnb_neighbourhood_summary_avg_price
ON "student_ali_ghanbari".mv_airbnb_neighbourhood_summary (avg_price);
