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
import LocalOfferIcon from '@mui/icons-material/LocalOffer';
import TagDropdown from '../../components/TagDropdown';
import AddTagDialog from '../../components/AddTagDialog';
import SiderbarTags from '../../components/SidebarTags';








export default function Pocetna() {
  const [projects, setProjects] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const userId = localStorage.getItem("user_id");
  const [viewMode, setViewMode] = useState("lectures"); 
  const [problems, setProblems] = useState([]);
  const [copiedId, setCopiedId] = useState(null);
  const navigate = useNavigate();
  const [openTagDialog, setOpenTagDialog] = useState(false);
  const [selectedLectureId, setSelectedLectureId] = useState(null);
  const [openAddTag, setOpenAddTag] = useState(false);
  const [tags, setTags] = useState([]);

useEffect(() => {
  axios
    .get("http://localhost:8000/tags")
    .then((res) => setTags(res.data))
    .catch((err) => console.error("Greška prilikom dohvatanja tagova:", err));
}, []);


  


const rememberOpenedLecture = (id) => {
  const userId = localStorage.getItem("user_id");
  if (!userId) return;

  const key = `recentLectures_${userId}`;
  let recent = JSON.parse(localStorage.getItem(key)) || [];
  recent = recent.filter((item) => item !== id);
  recent.unshift(id);
  localStorage.setItem(key, JSON.stringify(recent));
};


useEffect(() => {
  axios
    .get("http://localhost:8000/problemsets")
    .then((res) => {
      const data = res.data;
      const userId = localStorage.getItem("user_id");
      const key = `recentLectures_${userId}`;
      const recent = JSON.parse(localStorage.getItem(key)) || [];

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
             <div
  className="section-item"
  onClick={() => setOpenAddTag(true)}
  style={{ cursor: "pointer" }}
>
  <Plus className="icon small-icon" /> Dodaj tag
</div>
<div className="tag-list">
  {tags.map((tag) => (
    <div
      key={tag.id}
      className="tag-item"
      style={{
        display: "flex",
        alignItems: "center",
        marginBottom: "6px",
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: "14px",
          height: "14px",
          backgroundColor: tag.color,
          borderRadius: "50%",
          marginRight: "8px",
        }}
      />
      <span>{tag.name}</span>
    </div>
  ))}
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
                       <LocalOfferIcon
    className="action-icon"
    titleAccess="Dodaj tag"
    style={{ cursor: 'pointer' }}
    onClick={() => {
      setSelectedLectureId(project.id);
      setOpenTagDialog(true);
    }}
  />
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

{openAddTag && (
  <AddTagDialog
    open={openAddTag}
    onClose={() => setOpenAddTag(false)}
    onTagAdded={() => {
      setOpenAddTag(false);
      
    }}
  />
)}

          </div>
          {openTagDialog && selectedLectureId && (
  <TagDropdown
    open={openTagDialog}
    onClose={() => setOpenTagDialog(false)}
    lectureId={selectedLectureId}
    onSaved={() => {
      setOpenTagDialog(false);
    }}
  />
)}

        </div>
      </div>



   
  );
}
