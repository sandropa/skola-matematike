import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Avatar, Modal, Box, TextField, Button, Typography } from '@mui/material';
import './Predavaci.css';

function Predavaci() {
  const [lecturers, setLecturers] = useState([]);
  const [openModal, setOpenModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newSurname, setNewSurname] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [searchTerm, setSearchTerm] = useState('');


  useEffect(() => {
    fetchLecturers();
  }, []);

  const fetchLecturers = () => {
    axios.get('http://localhost:8000/users')
      .then(res => setLecturers(res.data))
      .catch(err => console.error('Greška pri dohvaćanju predavača:', err));
  };

  const getInitials = (name, surname) =>
    `${name?.[0] || ''}${surname?.[0] || ''}`.toUpperCase();

  const handleAddLecturer = () => {
    const novi = { name: newName, surname: newSurname, email: newEmail };
    axios.post('http://localhost:8000/users', novi)
      .then(() => {
        fetchLecturers();
        setOpenModal(false);
        setNewName('');
        setNewSurname('');
        setNewEmail('');
      })
      .catch(err => console.error('Greška pri dodavanju predavača:', err));
  };

  const filteredLecturers = lecturers.filter((lecturer) =>
    (`${lecturer.name} ${lecturer.surname}`).toLowerCase().includes(searchTerm.toLowerCase()) ||
    lecturer.email.toLowerCase().includes(searchTerm.toLowerCase())
  );
  

  return (
    <>

     


      <nav className="navbar">
        <div className="navbar-left">
          <a href="/pocetna">
            <img src="/logo.png" className="navbar-logo" alt="Logo" />
          </a>
        </div>
        <div className="navbar-right">
        
        </div>
      </nav>

      <div className="users-container">
        <div className="users-content">
          <h1 className="users-title">Predavači</h1>

          <div className="users-search-and-filters">
            <div className="search-container">
              <div className="search-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </div>
              <input
  type="text"
  placeholder="Pretraga predavača"
  className="search-input"
  value={searchTerm}
  onChange={(e) => setSearchTerm(e.target.value)}
/>

            </div>

            <div className="filters-container">
              <button className="filter-button active" onClick={() => setOpenModal(true)}>
                Dodaj predavača
              </button>
            </div>
          </div>

          <div className="users-grid">
            {filteredLecturers.map((lecturer) => (

              <div className="user-card" key={lecturer.id}>
                <div className="user-avatar">
                  <Avatar sx={{ width: 80, height: 80 }}>
                    {getInitials(lecturer.name, lecturer.surname)}
                  </Avatar>
                </div>
                <div className="user-info">
                  <h3 className="user-name">{lecturer.name} {lecturer.surname}</h3>
                  <p className="user-location">{lecturer.email}</p>
                  <div className="user-tags">
                    {lecturer.tags?.map((tag, index) => (
                      <span className="tag" key={index}>{tag}</span>
                    ))}
                  </div>
                </div>
              </div>
            ))}



          </div>

          <div className="scroll-to-top" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 15l-6-6-6 6"/>
  </svg>
</div>

        </div>
      </div>

     
      <Modal open={openModal} onClose={() => setOpenModal(false)}>
  <Box
    sx={{
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      bgcolor: '#ffffff',
      borderRadius: 3,
      boxShadow: 24,
      width: 420,
      p: 4,
      display: 'flex',
      flexDirection: 'column',
      gap: 3
    }}
  >
    <Typography variant="h6" sx={{ color: '#1e293b', fontWeight: 600 }}>
      Dodaj novog predavača
    </Typography>

    <TextField
      label="Ime"
      variant="outlined"
      value={newName}
      onChange={e => setNewName(e.target.value)}
      fullWidth
    />
    <TextField
      label="Prezime"
      variant="outlined"
      value={newSurname}
      onChange={e => setNewSurname(e.target.value)}
      fullWidth
    />
    <TextField
      label="Email"
      type="email"
      variant="outlined"
      value={newEmail}
      onChange={e => setNewEmail(e.target.value)}
      fullWidth
    />

    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 1 }}>
      <Button
        onClick={() => setOpenModal(false)}
        variant="outlined"
        sx={{
          color: '#1e293b',
          borderColor: '#cbd5e1',
          '&:hover': {
            borderColor: '#1e293b',
            backgroundColor: '#f1f5f9'
          }
        }}
      >
        Otkaži
      </Button>

      <Button
        onClick={handleAddLecturer}
        variant="contained"
        sx={{
          backgroundColor: '#1d4ed8',
          '&:hover': {
            backgroundColor: '#1e40af'
          }
        }}
      >
        Pošalji invite
      </Button>
    </Box>
  </Box>
</Modal>

    </>
  );
}

export default Predavaci;
