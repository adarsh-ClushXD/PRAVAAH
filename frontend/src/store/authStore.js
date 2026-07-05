import { create } from 'zustand';

export const useAuthStore = create((set) => ({
  isAuthenticated: false,
  isLoginModalOpen: false,
  isLoadingScreen: true,
  
  // Hardcoded Demo Credentials
  DEMO_USER: 'Admin',
  DEMO_PASS: 'Clush@232774',

  setLoadingScreen: (status) => set({ isLoadingScreen: status }),
  
  openLoginModal: () => set({ isLoginModalOpen: true }),
  
  closeLoginModal: () => set({ isLoginModalOpen: false }),
  
  login: (username, password) => {
    return new Promise((resolve, reject) => {
      // Simulate slight network delay for realism
      setTimeout(() => {
        if (username === 'Admin' && password === 'Clush@232774') {
          set({ isAuthenticated: true, isLoginModalOpen: false });
          resolve(true);
        } else {
          reject(new Error("Invalid credentials. Please try again."));
        }
      }, 500);
    });
  },
  
  logout: () => set({ isAuthenticated: false }),
}));
