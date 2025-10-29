with source_orders as (
    select
        order_id,
        customer_id,
        status,
        total_amount,
        order_date,
        updated_at
    from {{ source('gold', 'orders_snapshot') }}
)

select
    order_id,
    customer_id,
    status,
    total_amount,
    order_date,
    updated_at,
    case when status = 'completed' then total_amount else 0 end as completed_amount
from source_orders
