import React, { Component } from 'react'

export class About extends Component {
  render() {
    return (
      <div style={{marginBottom: 15}}>
        <h1 className="text-light text-center my-2">About</h1>
        <div className="container">
          <div className="box">
            <div>
              <p className='mx-3'>
                Most teams live with more than one database — structured records in
                PostgreSQL, flexible documents in MongoDB — and switch between SQL and
                aggregation pipelines just to answer one question. AI DB Copilot removes
                that friction: ask in plain English, and it figures out the rest.
              </p>
              <p className='mx-3'>
                At its core is a Semantic Database Twin — a live map of every table,
                collection, field, and relationship across both databases. Every query is
                grounded in your real schema, not a guess.
              </p>
              <p className='mx-3'>
                A query planner knows when a question needs PostgreSQL, MongoDB, or both.
                Ask for <em>"customers with high order totals who are also highly active on
                the website"</em> and it plans both sides, runs them, and fuses the results
                into one answer — something no single query language can do alone.
              </p>
              <p className='mx-3'>
                When a query fails, the system reads the real error and repairs it
                automatically instead of handing you a stack trace. You can also create
                tables and collections, run CRUD operations, and generate forms and
                visualizations — all from plain English.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default About
