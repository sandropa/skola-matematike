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
import { Link } from 'react-router-dom';
import { User as UserIcon, Settings as SettingsIcon } from 'lucide-react';

export default function Pocetna() {
  const [projects, setProjects] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');


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
  const filtriraniProjekti = projects.filter((project) =>
  project.title.toLowerCase().includes(searchTerm.toLowerCase())
);


  return (
    <div>
      {}
      

      <div className="container">
        {}
        <div className="sidebar">
          <div>
            <Link to="/editor">
              <button className="full-width">
                <Plus className="icon" /> Dodaj predavanje
              </button>
            </Link>

            <div className="sidebar-section">
              <div className="section-title">Tagovi</div>
              <div className="section-item">
                <Plus className="icon small-icon" /> Dodaj tag
              </div>
            </div>
          </div>

          <div className="sidebar-section bottom-icons">
            <Link to="/profil">
              <UserIcon className="action-icon large-icon" />
            </Link>
            <SettingsIcon className="action-icon large-icon" />
          </div>
        </div>

        {}
        <div className="main-content">
          <div className="main-header">
            <div className="search-container">
              <Search className="search-icon" />
              <input
                type="text"
                placeholder="Pretraga svih predavanja..."
                className="search-input large"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {}
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
                {filtriraniProjekti.map((project, index) => (
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
