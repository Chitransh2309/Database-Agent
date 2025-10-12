import React,{useState} from 'react';
import logo from './logo.svg'

import { Link } from 'react-router-dom'
const Navbar = () => {
  const[mode,setMode]=useState(1);

  const home=()=>{
    setMode(1);
  }

  const about=()=>{
    setMode(2);
  }

  const docs=()=>{
    setMode(3);
  }
  return (
    <nav>
  <ul>
    <li><Link to='/' className='text-white' onClick={home} style={{marginInlineStart: -500}}>
    <img src={logo} alt="" height="35" width="35" style={{marginRight: 5}} />
    PDFGenie</Link></li>
    <li>
      <Link to="/"className={`${mode===1?"text-white":""}`} onClick={home}>Home</Link>
    </li>
    <li>
      <Link to="/aboutus" className={`${mode===2?"text-white":""}`} onClick={about}>About Us</Link>
    </li>
    <li>
      <Link to="/contact" className={`${mode===3?"text-white":""}`} onClick={docs}>Contact</Link>
    </li>
  </ul>
</nav>)}
export default Navbar;
