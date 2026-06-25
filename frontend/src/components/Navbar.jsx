import React from 'react';
import { Menu, Bell, User, ShieldCheck } from 'lucide-react';

const Navbar = ({ onToggleSidebar }) => {
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between h-16 px-6 bg-white border-b border-slate-200 shadow-sm">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 text-slate-500 rounded-xl hover:bg-slate-50 lg:hidden focus:outline-none"
        >
          <Menu className="w-6 h-6" />
        </button>
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-xs font-medium border border-emerald-100">
          <ShieldCheck className="w-4 h-4" />
          <span>HIPAA & HITECH Compliance Guard Enabled</span>
        </div>
      </div>

      {/* Action Indicators */}
      <div className="flex items-center gap-4">
        <button className="p-2 text-slate-500 rounded-xl hover:bg-slate-50 relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full" />
        </button>
        
        <div className="h-8 w-px bg-slate-200" />
        
        {/* User Profile */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-teal-600 text-white rounded-full flex items-center justify-center font-bold shadow-sm">
            Dr
          </div>
          <div className="hidden md:block text-left">
            <p className="text-xs font-semibold text-slate-900 leading-none">Dr. Alexander</p>
            <span className="text-[10px] text-slate-500 font-medium">Chief Security Officer</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
