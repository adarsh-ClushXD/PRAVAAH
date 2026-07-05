import React from 'react';
import { usePravaahStore } from '../../store/pravaahStore';

const NavItem = ({ icon, label, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center space-x-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-600 text-white'
        : 'text-gray-400 hover:text-white hover:bg-navy-800'
    }`}
  >
    <span className="text-lg">{icon}</span>
    <span>{label}</span>
  </button>
);

const Sidebar = () => {
  const { currentAnalysis: analysis, activePanel, setActivePanel } = usePravaahStore();
  const confidence = analysis?.confidence_score ? Math.round(analysis.confidence_score * 100) : 88;

  const navItems = [
    { id: 'dashboard', icon: '⊞', label: 'Dashboard' },
    { id: 'live', icon: '◉', label: 'Live Overview' },
    { id: 'map', icon: '🗺️', label: 'District Risk Map' },
    { id: 'river', icon: '🌊', label: 'River Monitoring' },
    { id: 'weather', icon: '🌧️', label: 'Weather & Rainfall' },
    { id: 'scenarios', icon: '⚡', label: 'Scenarios' },
    { id: 'reports', icon: '📊', label: 'Reports & Insights' },
    { id: 'alerts', icon: '⚠️', label: 'Alerts' },
    { id: 'history', icon: '🕒', label: 'Historical Events' },
    { id: 'settings', icon: '⚙️', label: 'Settings' },
    { id: 'feedback', icon: '💬', label: 'Feedback' },
  ];

  return (
    <aside className="w-64 bg-navy-950 border-r border-navy-800 flex flex-col h-screen overflow-hidden flex-shrink-0">
      {/* Brand */}
      <div className="p-6 border-b border-navy-800">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-glow to-blue-600 flex items-center justify-center">
            <span className="text-white font-bold text-xl leading-none">≈</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">PRAVAAH</h1>
            <p className="text-[10px] text-gray-400 uppercase tracking-widest mt-0.5">
              Flowing Insights, Saving Lives
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1 scrollbar-thin scrollbar-thumb-navy-700">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-2">
          Navigation
        </div>
        {navItems.map((item) => (
          <NavItem 
            key={item.id} 
            icon={item.icon} 
            label={item.label} 
            isActive={activePanel === item.id} 
            onClick={() => setActivePanel(item.id)} 
          />
        ))}
      </nav>

      {/* System Status */}
      <div className="p-4 border-t border-navy-800 bg-navy-900/50">
        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          System Status
        </div>
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-risk-low animate-pulse"></span>
            <span className="text-sm text-risk-low font-medium">All Systems Operational</span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-400">Data Sources:</span>
            <span className="text-white font-mono">8/8 Active</span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-400">Model Confidence:</span>
            <span className="text-cyan-glow font-mono font-bold">{confidence}%</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
