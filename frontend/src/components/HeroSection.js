import React from 'react';
//import Button from './templatebtn';
import Button1 from './getstartedbtn';
import Button from './templatebtn';

const Herosection = () => {
  return (
    <div id="heroSec">
      <Button/>
      <p id='herotext' style={{ marginLeft: 250,marginTop: 70}}>Ask your data anything.<br />No SQL. No pipelines.<br/>Just answers.</p>
      <p style={{ marginLeft: 250, marginTop: 10, fontSize: 20, color: 'rgba(255,255,255,0.6)', fontFamily: 'Alegreya Sans' }}>
        One conversation. PostgreSQL and MongoDB, together.
      </p>
      <div className='btn-div'>
        <Button1/>
      </div>
    </div>
  );
}

export default Herosection;

