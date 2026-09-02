// File Name: TeacherLayout.jsx
// Description: Global master layout providing unified Header and TeacherSidebar with dynamic module Outlet.
// Created At: 2026-09-02
// Created By: Tam Khang
// Updated At: 2026-09-02
// Updated By: Tam Khang

import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../common/Header';
import TeacherSidebar from '../teacher/TeacherSidebar';
import './TeacherLayout.css';

export default function TeacherLayout() {
  const [showSidebar, setShowSidebar] = useState(true);

  return (
    <div className="teacher-global-layout">
      {/* 1. Global Persistent Header */}
      <Header onToggleSidebar={() => setShowSidebar(prev => !prev)} />

      <div className="teacher-global-body">
        {/* 2. Global Persistent Sidebar */}
        {showSidebar && <TeacherSidebar />}

        {/* 3. Dynamic Module Body */}
        <main className="teacher-global-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
