import logo from './logo.svg';
import './App.css';
import React from 'react';

class FileInput extends React.Component {
  constructor(props) {
    super(props);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.fileInput = React.createRef();
  }
  handleSubmit(event) {
    event.preventDefault();
    alert(
      `Selected file - ${this.fileInput.current.files[0].name}`
    );
  }

  render() {
    return (
      <form onSubmit={this.handleSubmit}>
        <label>
          Upload file:&nbsp;&nbsp;
          <input type="file" ref={this.fileInput} />
        </label>
        <br />
        <button type="submit">Submit</button>
      </form>
    );
  }
}


function App() {

  return (
    <div className="App">
      <header className="App-header">
        <p>
        	ECE 461 Project 2 Demo
        </p>
        <FileInput/>
        


      </header>
    </div>
  );
}

export default App;

