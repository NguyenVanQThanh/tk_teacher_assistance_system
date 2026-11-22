// File Name: StudentLayout.jsx
// Description: Master layout wrapper providing unified top StudentHeader and persistent StudentSidebar with dynamic module Outlet.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-12
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import StudentHeader from '../student/StudentHeader';
import StudentSidebar from '../student/StudentSidebar';
import './StudentLayout.css';

export default function StudentLayout() {
  const [showSidebar, setShowSidebar] = useState(() => window.innerWidth > 992);
  const { pathname } = useLocation();

  // Mobile drawer: close on navigation and sync with viewport changes
  useEffect(() => {
    if (window.innerWidth <= 992) setShowSidebar(false);
  }, [pathname]);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 992px)');
    const onChange = (e) => setShowSidebar(!e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  return (
    <div className="student-global-layout">
      {/* 1. Global Persistent Header across top */}
      <StudentHeader onToggleSidebar={() => setShowSidebar(prev => !prev)} />

      <div className="student-global-body">
        {/* 2. Global Persistent Sidebar */}
        {showSidebar && <div className="student-sidebar-backdrop" onClick={() => setShowSidebar(false)} />}
        {showSidebar && <div className="student-sidebar-wrap" onClick={(e) => { if (window.innerWidth <= 992 && e.target.closest("button, a")) setShowSidebar(false); }}><StudentSidebar /></div>}

        {/* 3. Dynamic Module Body */}
        <main className="student-global-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
