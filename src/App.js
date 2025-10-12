import React, { Component } from 'react'
import About from './components/About'
import Robot from './components/Robot'
import Herosection from './components/HeroSection'

import {
  BrowserRouter as Router,
  Routes,
  Route
} from "react-router-dom";
import Upload from './components/Upload'
import Contact from './components/Contact'
import Navbar from './components/Navbar';
import Footer from './components/Footer';

export default class App extends Component {
  render() {
    return (
      <div>
        <Router>
          <Navbar/>
          <Routes>
            <Route exact path ="/aboutus" element={<About/>}/>
            <Route exact path ="/" element={<div className='d-flex'>
              <div style={{flex:4}}><Herosection/></div>
              <div style={{flex:3}}><Robot/></div>
            </div>}/>
            <Route exact path ="/upload" element={<Upload/>}/>
            <Route exact path ="/contact" element={<Contact/>}/>
          </Routes>
          <Footer/>
        </Router>
      </div>
    )
  }
}

