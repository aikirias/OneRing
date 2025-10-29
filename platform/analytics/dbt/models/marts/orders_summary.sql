with orders as (
    select
        customer_id,
        date_trunc('month', order_date)::date as order_month,
        sum(total_amount) as gross_revenue,
        sum(completed_amount) as completed_revenue,
        count(*) as order_count
    from {{ ref('stg_orders') }}
    group by 1, 2
)

select
    customer_id,
    order_month,
    gross_revenue,
    completed_revenue,
    order_count,
    case
        when order_count = 0 then 0
        else completed_revenue / nullif(order_count, 0)
    end as avg_completed_order_value
from orders
