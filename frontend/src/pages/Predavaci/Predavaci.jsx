import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Avatar, Modal, Box, TextField, Button, Typography } from '@mui/material';
import { Snackbar, Alert } from '@mui/material';

import './Predavaci.css';
import EditIcon from '@mui/icons-material/Edit';



function Predavaci() {
  const [lecturers, setLecturers] = useState([]);
  const [openModal, setOpenModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newSurname, setNewSurname] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [newRole, setNewRole] = useState('user');
  const [selectedLecturer, setSelectedLecturer] = useState(null);
  const [roleUpdateModalOpen, setRoleUpdateModalOpen] = useState(false);
  const [updatedRole, setUpdatedRole] = useState('');





  useEffect(() => {
    fetchLecturers();
  }, []);

  const fetchLecturers = () => {
    axios.get('http://localhost:8000/users')
      .then(res => setLecturers(res.data))
      .catch(err => console.error('Greška pri dohvaćanju predavača:', err));
  };
  const openRoleModal = (lecturer) => {
  setSelectedLecturer(lecturer);
  setUpdatedRole(lecturer.role || 'user');
  setRoleUpdateModalOpen(true);
};

  const getInitials = (name, surname) =>
    `${name?.[0] || ''}${surname?.[0] || ''}`.toUpperCase();

  const handleAddLecturer = () => {
    const novi = { name: newName, surname: newSurname, to_email: newEmail, role: newRole };
    axios.post('http://localhost:8000/users/send-invite', novi)
      .then(() => {
        fetchLecturers();
        setOpenModal(false);
        setNewName('');
        setNewSurname('');
        setNewEmail('');
         setShowSuccess(true)
      })
    .catch(err => {
  console.error('Greška pri dodavanju predavača:', err);
  setErrorMessage('Email nije ispravan ili već postoji.');
  setShowError(true);
});

};

  const filteredLecturers = lecturers.filter((lecturer) =>
    (`${lecturer.name} ${lecturer.surname}`).toLowerCase().includes(searchTerm.toLowerCase()) ||
    lecturer.email.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const handleRoleUpdate = () => {
  axios.put(`http://localhost:8000/users/${selectedLecturer.id}/role`, {
    role: updatedRole
  })
    .then(() => {
      setRoleUpdateModalOpen(false);
      fetchLecturers(); 
    })
    .catch(err => {
      console.error('Greška pri izmjeni uloge:', err);
      alert('Greška pri izmjeni uloge.');
    });
};


  return (
    <>

     


      

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
                 <Avatar
  sx={{ width: 80, height: 80 }}
  src={lecturer.profile_image ? `http://localhost:8000${lecturer.profile_image}` : undefined}
>
  {!lecturer.profile_image && getInitials(lecturer.name, lecturer.surname)}
</Avatar>

                </div>
                <div className="user-info">
                  <h3 className="user-name">{lecturer.name} {lecturer.surname}</h3>
                  <p className="user-email">{lecturer.email}</p>
                  <div className="edit-icon" onClick={() => openRoleModal(lecturer)} title="Uredi ulogu">
  <EditIcon style={{ fontSize: 20 }} />
</div>

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
    <TextField
  label="Uloga"
  select
  value={newRole}
  onChange={e => setNewRole(e.target.value)}
  fullWidth
  SelectProps={{ native: true }}
>
  <option value="user">User</option>
  <option value="admin">Admin</option>
</TextField>


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

<Snackbar
  open={showSuccess}
  autoHideDuration={4000}
  onClose={() => setShowSuccess(false)}
  anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
>
  <Alert onClose={() => setShowSuccess(false)} severity="success" sx={{ width: '100%' }}>
    Pozivnica je uspješno poslana!
  </Alert>
</Snackbar>

<Snackbar
  open={showError}
  autoHideDuration={5000}
  onClose={() => setShowError(false)}
  anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
>
  <Alert onClose={() => setShowError(false)} severity="error" sx={{ width: '100%' }}>
    {errorMessage}
  </Alert>
</Snackbar>
<Modal open={roleUpdateModalOpen} onClose={() => setRoleUpdateModalOpen(false)}>
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
    <Typography variant="h6">Promjena uloge</Typography>

    <Typography variant="body1">
      {selectedLecturer?.name} {selectedLecturer?.surname} ({selectedLecturer?.email})
    </Typography>

    <TextField
      select
      label="Uloga"
      value={updatedRole}
      onChange={(e) => setUpdatedRole(e.target.value)}
      SelectProps={{ native: true }}
      fullWidth
    >
      <option value="user">User</option>
      <option value="admin">Admin</option>
    </TextField>

    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
      <Button onClick={() => setRoleUpdateModalOpen(false)}>Otkaži</Button>
      <Button variant="contained" onClick={handleRoleUpdate}>Sačuvaj</Button>
    </Box>
  </Box>
</Modal>

    </>
  );

}

export default Predavaci;
