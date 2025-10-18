import React from 'react';
import Recognition from './components/Recognition';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Ứng dụng nhận diện biển số xe công ty</h1>
      </header>
      <main>
        <Recognition />
      </main>
    </div>
  );
}

export default App;