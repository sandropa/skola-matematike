import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  Plus,
  Trash2,
  FolderOpen,
  UploadCloud,
  User,
  Settings,
  Search,
} from "lucide-react";
import "./PocetnaStranica.css";

export default function OverleafDashboard() {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    axios
      .get("http://localhost:8000/problemsets")
      .then((res) => {
        setProjects(res.data);
      })
      .catch((err) => {
        console.error("Error fetching lectures:", err);
      });
  }, []);

  return (
    <div>
      {/* Navbar */}
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
              <Plus className="icon" /> New Lecture
            </button>

            <div className="sidebar-section">
              <div className="section-title">Tags</div>
              <div className="section-item">+ Add Tag</div>
            </div>
          </div>

          <div className="sidebar-section bottom-icons">
            <User className="action-icon large-icon" />
            <Settings className="action-icon large-icon" />
          </div>
        </div>

        {/* Main Content */}
        <div className="main-content">
          <div className="main-header">
            <div className="search-container">
              <Search className="search-icon" />
              <input
                type="text"
                placeholder="Search in all lectures..."
                className="search-input large"
              />
            </div>
          </div>

          <div className="project-list">
            {projects.map((project, index) => (
              <div key={index} className="project-card">
                <div>
                  <div className="project-title">{project.title}</div>
                  <div className="project-meta">
                    Created at:{" "}
                    {project.created_at
                      ? new Date(project.created_at).toLocaleDateString()
                      : "N/A"}
                  </div>
                </div>
                <div className="project-actions">
                  <FolderOpen className="action-icon" />
                  <UploadCloud className="action-icon" />
                  <Trash2 className="action-icon" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
