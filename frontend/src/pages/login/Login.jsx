import React from 'react';
import './Login.css';

function Login() {
  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-left">
          <img src="/logo.png" alt="Logo" className="login-logo" />
        </div>
        <div className="login-right">
          <h2>Prijava</h2>
          <form>
            <input type="email" placeholder="Email adresa" required />
            <input type="password" placeholder="Lozinka" required />
            <button type="submit">Prijavi se</button>
          </form>
          <div className="login-links">
            <a href="#">Zaboravili ste lozinku?</a>
        
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
