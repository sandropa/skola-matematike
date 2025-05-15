import React, { useState } from "react";
import "./profile.css";
import { useNavigate } from "react-router-dom"; 

export default function ProfilKorisnika() {
  const [user, setUser] = useState({
    ime: "Marko",
    prezime: "Marković",
    email: "marko@example.com",
  });

  const [passwords, setPasswords] = useState({
    old: "",
    new: "",
  });

  const [isEditing, setIsEditing] = useState(false);
  const navigate = useNavigate();

  const inicijali = `${user.ime[0]}${user.prezime[0]}`.toUpperCase();

  const handleUserChange = (e) => {
    setUser({ ...user, [e.target.name]: e.target.value });
  };

  const handlePasswordChange = (e) => {
    setPasswords({ ...passwords, [e.target.name]: e.target.value });
  };

  const handleUserSubmit = (e) => {
    e.preventDefault();
    setIsEditing(false);
    // axios.put("/api/user", user)
  };

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    // axios.post("/api/user/change-password", passwords)
    setPasswords({ old: "", new: "" });
    alert("Lozinka je uspješno promijenjena.");
  };

  return (
    <>
      <header className="profile-header-bar">
        <div
  className="logo-wrapper"
  style={{ cursor: "pointer" }}
  onClick={() => navigate("/")}
>
  <a href="pocetna">
  <img src="logo.png" class="navbar-logo" alt="Logo" />
</a>
  <span className="header-title">Moj profil</span>
</div>
      </header>

      <div className="profile-wrapper">
        <div className="profile-layout">
          {/* Lijeva strana */}
          <div className="profile-sidebar">
            <div className="avatar-large">{inicijali}</div>
            <h2>{user.ime} {user.prezime}</h2>
            <p>{user.email}</p>
            <button className="edit-button" onClick={() => setIsEditing(!isEditing)}>
              {isEditing ? "Odustani" : "Uredi podatke"}
            </button>
          </div>

          {/* Desna strana */}
          <div className="profile-details">
            {isEditing && (
              <form onSubmit={handleUserSubmit} className="profile-form">
                <h3>Uredi podatke</h3>
                <input
                  type="text"
                  name="ime"
                  value={user.ime}
                  onChange={handleUserChange}
                  placeholder="Ime"
                  required
                />
                <input
                  type="text"
                  name="prezime"
                  value={user.prezime}
                  onChange={handleUserChange}
                  placeholder="Prezime"
                  required
                />
                <input
                  type="email"
                  name="email"
                  value={user.email}
                  onChange={handleUserChange}
                  placeholder="Email"
                  required
                />
                <button type="submit" className="save-button">Sačuvaj promjene</button>
              </form>
            )}

            <form onSubmit={handlePasswordSubmit} className="profile-form">
              <h3>Promjena lozinke</h3>
              <input
                type="password"
                name="old"
                value={passwords.old}
                onChange={handlePasswordChange}
                placeholder="Stara lozinka"
                required
              />
              <input
                type="password"
                name="new"
                value={passwords.new}
                onChange={handlePasswordChange}
                placeholder="Nova lozinka"
                required
              />
              <button type="submit" className="save-button">Promijeni lozinku</button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}




