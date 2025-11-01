import React from 'react';
import Recognition from './components/Recognition';
import './App.css';

function App() {
  return (
    <div className="app-wrapper">
      <header className="App-header">
        <h1>Ứng dụng nhận diện biển số xe công ty</h1>
      </header>
      <main className="main-content">
        <Recognition />
      </main>
    </div>
  );
}

export default App;