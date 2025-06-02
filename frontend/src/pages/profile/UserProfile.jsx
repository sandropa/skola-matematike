import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import './profile.css';

function Profil() {
  const { id } = useParams();
  const [user, setUser] = useState({
    firstName: '',
    lastName: '',
    email: '',
    profileImage: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [activeTab, setActiveTab] = useState('personal');

  const token = localStorage.getItem('token');

  // Dohvati korisnika pri učitavanju
  useEffect(() => {
    axios.get(`http://localhost:8000/users/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    .then(res => {
      console.log(res.data)
      const { name, surname, email, profile_image } = res.data;
      setUser({
        firstName: name,
        lastName: surname,
        email: email,
        profileImage: profile_image || ''
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
      alert('Profil uspješno ažuriran');
    })
    .catch(err => {
      console.error('Greška pri ažuriranju:', err);
      alert('Došlo je do greške.');
    });
  };

  const handlePasswordChange = (e) => {
    e.preventDefault();
    console.log("password", user)
    if (user.newPassword.length < 8) {
      alert('Nova lozinka mora imati najmanje 8 karaktera.');
      return;
    }

    if (user.newPassword !== user.confirmPassword) {
      alert('Lozinke se ne podudaraju.');
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
      alert('Lozinka uspješno promijenjena.');
      setUser({...user, currentPassword: '', newPassword: '', confirmPassword: ''})
    })
    .catch(err => {
      console.error('Greška pri promjeni lozinke:', err);
      if (err.response && err.response.data && err.response.data.detail) {
        alert(`Greška: ${err.response.data.detail}`);
      } else {
        alert('Došlo je do greške prilikom promjene lozinke.');
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
    alert("Slika uspješno uploadovana.");
  })
  .catch(err => {
    console.error('Greška pri uploadu slike:', err);
    alert('Došlo je do greške prilikom uploada slike.');
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
    alert("Profilna slika je uklonjena.");
  })
  .catch(err => {
    console.error('Greška pri uklanjanju slike:', err);
    alert("Došlo je do greške.");
  });
};



  return (
    <div>
      <nav className="navbar">
        <div className="navbar-left">
          <a href="pocetna">
            <img src="/logo.png" className="navbar-logo" alt="Logo" />
          </a>
        </div>
        <div className="navbar-right">
          <div className="navbar-item">Predavači</div>
        </div>
      </nav>

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
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profil;
