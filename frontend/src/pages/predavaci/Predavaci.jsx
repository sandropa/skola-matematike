import React from "react";
import "./Predavaci.css";

export default function Predavaci() {
  const users = [
    { id: 1, name: "Amar Koric", email: "amar.koric@example.com" },
    { id: 2, name: "Sandro Paradžik", email: "sandro.paradzik@example.com" },
    { id: 3, name: "Imana Alibašić", email: "imana.alibasic@example.com" },
    { id: 4, name: "Adisa Bolić", email: "adisa.bolic@example.com" },
    { id: 5, name: "Adi Hujić", email: "adi.hujic@example.com" },
    { id: 6, name: "Selma Halilović", email: "selma.halilovic@example.com" },
    { id: 7, name: "Dino Dervišević", email: "dino.dervisevic@example.com" },
    { id: 8, name: "Nina Kadić", email: "nina.kadic@example.com" },
    { id: 9, name: "Jasmin Hadžić", email: "jasmin.hadzic@example.com" },
    { id: 10, name: "Ajla Mujić", email: "ajla.mujic@example.com" }
  ];

  return (
    <>
      <header className="profile-header-bar">
        <div
          className="logo-wrapper"
          style={{ cursor: "pointer" }}
          onClick={() => (window.location.href = "/")}
        >
          <img src="/logo.png" className="header-logo" alt="Logo" />
          <span className="header-title">Naši Predavači</span>
        </div>
      </header>

      <div className="team-wrapper">
        <h2 className="section-title">Predavači</h2>
        <div className="card-grid">
          {users.map((user, index) => (
            <div key={index} className="card">
              <div className="inner-card">
                <div className="avatar-circle">
                  {user.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .toUpperCase()}
                </div>
                <h3 className="name">{user.name}</h3>
                <p className="email">{user.email}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
