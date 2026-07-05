import React, { useState } from 'react';
import { useAuthStore } from '../../store/authStore';
import { X, Lock, User, Loader2 } from 'lucide-react';

export default function LoginModal() {
  const { isLoginModalOpen, closeLoginModal, login, loginWithGoogle } = useAuthStore();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [showGoogleChooser, setShowGoogleChooser] = useState(false);
  const [isSelectingAccount, setIsSelectingAccount] = useState(false);

  if (!isLoginModalOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsAuthenticating(true);

    try {
      await login(username, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handleGoogleSignIn = () => {
    setIsSelectingAccount(true);
    // Simulate Google account selection latency
    setTimeout(() => {
      try {
        loginWithGoogle({
          name: 'Adarsh (DDMO Officer)',
          email: 'adarsh.clush@wb.gov.in',
          picture: null
        });
        setShowGoogleChooser(false);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsSelectingAccount(false);
      }
    }, 1200);
  };

  // Google Account Chooser Overlay
  if (showGoogleChooser) {
    return (
      <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-md animate-fade-in">
        <div className="relative w-full max-w-sm bg-white rounded-xl shadow-2xl overflow-hidden p-6 border border-gray-200">
          <button 
            onClick={() => setShowGoogleChooser(false)}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
          
          <div className="flex flex-col items-center mt-4">
            {/* Google Logo */}
            <svg className="w-10 h-10 mb-4" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l3.66-2.85z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.85c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>

            <h2 className="text-xl font-medium text-gray-800">Choose an account</h2>
            <p className="text-sm text-gray-500 mt-1">to continue to PRAVAAH</p>
          </div>

          {/* Account Card List */}
          <div className="mt-6 space-y-2">
            {isSelectingAccount ? (
              <div className="py-8 flex flex-col items-center justify-center space-y-3">
                <Loader2 size={32} className="animate-spin text-blue-600" />
                <span className="text-sm text-gray-500 font-medium">Signing in with Google...</span>
              </div>
            ) : (
              <>
                <button
                  onClick={handleGoogleSignIn}
                  className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
                    AC
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-800">Adarsh (DDMO Officer)</p>
                    <p className="text-xs text-gray-500">adarsh.clush@wb.gov.in</p>
                  </div>
                </button>
                
                <button
                  onClick={() => alert("Please use the demo account 'Adarsh' for the hackathon preview.")}
                  className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 text-lg">
                    👤
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-500">Use another account</p>
                  </div>
                </button>
              </>
            )}
          </div>

          <div className="mt-8 pt-4 border-t border-gray-100 text-[11px] text-gray-400 leading-relaxed">
            To continue, Google will share your name, email address, language preference, and profile picture with PRAVAAH.
          </div>
        </div>
      </div>
    );
  }

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

            <div className="relative my-4 flex py-1 items-center">
              <div className="flex-grow border-t border-navy-800"></div>
              <span className="flex-shrink mx-3 text-xs text-gray-500 uppercase tracking-widest">or</span>
              <div className="flex-grow border-t border-navy-800"></div>
            </div>

            <div className="flex justify-center w-full">
              <button
                type="button"
                onClick={() => setShowGoogleChooser(true)}
                className="w-full flex items-center justify-center gap-3 py-2.5 px-4 bg-white hover:bg-gray-100 text-gray-900 font-semibold rounded-lg border border-gray-300 transition-colors shadow-sm"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#EA4335"
                    d="M12.24 10.285V14.4h6.887c-.648 2.41-2.519 4.114-5.136 4.114-3.41 0-6.19-2.78-6.19-6.19s2.78-6.19 6.19-6.19c1.554 0 2.969.577 4.058 1.536l3.057-3.057C19.168 1.956 15.932 1 12.24 1c-6.077 0-11 4.923-11 11s4.923 11 11 11c5.787 0 10.4-4.148 10.945-9.6H12.24z"
                  />
                </svg>
                Sign in with Google
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
