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
import { Link, useNavigate } from 'react-router-dom';
import { User as UserIcon, Settings as SettingsIcon } from 'lucide-react';
import { Copy, Check } from "lucide-react";




export default function Pocetna() {
  const [projects, setProjects] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const userId = localStorage.getItem("user_id");
  const [viewMode, setViewMode] = useState("lectures"); 
  const [problems, setProblems] = useState([]);
  const [copiedId, setCopiedId] = useState(null);
  const navigate = useNavigate();

  // Function to remember which lecture was opened
const rememberOpenedLecture = (id) => {
  let recent = JSON.parse(localStorage.getItem("recentLectures")) || [];
  recent = recent.filter((item) => item !== id);
  recent.unshift(id);
  localStorage.setItem("recentLectures", JSON.stringify(recent));
};




  useEffect(() => {
    axios
      .get("http://localhost:8000/problemsets")
      .then((res) => {
  const data = res.data;
  const recent = JSON.parse(localStorage.getItem("recentLectures")) || [];

  const sorted = [...data].sort((a, b) => {
    const aIndex = recent.indexOf(a.id);
    const bIndex = recent.indexOf(b.id);
    if (aIndex === -1 && bIndex === -1) return 0;
    if (aIndex === -1) return 1;
    if (bIndex === -1) return -1;
    return aIndex - bIndex;
  });

  setProjects(sorted);
})

      .catch((err) => {
        console.error("Greška prilikom dohvatanja predavanja:", err);
      });
  }, []);
  const filtriraniProjekti = projects.filter((project) =>
  project.title.toLowerCase().includes(searchTerm.toLowerCase())
);

const filtriraniZadaci = problems.filter((problem) =>
  problem.latex_text.toLowerCase().includes(searchTerm.toLowerCase())
);


useEffect(() => {
  if (viewMode === "problems") {
  
        axios.get("http://localhost:8000/problems/with-lecture")
      .then((res) => {
        setProblems(res.data);
      })
      .catch((err) => {
        console.error("Greška prilikom dohvatanja zadataka:", err);
      });
  }
}, [viewMode]);

const copyToClipboard = (text, id) => {
  navigator.clipboard.writeText(text).then(() => {
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1000);
  });
};



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
            <Link to={`/profil/${userId}`}>
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
      placeholder={
        viewMode === "lectures"
          ? "Pretraga svih predavanja..."
          : "Pretraga zadataka..."
      }
      className="search-input large"
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
    />
  </div>

  <div className="dropdown-inline">
    <select
      value={viewMode}
      onChange={(e) => setViewMode(e.target.value)}
      className="dropdown-select"
    >
      <option value="lectures">Predavanja</option>
      <option value="problems">Zadaci</option>
    </select>
  </div>
</div>


          {}
          <div className="table-wrapper">
             {viewMode === "lectures" ? (
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
                      <FileText
                        className="action-icon"
                        title="Prikaži fajl"
                        style={{ cursor: 'pointer' }}
                        onClick={() => {
  rememberOpenedLecture(project.id);
  navigate(`/editor/${project.id}`);
}}

                      />
                      <FileDown className="action-icon" title="Preuzmi PDF" />
                    </td>
                  </tr>
                ))}
              </tbody>
           </table>
) : (

    <table className="table-predavanja">
      <thead>
        <tr>
          <th>Tekst zadatka</th>
          <th>Kategorija</th>
          <th>Predavanje</th>
          <th>Akcija</th>
        </tr>
      </thead>
      <tbody>
        {filtriraniZadaci.map((problem, index) => (

          <tr key={index}>
            <td>{problem.latex_text}</td>
            <td>{problem.category}</td>
            <td>{problem.lecture_title || "Nepoznato"}</td> 
            <td>
     <button
  type="button"
  onClick={(e) => {
    e.preventDefault(); 
    e.stopPropagation(); 
    copyToClipboard(problem.latex_text, problem.id);
  }}
  className="copy-icon-button"
  title="Kopiraj"
>
  {copiedId === problem.id ? (
    <Check size={18} strokeWidth={2} />
  ) : (
    <Copy size={18} strokeWidth={2} />
  )}
</button>





            </td>
          </tr>
        ))}
      </tbody>
    </table>
     )}
  </div>


          </div>
        </div>
      </div>
   
  );
}
