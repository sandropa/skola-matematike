import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';

import axios from 'axios';

function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get('token');

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();


  const handleSubmit = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setMessage('Lozinke se ne poklapaju.');
      return;
    }

    try {
      await axios.post('http://localhost:8000/users/password-reset-confirm', {
        token,
        new_password: newPassword,
      });
     setMessage('Lozinka je uspješno promijenjena. Možete se sada prijaviti.');
    setTimeout(() => {
      navigate('/');
    }, 2000);
    } catch (err) {
      console.error(err);
      setMessage('Neispravan ili istekao token.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-left">
          <img src="/logo.png" alt="Logo" className="login-logo" />
        </div>
        <div className="login-right">
          <h2>Resetuj lozinku</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="password"
              placeholder="Nova lozinka"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Potvrdi lozinku"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
            <button type="submit">Postavi lozinku</button>
          </form>
          {message && <p>{message}</p>}
        </div>
      </div>
    </div>
  );
}

export default ResetPassword;
