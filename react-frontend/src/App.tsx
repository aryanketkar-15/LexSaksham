import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { ContractsProvider } from './context/ContractsContext';
import { NotificationsProvider } from './context/NotificationsContext';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import UserDashboard from './components/UserDashboard';
import LawyerDashboard from './components/LawyerDashboard';
import ContractList from './components/ContractList';
import ContractUpload from './components/ContractUpload';
import ContractDetails from './components/ContractDetails';
import AIAnalytics from './components/AIAnalytics';
import VoiceInterface from './components/VoiceInterface';
import Notifications from './components/Notifications';
import ChatBot from './components/ChatBot';
import LegalResearch from './components/LegalResearch';
import Layout from './components/Layout';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  const handleLogin = (userData) => {
    setIsAuthenticated(true);
    setCurrentUser(userData);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

  if (!isAuthenticated) {
    return (
      <Router>
        <div className="min-h-screen bg-background">
          <Routes>
            <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/register" element={<RegisterPage onRegister={handleLogin} />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
          <Toaster />
        </div>
      </Router>
    );
  }

  // Determine which dashboard to show based on role
  const DashboardComponent = currentUser?.role === 'Lawyer' ? LawyerDashboard : UserDashboard;

  return (
    <ContractsProvider>
      <NotificationsProvider>
        <Router>
        <Layout currentUser={currentUser} onLogout={handleLogout}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardComponent />} />
            <Route path="/contracts" element={<ContractList />} />
            <Route path="/contracts/:id" element={<ContractDetails currentUser={currentUser} />} />
            <Route path="/upload" element={<ContractUpload />} />
            <Route path="/analytics" element={<AIAnalytics />} />
            <Route path="/voice" element={<VoiceInterface />} />
            <Route path="/chat" element={<ChatBot currentUser={currentUser} />} />
            <Route path="/legal-research" element={currentUser?.role === 'Lawyer' ? <LegalResearch /> : <Navigate to="/dashboard" replace />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Layout>
        <Toaster />
      </Router>
      </NotificationsProvider>
    </ContractsProvider>
  );
}
