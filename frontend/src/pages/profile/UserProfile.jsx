import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import './profile.css';
import { Snackbar, Alert } from '@mui/material';


function Profil() {
  const { id } = useParams();
  const [user, setUser] = useState({
    firstName: '',
    lastName: '',
    email: '',
    profileImage: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    hasPassword: true 
    
  });
  const [activeTab, setActiveTab] = useState('personal');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMsg, setSnackbarMsg] = useState('');
  const [snackbarType, setSnackbarType] = useState('success')
  const showSnackbar = (msg, type = 'success') => {
  setSnackbarMsg(msg);
  setSnackbarType(type);
  setSnackbarOpen(true);
};


  const token = localStorage.getItem('token');


  useEffect(() => {
    axios.get(`http://localhost:8000/users/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    .then(res => {
      console.log(res.data)
      const { name, surname, email, profile_image,password } = res.data;
      setUser({
        firstName: name,
        lastName: surname,
        email: email,
        profileImage: profile_image || '',
        hasPassword: password !== null
      });
    })
    .catch(err => {
      console.error('Greška pri dohvatu profila:', err);
    });
  }, [token]);

  const handleProfileUpdate = (e) => {
    e.preventDefault();
    axios.put(`http://localhost:8000/users/${id}/`, {
      name: user.firstName,
      surname: user.lastName
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    .then(() => {
     showSnackbar('Profil uspješno ažuriran');

    })
    .catch(err => {
      console.error('Greška pri ažuriranju:', err);
      showSnackbar('Došlo je do greške.',"error");
    });
  };

  const handlePasswordChange = (e) => {
    e.preventDefault();
    console.log("password", user)
    if (user.newPassword.length < 8) {
    showSnackbar('Nova lozinka mora imati najmanje 8 karaktera.',"error");
      return;
    }

    if (user.newPassword !== user.confirmPassword) {
      showSnackbar('Lozinke se ne podudaraju.',"error");
      return;
    }

    axios.put(`http://localhost:8000/users/${id}/password`, {
      current_password: user.currentPassword,
      new_password: user.newPassword,
      confirm_password: user.confirmPassword
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    .then(() => {
      showSnackbar('Lozinka uspješno promijenjena.');
      setUser({...user, currentPassword: '', newPassword: '', confirmPassword: ''})
    })
    .catch(err => {
      console.error('Greška pri promjeni lozinke:', err);
      if (err.response && err.response.data && err.response.data.detail) {
        showSnackbar(`Greška: ${err.response.data.detail}`);
      } else {
        showSnackbar('Došlo je do greške prilikom promjene lozinke.',"error");
      }
    });
  };

  const handleImageUpload = (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  axios.post(`http://localhost:8000/users/${id}/upload-photo`, formData, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'multipart/form-data'
    }
  })
  .then(res => {
    setUser(prev => ({ ...prev, profileImage: res.data.image_path }));
    showSnackbar("Slika uspješno uploadovana.");
  })
  .catch(err => {
    console.error('Greška pri uploadu slike:', err);
    showSnackbar('Došlo je do greške prilikom uploada slike.',"error");
  });
};



const handleRemovePhoto = () => {
  axios.delete(`http://localhost:8000/users/${id}/delete-photo`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
  .then(() => {
    setUser(prev => ({ ...prev, profileImage: '' }));
    showSnackbar("Profilna slika je uklonjena.");
  })
  .catch(err => {
    console.error('Greška pri uklanjanju slike:', err);
    showSnackbar("Došlo je do greške.","error");
  });
};

const handleSetPassword = (e) => {
  e.preventDefault();

  if (user.newPassword.length < 8) {
    showSnackbar('Lozinka mora imati najmanje 8 karaktera.', "error");
    return;
  }

  if (user.newPassword !== user.confirmPassword) {
    showSnackbar('Lozinke se ne poklapaju.', "error");
    return;
  }

  axios.post(`http://localhost:8000/users/${id}/set-password`, {
    new_password: user.newPassword,
    confirm_password: user.confirmPassword
  }, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
    .then(() => {
      showSnackbar('Lozinka uspješno postavljena.');
      setUser(prev => ({
        ...prev,
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        hasPassword: true  
      }));
    })
    .catch(err => {
      console.error('Greška pri postavljanju lozinke:', err);
      showSnackbar('Došlo je do greške.', "error");
    });
};


  return (
    <>
    <div>
 

      <div className="profile-container">
        <div className="profile-sidebar">
          <div className="profile-image-container">
            {user.profileImage ? (
              <>
              <img
  src={`http://localhost:8000${user.profileImage}`}
  alt="Profile"
  className="profile-image"
/>

               <div className="image-overlay">
  <label className="change-photo-btn">
    Promijeni
    <input
      type="file"
      accept="image/*"
      style={{ display: 'none' }}
      onChange={handleImageUpload}
    />
  </label>
  <button
  className="remove-photo-btn"
  onClick={handleRemovePhoto}
>
  Ukloni
</button>

</div>

              </>
            ) : (
              <>
                <div className="initials-circle">
                  {user.firstName[0]}{user.lastName[0]}
                </div>
                <div className="image-overlay">
  <label className="change-photo-btn">
    Promijeni
    <input
      type="file"
      accept="image/*"
      style={{ display: 'none' }}
      onChange={handleImageUpload}
    />
  </label>
  <button
  className="remove-photo-btn"
  onClick={handleRemovePhoto}
>
  Ukloni
</button>

</div>

              </>
            )}
          </div>

          <div className="user-info">
            <h2>{`${user.firstName} ${user.lastName}`}</h2>
            <p className="userEmail">{user.email}</p>
          </div>
        </div>

        <div className="profile-content">
          <div className="profile-header">
            <h1>Postavke</h1>
            <div className="tab-navigation">
              <button
                className={`tab-btn ${activeTab === 'personal' ? 'active' : ''}`}
                onClick={() => setActiveTab('personal')}
              >
                Osobni podaci
              </button>
              <button
                className={`tab-btn ${activeTab === 'security' ? 'active' : ''}`}
                onClick={() => setActiveTab('security')}
              >
                Lozinka
              </button>
            </div>
          </div>

          <div className="profile-sections">
            {activeTab === 'personal' && (
              <section className="profile-section">
                <div className="section-header">
                  <h2>Osobni podaci</h2>
                  <p>Ažuriraj lične podatke i javni profil.</p>
                </div>
                <form onSubmit={handleProfileUpdate}>
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="firstName">Ime</label>
                      <input
                        type="text"
                        id="firstName"
                        value={user.firstName}
                        onChange={(e) => setUser({ ...user, firstName: e.target.value })}
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="lastName">Prezime</label>
                      <input
                        type="text"
                        id="lastName"
                        value={user.lastName}
                        onChange={(e) => setUser({ ...user, lastName: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="email">Email</label>
                    <input
                      type="email"
                      id="email"
                      value={user.email}
                      disabled={true}
                    />
                  </div>

                  <button type="submit" className="save-btn">Sačuvaj promjene</button>
                </form>
              </section>
            )}

           {activeTab === 'security' && (
  <section className="profile-section">
    <div className="section-header">
      <h2>Sigurnosne postavke</h2>
      <p>Postavi lozinku i prilagodi sigurnosne opcije.</p>
    </div>

    {!user.hasPassword ? (
      <form onSubmit={handleSetPassword}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="newPassword">Nova lozinka</label>
            <input
              type="password"
              id="newPassword"
              onChange={(e) => setUser({ ...user, newPassword: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label htmlFor="confirmPassword">Potvrdi lozinku</label>
            <input
              type="password"
              id="confirmPassword"
              onChange={(e) => setUser({ ...user, confirmPassword: e.target.value })}
            />
          </div>
        </div>
        <button type="submit" className="save-btn">Postavi lozinku</button>
      </form>
    ) : (
      <form onSubmit={handlePasswordChange}>
        <div className="form-group">
          <label htmlFor="currentPassword">Trenutna lozinka</label>
          <input
            type="password"
            id="currentPassword"
            onChange={(e) => setUser({ ...user, currentPassword: e.target.value })}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="newPassword">Nova lozinka</label>
            <input
              type="password"
              id="newPassword"
              onChange={(e) => setUser({ ...user, newPassword: e.target.value })}
            />
            <span className="password-hint">Treba imati minimalno 8 karaktera</span>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Unesite ponovo lozinku</label>
            <input
              type="password"
              id="confirmPassword"
              onChange={(e) => setUser({ ...user, confirmPassword: e.target.value })}
            />
          </div>
        </div>

        <button type="submit" className="save-btn">Sačuvaj</button>
      </form>
    )}
  </section>
)}

          </div>
        </div>
      </div>
    </div>
    <Snackbar
      open={snackbarOpen}
      autoHideDuration={4000}
      onClose={() => setSnackbarOpen(false)}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      <Alert
        onClose={() => setSnackbarOpen(false)}
        severity={snackbarType}
        sx={{ width: '100%' }}
      >
        {snackbarMsg}
      </Alert>
    </Snackbar>
    </>
  );
}


export default Profil;
