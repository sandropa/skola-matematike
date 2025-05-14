import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  Plus,
  FileText,
  FileDown,
  User,
  Settings,
  Search,
} from "lucide-react";
import "./PocetnaStranica.css";

export default function Pocetna() {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    axios
      .get("http://localhost:8000/problemsets")
      .then((res) => {
        setProjects(res.data);
      })
      .catch((err) => {
        console.error("Greška prilikom dohvatanja predavanja:", err);
      });
  }, []);

  return (
    <div>
      {/* Navigacija */}
      <nav className="navbar">
        <div className="navbar-left">
          <img src="/logo.png" alt="Logo" className="navbar-logo large" />
        </div>
        <div className="navbar-right">
          <div className="navbar-item">Predavači</div>
        </div>
      </nav>

      <div className="container">
        {/* Sidebar */}
        <div className="sidebar">
          <div>
            <button className="full-width">
              <Plus className="icon" /> Dodaj predavanje
            </button>

            <div className="sidebar-section">
              <div className="section-title">Tagovi</div>
              <div className="section-item">
                <Plus className="icon small-icon" /> Dodaj tag
              </div>
            </div>
          </div>

          <div className="sidebar-section bottom-icons">
            <User className="action-icon large-icon" />
            <Settings className="action-icon large-icon" />
          </div>
        </div>

        {/* Glavni sadržaj */}
        <div className="main-content">
          <div className="main-header">
            <div className="search-container">
              <Search className="search-icon" />
              <input
                type="text"
                placeholder="Pretraga svih predavanja..."
                className="search-input large"
              />
            </div>
          </div>

          {/* === TABELA PREDAVANJA === */}
          <div className="table-wrapper">
            <table className="table-predavanja">
              <thead>
                <tr>
                  <th>Naslov</th>
                  <th>Grupa</th>
                  <th>Akcije</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project, index) => (
                  <tr key={index}>
                    <td>{project.title}</td>
                    <td>{project.group_name || "Nepoznato"}</td>
                    <td className="action-buttons">
                      <FileText className="action-icon" title="Prikaži fajl" />
                      <FileDown className="action-icon" title="Preuzmi PDF" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
