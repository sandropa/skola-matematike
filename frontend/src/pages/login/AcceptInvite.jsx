import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Login.css'; 

import { GoogleLogin } from '@react-oauth/google';
import {
  Container, Card, CardContent, Typography,
  TextField, Button, Box, Alert, Link
} from '@mui/material';


function AcceptInvite() {
  const { inviteId } = useParams();
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccessMsg('');
    setErrorMsg('');

    if (password !== confirmPassword) {
      setErrorMsg('Lozinke se ne poklapaju.');
      return;
    }

    try {
      const res = await axios.post(`http://localhost:8000/users/accept-invite/${inviteId}`, {
        password: password,
      });

      setSuccessMsg(res.data.message);
      setTimeout(() => navigate('/'), 2000);
    } catch (err) {
      console.error('Invite error:', err);
      setErrorMsg(err.response?.data?.detail || 'Greška pri registraciji.');
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
  try {
    const res = await axios.post(`http://localhost:8000/users/accept-invite/google/${inviteId}`, {
      id_token: credentialResponse.credential,
    });

    setSuccessMsg(res.data.message);
    setTimeout(() => navigate('/'), 2000);
  } catch (err) {
    console.error('Google invite error:', err);
    setErrorMsg(err.response?.data?.detail || 'Greška pri Google registraciji.');
  }
};

const handleGoogleError = () => {
  setErrorMsg('Google prijava nije uspjela.');
};


  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-left">
          <img src="/logo.png" alt="Logo" className="login-logo" />
        </div>
        <div className="login-right">
          <h2>Kreiraj lozinku</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="password"
              placeholder="Lozinka"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Potvrdi lozinku"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
            <button type="submit">Registruj se</button>
          </form>
<div style={{ textAlign: 'center', marginTop: '30px' }}>
  <p>ili</p>
  <GoogleLogin
    onSuccess={handleGoogleSuccess}
    onError={handleGoogleError}
  />
</div>

          {successMsg && <p className="success-msg">{successMsg}</p>}
          {errorMsg && <p className="error-msg">{errorMsg}</p>}

          <div className="login-links">
            <a href="/">Već imaš nalog?</a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AcceptInvite;
