import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../../store/authStore';

export default function LoadingScreen() {
  const [fadeOut, setFadeOut] = useState(false);
  const setLoadingScreen = useAuthStore(state => state.setLoadingScreen);

  useEffect(() => {
    // 2.5 seconds total loading time
    const fadeTimer = setTimeout(() => {
      setFadeOut(true);
    }, 2000); // Start fade out at 2 seconds

    const unmountTimer = setTimeout(() => {
      setLoadingScreen(false);
    }, 2500); // Unmount at 2.5 seconds

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(unmountTimer);
    };
  }, [setLoadingScreen]);

  return (
    <div 
      className={`fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-navy-950 transition-opacity duration-500 ${
        fadeOut ? 'opacity-0' : 'opacity-100'
      }`}
    >
      <div className="flex flex-col items-center">
        {/* Animated Logo */}
        <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-cyan-glow to-blue-600 flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(0,212,255,0.3)] animate-pulse">
          <span className="text-white font-bold text-4xl leading-none">≈</span>
        </div>
        
        {/* Title */}
        <h1 className="text-3xl font-bold text-white tracking-widest mb-2">PRAVAAH</h1>
        <p className="text-xs text-cyan-glow uppercase tracking-[0.3em] font-medium mb-8">
          Flowing Insights, Saving Lives
        </p>
        
        {/* Loading Bar */}
        <div className="w-48 h-1 bg-navy-800 rounded-full overflow-hidden">
          <div className="h-full bg-cyan-glow animate-progress-bar rounded-full"></div>
        </div>
        
        <div className="mt-4 text-xs text-gray-500 font-mono animate-pulse">
          Initializing Intelligence Systems...
        </div>
      </div>
    </div>
  );
}
