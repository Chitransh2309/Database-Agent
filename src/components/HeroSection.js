import React from 'react';
//import Button from './templatebtn';
import Button1 from './getstartedbtn';

const Herosection = () => {
  return (
    <div id="heroSec">
      {/* <Button/> */}
      <p className='my-5' id='herotext' style={{ marginLeft: 250}}> <br />Smart, Simple, <br /> and Seamless PDF Management at <br /> Your Fingertips!</p>
      <Button1/>
    </div>
  );
}

export default Herosection;

