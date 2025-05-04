// src/App.jsx
import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
// Import your future component (we'll create it next)
import LectureView from './components/LectureView';
import './App.css'; // Keep or modify App.css

function App() {
  return (
    <div className="App">
      <nav>
        {/* Optional: Add some basic navigation */}
        <Link to="/">Home</Link> | {/* Example link */}
        <Link to="/lecture/69">Sample Lecture 1</Link> {/* Example link */}
      </nav>
      <h1>Skola Matematike - Lectures</h1>
      <Routes>
        {/* Define a route for the lecture view */}
        {/* The :id part makes 'id' a URL parameter */}
        <Route path="/lecture/:id" element={<LectureView />} />

        {/* Optional: Define a simple home route */}
        <Route path="/" element={<div>Welcome! Select a lecture.</div>} />

        {/* Optional: Add a 404 Not Found route */}
        <Route path="*" element={<div>404: Page Not Found</div>} />
      </Routes>
    </div>
  );
}

export default App;