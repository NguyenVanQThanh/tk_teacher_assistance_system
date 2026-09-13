// File Name: StudentLayout.jsx
// Description: Master layout wrapper providing unified top StudentHeader and persistent StudentSidebar with dynamic module Outlet.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-12
// Updated By: Tam Khang

import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import StudentHeader from '../student/StudentHeader';
import StudentSidebar from '../student/StudentSidebar';
import './StudentLayout.css';

export default function StudentLayout() {
  const [showSidebar, setShowSidebar] = useState(true);

  return (
    <div className="student-global-layout">
      {/* 1. Global Persistent Header across top */}
      <StudentHeader onToggleSidebar={() => setShowSidebar(prev => !prev)} />

      <div className="student-global-body">
        {/* 2. Global Persistent Sidebar */}
        {showSidebar && <StudentSidebar />}

        {/* 3. Dynamic Module Body */}
        <main className="student-global-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
