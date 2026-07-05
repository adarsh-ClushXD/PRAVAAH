import React, { useState } from 'react';
import { Bell, ChevronDown, RefreshCw, Lock, User, LogOut } from 'lucide-react';
import { usePravaahStore } from '../../store/pravaahStore';
import { useAuthStore } from '../../store/authStore';

export default function Header() {
  const { lastUpdated, syncAllDistricts, isSyncing, syncProgress } = usePravaahStore();
  const { isAuthenticated, openLoginModal, logout } = useAuthStore();
  
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const formattedDate = lastUpdated 
    ? new Date(lastUpdated).toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    : '12 May 2025 | 10:30 AM';

  const syncLabel = isSyncing && syncProgress
    ? `Syncing ${syncProgress.current}/${syncProgress.total}...`
    : 'Sync State';

  return (
    <header className="flex-none h-16 flex items-center justify-between px-6 border-b border-navy-800 bg-navy-950 text-white">
      {/* Title */}
      <div className="flex-1">
        <h2 className="text-lg font-semibold tracking-wide text-gray-100">
          West Bengal Flood Intelligence System
        </h2>
      </div>

      {/* Meta & User Profile */}
      <div className="flex items-center space-x-6">
        <div className="text-xs text-gray-400 font-mono">
          Last Updated: {formattedDate}
        </div>
        
        <div className="relative group">
          <button 
            onClick={() => isAuthenticated && syncAllDistricts(false)}
            disabled={isSyncing || !isAuthenticated}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors border ${
              isSyncing || !isAuthenticated
                ? 'bg-navy-800 text-gray-500 border-navy-700 cursor-not-allowed opacity-60' 
                : 'bg-navy-800 text-cyan-glow border-cyan-glow/30 hover:bg-navy-700'
            }`}
          >
            {!isAuthenticated ? (
              <Lock size={14} className="text-gray-500" />
            ) : (
              <RefreshCw size={16} className={isSyncing ? 'animate-spin' : ''} />
            )}
            <span>{syncLabel}</span>
          </button>
          
          {/* Tooltip for Locked State */}
          {!isAuthenticated && (
            <div className="absolute top-full right-0 mt-2 w-48 p-2 bg-navy-800 border border-navy-700 rounded-md shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <p className="text-xs text-gray-300 text-center">Login to access this operational feature.</p>
            </div>
          )}
        </div>

        <button className="relative p-2 text-gray-400 hover:text-white transition-colors">
          <Bell size={20} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-risk-critical rounded-full border border-navy-950"></span>
        </button>

        {/* Authentication State */}
        {isAuthenticated ? (
          <div className="relative">
            <button 
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-md hover:bg-navy-800 transition-colors border border-transparent hover:border-navy-700"
            >
              <div className="w-7 h-7 rounded-full bg-cyan-glow/20 flex items-center justify-center text-sm font-medium text-cyan-glow border border-cyan-glow/30">
                <User size={14} />
              </div>
              <span className="text-sm font-medium text-cyan-glow">Authenticated User</span>
              <ChevronDown size={16} className="text-cyan-glow/70" />
            </button>
            
            {/* Dropdown Menu */}
            {isDropdownOpen && (
              <div className="absolute top-full right-0 mt-1 w-48 bg-navy-900 border border-navy-700 rounded-lg shadow-xl overflow-hidden z-50">
                <button 
                  onClick={() => {
                    logout();
                    setIsDropdownOpen(false);
                  }}
                  className="w-full flex items-center space-x-2 px-4 py-3 text-sm text-gray-300 hover:bg-navy-800 hover:text-white transition-colors"
                >
                  <LogOut size={16} />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <button 
            onClick={openLoginModal}
            className="flex items-center space-x-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-md transition-colors"
          >
            <User size={16} />
            <span>Login</span>
          </button>
        )}
      </div>
    </header>
  );
}
