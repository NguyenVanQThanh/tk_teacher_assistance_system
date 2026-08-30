// File Name: App.jsx
// Description: Main Application Component for SmartLMS frontend.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React from 'react';

export default function App() {
  return (
    <div className="container">
      <div className="hero">
        <span className="status-badge">SmartLMS Frontend Ready</span>
        <h1>SmartLMS — Teacher Assistance System</h1>
        <p>
          AI-driven LMS with Learning Analytics, Exercise Management, and Personalized Recommendations.
        </p>

        <div className="grid">
          <div className="card">
            <h3>Backend API</h3>
            <p>FastAPI service running on port 8000 with RBAC, PostgreSQL, and Alembic migrations.</p>
          </div>
          <div className="card">
            <h3>Exercise & AI</h3>
            <p>Smart document parser, math benchmark importer, and automated exercise generation.</p>
          </div>
          <div className="card">
            <h3>Analytics & Tracking</h3>
            <p>Real-time learning behavior analysis, radar charts, and student performance dashboard.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
