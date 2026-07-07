import { create } from 'zustand';

export const useAuthStore = create((set) => ({
  isAuthenticated: false,
  isLoginModalOpen: false,
  isLoadingScreen: true,
  
  // Hardcoded Demo Credentials
  DEMO_USER: 'admin',
  DEMO_PASS: 'admin',

  userProfile: null,

  setLoadingScreen: (status) => set({ isLoadingScreen: status }),
  
  openLoginModal: () => set({ isLoginModalOpen: true }),
  
  closeLoginModal: () => set({ isLoginModalOpen: false }),
  
  login: (username, password) => {
    return new Promise((resolve, reject) => {
      // Simulate slight network delay for realism
      setTimeout(() => {
        if (username.toLowerCase() === 'admin' && password === 'admin') {
          set({ 
            isAuthenticated: true, 
            isLoginModalOpen: false,
            userProfile: { name: 'Admin Officer', email: 'ddmo.officer@wb.gov.in', picture: null }
          });
          resolve(true);
        } else {
          reject(new Error("Invalid credentials. Please try again."));
        }
      }, 500);
    });
  },

  loginWithGoogle: (profile) => {
    try {
      set({ 
        isAuthenticated: true, 
        isLoginModalOpen: false, 
        userProfile: {
          name: profile.name || 'Adarsh (DDMO Officer)',
          email: profile.email || 'adarsh.clush@wb.gov.in',
          picture: profile.picture || null
        }
      });
      return true;
    } catch (err) {
      console.error("Google authentication error", err);
      throw new Error("Failed to process Google profile.");
    }
  },
  
  logout: () => set({ isAuthenticated: false, userProfile: null }),
}));
