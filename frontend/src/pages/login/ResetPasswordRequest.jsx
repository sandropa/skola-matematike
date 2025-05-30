import React, { useState } from 'react';
import axios from 'axios';

function ResetPasswordRequest() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:8000/users/password-reset-request', { email });
      setMessage('Poslali smo vam email sa instrukcijama za resetovanje lozinke.');
    } catch (err) {
      console.error(err);
      setMessage('Došlo je do greške. Provjerite email adresu.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-left">
          <img src="/logo.png" alt="Logo" className="login-logo" />
        </div>
        <div className="login-right">
          <h2>Zaboravili ste lozinku?</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="email"
              placeholder="Unesite vašu email adresu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <button type="submit">Pošalji link za reset</button>
          </form>
          {message && <p>{message}</p>}
        </div>
      </div>
    </div>
  );
}

export default ResetPasswordRequest;
