import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import LectureView from './components/LectureView';
import Login from './pages/login/Login';
import './App.css';

function App() {
  const location = useLocation();

  return (
    <div className="App">
      {location.pathname !== "/login" && (
        <>
          <nav>
            <Link to="/">Home</Link> | 
            <Link to="/lecture/69">Sample Lecture 1</Link>
          </nav>
          <h1>Skola Matematike - Lectures</h1>
        </>
      )}

      <Routes>
        <Route path="/lecture/:id" element={<LectureView />} />
        <Route path="/" element={<div>Welcome! Select a lecture.</div>} />
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<div>404: Page Not Found</div>} />
      </Routes>
    </div>
  );
}

export default App;
