import React, { Component } from 'react'
import Spline from '@splinetool/react-spline';

export class Robot extends Component {
  render() {
    return (
      <div id='heroBot'>
        <div className="container" style={{marginLeft:20, marginBottom:0,height:500}}>
            <Spline scene="https://prod.spline.design/KEifiS50JUkiH3PI/scene.splinecode"/>
        </div>
      </div>
    )
  }
}

export default Robot
