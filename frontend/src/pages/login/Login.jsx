import React, { useState } from 'react';
import { useNavigate } from "react-router-dom";
import axios from 'axios';
import './Login.css';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    try {
      const response = await axios.post('http://localhost:8000/users/login', {
        email,
        password,
      });

      const { access_token, user_id } = response.data;
      console.log(access_token)

      localStorage.setItem('token', access_token);
      localStorage.setItem('user_id', user_id);
      navigate(`/profil/${user_id}`)

      
    } catch (err) {
      console.error('Login error:', err);
      setErrorMsg('Pogrešan email ili lozinka.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-left">
          <img src="/logo.png" alt="Logo" className="login-logo" />
        </div>
        <div className="login-right">
          <h2>Prijava</h2>
          <form onSubmit={handleLogin}>
            <input
              type="email"
              placeholder="Email adresa"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Lozinka"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button type="submit">Prijavi se</button>
          </form>

          {errorMsg && <p className="error-msg">{errorMsg}</p>}

         <div className="login-links">
          <a href="/forgot-password">Zaboravili ste lozinku?</a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
