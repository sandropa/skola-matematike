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
import { User as UserIcon } from 'lucide-react';
import { Copy, Check } from "lucide-react";
import LocalOfferIcon from '@mui/icons-material/LocalOffer';
import TagDropdown from '../../components/TagDropdown';
import AddTagDialog from '../../components/AddTagDialog';
import SiderbarTags from '../../components/SidebarTags';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
} from "@mui/material";
import { Drawer, IconButton } from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import useMediaQuery from "@mui/material/useMediaQuery";


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
  const [tagToDelete, setTagToDelete] = useState(null);
  const [activeTagId, setActiveTagId] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const isMobile = useMediaQuery('(max-width:900px)');

  const handleDrawerOpen = () => setDrawerOpen(true);
  const handleDrawerClose = () => setDrawerOpen(false);

const handleTagClick = (tagId) => {

  if (activeTagId === tagId) {
    setActiveTagId(null);
    axios.get("http://localhost:8000/problemsets")
      .then((res) => setProjects(res.data))
      .catch((err) => console.error("Greška prilikom dohvatanja svih predavanja:", err));
  } else {
    setActiveTagId(tagId);
    axios.get(`http://localhost:8000/tags/${tagId}/lectures`)
      .then((res) => setProjects(res.data))
      .catch((err) => console.error("Greška prilikom filtriranja predavanja:", err));
  }
};





const fetchTags = () => {
    axios
      .get("http://localhost:8000/tags")
      .then((res) => setTags(res.data))
      .catch((err) => console.error("Greška prilikom dohvatanja tagova:", err));
  };

const deleteTag = () => {
  axios.delete(`http://localhost:8000/tags/${tagToDelete}`)
    .then(fetchTags)
    .catch(err => console.error("Greška prilikom brisanja taga:", err))
    .finally(() => setTagToDelete(null));
};


useEffect(() => {
  fetchTags();
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

const downloadPDF = (problemsetId) => {
  axios.get(`http://localhost:8000/problemsets/${problemsetId}/pdf`, {
    responseType: 'blob'
  })
  .then((res) => {
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `problemset_${problemsetId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  })
  .catch((err) => {
    console.error("Greška prilikom preuzimanja PDF-a:", err);
  });
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
      {/* Hamburger dugme za male ekrane, prikazuje se samo kad je drawer zatvoren */}
      {isMobile && !drawerOpen && (
        <IconButton
          color="primary"
          aria-label="open sidebar"
          onClick={handleDrawerOpen}
          sx={{
            position: "fixed",
            top: 72, // odmah ispod navbar-a (ako je navbar 64px visine, dodaj malo razmaka)
            left: 16,
            zIndex: 2000,
            background: "white",
            boxShadow: 1,
            borderRadius: 2
          }}
        >
          <MenuIcon />
        </IconButton>
      )}
      {/* Drawer za sidebar */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={handleDrawerClose}
        sx={{ display: { md: "none" } }}
      >
        <div style={{ width: 260, padding: 24 }}>
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
                  onClick={() => handleTagClick(tag.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    marginBottom: "6px",
                    cursor: "pointer",
                    padding: "4px 6px",
                    borderRadius: "6px",
                    border: tag.id === activeTagId ? "2px solid #1976d2" : "none",
                    backgroundColor: tag.id === activeTagId ? "#e3f2fd" : "transparent"
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
                  <span
                    style={{
                      flexGrow: 1,
                      fontWeight: tag.id === activeTagId ? "bold" : "normal",
                      color: tag.id === activeTagId ? "#000" : "#333"
                    }}
                  >
                    {tag.name}
                  </span>
                  <button
                    onClick={() => setTagToDelete(tag.id)}
                    style={{
                      marginLeft: "8px",
                      background: "transparent",
                      border: "none",
                      color: "#999",
                      cursor: "pointer",
                      fontWeight: "bold",
                      fontSize: "14px",
                      lineHeight: "1"
                    }}
                    title="Obriši tag"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div className="sidebar-section bottom-icons">
            <Link to={`/profil/${userId}`}>
              <UserIcon className="action-icon large-icon" />
            </Link>
          </div>
        </div>
      </Drawer>
      <div className="container">
        {/* Sidebar samo na velikim ekranima */}
        <div className="sidebar" style={{ display: isMobile ? "none" : "flex" }}>
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
                    onClick={() => handleTagClick(tag.id)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      marginBottom: "6px",
                      cursor: "pointer",
                      padding: "4px 6px",
                      borderRadius: "6px",
                      border: tag.id === activeTagId ? "2px solid #1976d2" : "none",
                      backgroundColor: tag.id === activeTagId ? "#e3f2fd" : "transparent"
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
                    <span
                      style={{
                        flexGrow: 1,
                        fontWeight: tag.id === activeTagId ? "bold" : "normal",
                        color: tag.id === activeTagId ? "#000" : "#333"
                      }}
                    >
                      {tag.name}
                    </span>
                    <button
                      onClick={() => setTagToDelete(tag.id)}
                      style={{
                        marginLeft: "8px",
                        background: "transparent",
                        border: "none",
                        color: "#999",
                        cursor: "pointer",
                        fontWeight: "bold",
                        fontSize: "14px",
                        lineHeight: "1"
                      }}
                      title="Obriši tag"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="sidebar-section bottom-icons">
            <Link to={`/profil/${userId}`}>
              <UserIcon className="action-icon large-icon" />
            </Link>
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
                     <FileDown
  className="action-icon"
  title="Preuzmi PDF"
  style={{ cursor: 'pointer' }}
  onClick={() => downloadPDF(project.id)}
/>

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
      fetchTags();
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
<Dialog
  open={!!tagToDelete}
  onClose={() => setTagToDelete(null)}
  PaperProps={{
    sx: {
      borderRadius: 3,
      padding: 2,
      minWidth: 360,
      boxShadow: 6,
    }
  }}
>
  <DialogTitle
    sx={{ fontWeight: 'bold', fontSize: 20, textAlign: 'center' }}
  >
    Da li sigurno želiš obrisati tag?
  </DialogTitle>

  <DialogActions sx={{ justifyContent: 'center', gap: 2, mt: 1 }}>
    <Button
      variant="outlined"
      onClick={() => setTagToDelete(null)}
      sx={{ borderRadius: 2, textTransform: 'none' }}
    >
      Odustani
    </Button>
    <Button
      variant="contained"
      color="error"
      onClick={deleteTag}
      sx={{ borderRadius: 2, textTransform: 'none' }}
    >
      Obriši
    </Button>
  </DialogActions>
</Dialog>



        </div>
      </div>



   
  );
}
