import React, { useState } from 'react';
import { useAuthStore } from '../../store/authStore';
import { X, Lock, User, Loader2 } from 'lucide-react';

export default function LoginModal() {
  const { isLoginModalOpen, closeLoginModal, login } = useAuthStore();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  if (!isLoginModalOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsAuthenticating(true);

    try {
      await login(username, password);
      // On success, modal will automatically close via state in authStore
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAuthenticating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-md bg-navy-900 border border-navy-700 rounded-xl shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-navy-800 flex justify-between items-center bg-navy-900/50">
          <h2 className="text-lg font-semibold text-white tracking-wide">Authentication Required</h2>
          <button 
            onClick={closeLoginModal}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-6">
          <p className="text-sm text-gray-400 mb-6">
            Log in to access operational features including AI analysis, state synchronization, and simulation tools.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Username or Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <User size={16} />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-navy-950 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-glow focus:ring-1 focus:ring-cyan-glow transition-colors"
                  placeholder="Enter username"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <Lock size={16} />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-navy-950 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-glow focus:ring-1 focus:ring-cyan-glow transition-colors"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-risk-critical/10 border border-risk-critical/30 text-risk-critical text-sm">
                {error}
              </div>
            )}

            <div className="pt-2">
              <button
                type="submit"
                disabled={isAuthenticating}
                className="w-full flex items-center justify-center py-2.5 px-4 bg-cyan-glow/10 hover:bg-cyan-glow/20 text-cyan-glow font-semibold rounded-lg border border-cyan-glow/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAuthenticating ? (
                  <><Loader2 size={18} className="animate-spin mr-2" /> Authenticating...</>
                ) : (
                  'Login'
                )}
              </button>
            </div>
            
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={closeLoginModal}
                className="text-sm text-gray-500 hover:text-white transition-colors"
              >
                Continue as Guest (Read-Only)
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
