import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import LectureView from './components/LectureView';
import Login from './pages/login/Login';

import UserProfile from "./pages/profile/UserProfile";

import PocetnaStranica from './pages/pocetna/PocetnaStranica';
import Predavaci from './pages/Predavaci/Predavaci';

import AcceptInvite from  './pages/login/AcceptInvite';
import ResetPassword from  './pages/login/ResetPassword';
import ResetPasswordRequest from  './pages/login/ResetPasswordRequest';
import './App.css';
import Navbar from './components/Navbar';

import LatexEditor from './pages/LatexEditor';
import { Navigate } from 'react-router-dom';


function App() {
  const location = useLocation();
  const role = localStorage.getItem('role');
const token = localStorage.getItem('token');



const hideNavbarOnRoutes = [
  "/",
  "/reset-password",
  "/forgot-password"
];

const isInviteRoute = location.pathname.startsWith("/accept-invite");

const showNavbar = !hideNavbarOnRoutes.includes(location.pathname) && !isInviteRoute;

return (
  <div className="App">
    {showNavbar && <Navbar />}

    <Routes>
  {}
  <Route path="/" element={<Login />} />
  <Route path="/reset-password" element={<ResetPassword />} />
  <Route path="/forgot-password" element={<ResetPasswordRequest />} />
  <Route path="/accept-invite/:inviteId" element={<AcceptInvite />} />

  {}
  {token ? (
    <>
      <Route path="/editor" element={<LatexEditor />} />
      <Route path="/editor/:id" element={<LatexEditor />} />
      <Route path="/lecture/:id" element={<LectureView />} />
      <Route path="/profil/:id" element={<UserProfile />} />
      <Route path="/pocetna" element={<PocetnaStranica />} />
      <Route path="/predavaci" element={<Predavaci />} />
      <Route path="*" element={<div>404: Page Not Found</div>} />
    </>
  ) : (
    <Route path="*" element={<Navigate to="/login" />} />
  )}
</Routes>

  </div>
);

}

export default App;
