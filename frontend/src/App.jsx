import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import LectureView from './components/LectureView';
import Login from './pages/login/Login';

import UserProfile from "./pages/profile/UserProfile";

import PocetnaStranica from './pages/pocetna/PocetnaStranica';
import Predavaci from './pages/predavaci/Predavaci';
import AcceptInvite from  './pages/login/AcceptInvite';
import ResetPassword from  './pages/login/ResetPassword';
import ResetPasswordRequest from  './pages/login/ResetPasswordRequest';
import './App.css';
import LatexEditor from './pages/LatexEditor';

function App() {
  const location = useLocation();

  return (
    <div className="App">
      {/*location.pathname !== "/login" && (
        <>
          <nav>
            
          </nav>
        </>
      )*/}

      <Routes>
        <Route path="/editor" element={<LatexEditor />} />
        <Route path="/lecture/:id" element={<LectureView />} />
        <Route path="/profil/:id" element={<UserProfile />} />
        <Route path="/login" element={<Login />} />
        <Route path='/pocetna' element={<PocetnaStranica />}/>
        <Route path='/predavaci' element={<Predavaci />}/>
        <Route path="/accept-invite/:inviteId" element={<AcceptInvite />} />
        <Route path="*" element={<div>404: Page Not Found</div>} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/forgot-password" element={<ResetPasswordRequest />} />
      </Routes>
    </div>
  );
}

export default App;
