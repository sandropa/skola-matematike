import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-left">
        <Link to="/pocetna">
          <img src="/logo.png" className="navbar-logo" alt="Logo" />
        </Link>
      </div>

      <div className="navbar-right">
        <Link
          to="/predavaci"
          className="navbar-item"
          style={{ textDecoration: 'none', color: 'inherit' }}
        >
          Predavači
        </Link>
      </div>
    </nav>
  );
}

export default Navbar;
