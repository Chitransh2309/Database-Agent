# Initial database seed dataset

Synthetic data for the Unified AI Database research prototype.

PostgreSQL database: `copilot_db`
- customers: 30
- products: 25
- orders: 80
- order_items: 160
- payments: 80

MongoDB database: `copilot_db`
- customer_activity: 30
- product_reviews: 35
- support_tickets: 15

The same `customer_id` values intentionally exist in PostgreSQL and MongoDB so hybrid queries can join results at the application layer.

## PostgreSQL
In pgAdmin, connect to `copilot_db`, open Query Tool, load `postgres_seed.sql`, and execute it.

## MongoDB
Open mongosh and run:
`load("C:/FULL/PATH/database_seed_data/mongo_seed.js")`

Or paste `mongo_seed.js` into mongosh.

Both scripts are synthetic. They are designed for SQL, MongoDB, semantic retrieval, joins, aggregations, visualization, CRUD, hybrid queries, and self-healing experiments.

The PostgreSQL script drops/recreates the five project tables. Do not run it against data you need to preserve.
