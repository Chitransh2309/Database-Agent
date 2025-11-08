import React, { Component } from 'react'

export class About extends Component {
  render() {
    return (
      <div style={{marginBottom: 15}}>
        <h1 className="text-light text-center my-2">About Us</h1>
        <div className="container">
          <div className="box">
            <div>
              <p className='my-1 mx-3'>SayQL is an intelligent platform that transforms natural language into SQL — empowering users to interact with databases without ever writing a single query.
Whether you're a developer, analyst, or someone new to databases, SayQL helps you “say” what you need and get instant results.
 Understand plain English instructions and generate accurate SQL queries.
 Execute those queries directly on a live database and return real-time results.
 Automatically generate dynamic forms from your SQL table schemas — including support for constraints, validations, enums, and relationships.
 Help teams prototype, analyze, and visualize data faster — with no manual SQL writing required.
</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default About
