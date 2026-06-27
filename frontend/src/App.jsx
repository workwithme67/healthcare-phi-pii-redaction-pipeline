import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import ClinicalUpload from './pages/ClinicalUpload';
import AuditLogs from './pages/AuditLogs';
import Statistics from './pages/Statistics';
import Settings from './pages/Settings';
import Detection from './pages/Detection';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="upload" element={<ClinicalUpload />} />
          <Route path="detection" element={<Detection />} />
          <Route path="audit-logs" element={<AuditLogs />} />
          <Route path="statistics" element={<Statistics />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

