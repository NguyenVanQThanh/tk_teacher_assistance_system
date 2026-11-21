// File Name: TeacherLayout.jsx
// Description: Global master layout providing unified Header and TeacherSidebar with dynamic module Outlet.
// Created At: 2026-09-02
// Created By: Tam Khang
// Updated At: 2026-09-02
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Header from '../common/Header';
import TeacherSidebar from '../teacher/TeacherSidebar';
import './TeacherLayout.css';

export default function TeacherLayout() {
  const [showSidebar, setShowSidebar] = useState(() => window.innerWidth > 992);
  const { pathname } = useLocation();

  // Auto-close the drawer on mobile after navigation
  useEffect(() => {
    if (window.innerWidth <= 992) setShowSidebar(false);
  }, [pathname]);

  return (
    <div className="teacher-global-layout">
      {/* 1. Global Persistent Header */}
      <Header onToggleSidebar={() => setShowSidebar(prev => !prev)} />

      <div className="teacher-global-body">
        {/* 2. Global Persistent Sidebar */}
        {showSidebar && <div className="teacher-sidebar-backdrop" onClick={() => setShowSidebar(false)} />}
        {showSidebar && <TeacherSidebar />}

        {/* 3. Dynamic Module Body */}
        <main className="teacher-global-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
