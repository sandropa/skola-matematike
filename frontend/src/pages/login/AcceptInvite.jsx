import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Login.css'; // koristi isti stil

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
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      console.error('Invite error:', err);
      setErrorMsg(err.response?.data?.detail || 'Greška pri registraciji.');
    }
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

          {successMsg && <p className="success-msg">{successMsg}</p>}
          {errorMsg && <p className="error-msg">{errorMsg}</p>}

          <div className="login-links">
            <a href="/login">Već imaš nalog?</a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AcceptInvite;
