import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Shield, 
  Home, 
  Upload, 
  History, 
  BarChart2, 
  Settings as SettingsIcon,
  Server,
  ScanSearch,
} from 'lucide-react';

const Sidebar = ({ isOpen, systemStatus }) => {
  const menuItems = [
    { name: 'Dashboard', path: '/', icon: Home },
    { name: 'Upload Note', path: '/upload', icon: Upload },
    { name: 'Detection', path: '/detection', icon: ScanSearch },
    { name: 'Audit Logs', path: '/audit-logs', icon: History },
    { name: 'Statistics', path: '/statistics', icon: BarChart2 },
    { name: 'Settings', path: '/settings', icon: SettingsIcon },
  ];

  return (
    <aside className={`fixed inset-y-0 left-0 z-30 w-64 bg-slate-900 text-white transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      {/* Brand Header */}
      <div className="flex items-center justify-between px-6 h-16 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-teal-500/10 rounded-lg">
            <Shield className="w-6 h-6 text-teal-400" />
          </div>
          <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            HealthTech PHI
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-teal-600 text-white shadow-lg shadow-teal-600/20'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                }`
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* System Status / Health Widget */}
      <div className="p-4 m-4 bg-slate-800/40 border border-slate-800 rounded-2xl">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-slate-800 rounded-lg">
            <Server className="w-4 h-4 text-slate-400" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold text-slate-300">Backend API</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${systemStatus === 'running' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              <span className="text-[10px] text-slate-400 font-medium capitalize">
                {systemStatus || 'Connecting...'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
