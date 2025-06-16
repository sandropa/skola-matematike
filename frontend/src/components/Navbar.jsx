import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';
import { useNavigate } from 'react-router-dom';
import { Button } from '@mui/material';



function Navbar() {
  const navigate = useNavigate();

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user_id');
  localStorage.removeItem('role');
  navigate('/'); 
};
  
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
        <div
          onClick={handleLogout}
          className="navbar-item"
          style={{ cursor: 'pointer', marginLeft: '24px' }}
        >
                Logout
      </div>


      </div>
    </nav>
  );
}

export default Navbar;
