import React, { Component } from 'react'

export class About extends Component {
  render() {
    return (
      <div style={{marginBottom: 15}}>
        <h1 className="text-light text-center my-2">About Us</h1>
        <div className="container">
          <div className="box">
            <div>
              <p className='my-1 mx-3'>At PDFGenie, we are dedicated to making PDF management smarter, faster, and more intuitive. Our platform is built to handle a variety of PDF tasks effortlessly, ensuring that you can modify your documents with precision and ease. Whether you're compressing files to save space, redacting sensitive information, or flattening PDFs for security, PDFGenie streamlines the process to keep your workflow smooth and efficient. What makes PDFGenie stand out is our focus on simplicity, security, and accessibility. There are no hidden fees or complicated steps—just a seamless experience designed for everyone. With no sign-ups required, you can instantly edit, optimize, and protect your PDFs, so you can focus on what truly matters.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default About
