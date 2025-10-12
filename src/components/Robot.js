import React, { Component } from 'react'
import Spline from '@splinetool/react-spline';

export class Robot extends Component {
  render() {
    return (
      <div>
        <div className="container" style={{marginLeft:20, marginBottom:0,height:500}}>
            <Spline scene="https://prod.spline.design/uF0uwFOZ-P3IBjrd/scene.splinecode"/>
        </div>
      </div>
    )
  }
}

export default Robot
