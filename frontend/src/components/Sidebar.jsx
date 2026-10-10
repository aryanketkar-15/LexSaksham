import React from 'react';
import { LayoutDashboard, FileText, UploadCloud, PieChart, Scale, LogOut } from 'lucide-react';

const Sidebar = ({ role, activeTab, setActiveTab, onLogout }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'contracts', label: 'My Contracts', icon: FileText },
    { id: 'upload', label: 'New Analysis', icon: UploadCloud },
    { id: 'analytics', label: 'Risk Analytics', icon: PieChart },
  ];

  if (role === 'lawyer') {
    menuItems.push({ id: 'judgments', label: 'Supreme Court', icon: Scale });
  }

  return (
    <div className="w-64 bg-[#1F3C88] text-white flex flex-col h-screen shadow-xl fixed left-0 top-0 z-50">
      <div className="p-6 border-b border-blue-800">
        <h1 className="text-2xl font-bold tracking-wide flex items-center gap-2">
          <Scale className="w-8 h-8" /> LexSaksham
        </h1>
        <p className="text-xs text-blue-200 mt-1 uppercase tracking-wider">{role} Mode</p>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              activeTab === item.id 
                ? 'bg-white text-[#1F3C88] font-semibold shadow-md' 
                : 'text-blue-100 hover:bg-blue-800'
            }`}
          >
            <item.icon size={20} />
            {item.label}
          </button>
        ))}
      </nav>
      <div className="p-4 border-t border-blue-800">
        <button onClick={onLogout} className="w-full flex items-center gap-3 px-4 py-3 text-red-200 hover:bg-blue-900 rounded-lg transition-colors">
          <LogOut size={20} /> Logout
        </button>
      </div>
    </div>
  );
};

export default Sidebar;