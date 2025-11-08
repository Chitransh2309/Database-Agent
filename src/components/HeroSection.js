import React from 'react';
//import Button from './templatebtn';
import Button1 from './getstartedbtn';
import Button from './templatebtn';

const Herosection = () => {
  return (
    <div id="heroSec">
      <Button/>
      <p id='herotext' style={{ marginLeft: 250,marginTop: 70}}>Transform your <br />words into powerful SQL queries — insert, update, and fetch<br/> data effortlessly.</p>
      <div className='btn-div'>
        <Button1/>
      </div>
    </div>
  );
}

export default Herosection;

