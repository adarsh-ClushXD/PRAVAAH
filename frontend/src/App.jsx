import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import { useAuthStore } from './store/authStore';
import LoadingScreen from './components/auth/LoadingScreen';
import LoginModal from './components/auth/LoginModal';

export default function App() {
  const isLoadingScreen = useAuthStore(state => state.isLoadingScreen);

  return (
    <>
      {isLoadingScreen && <LoadingScreen />}
      <LoginModal />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </>
  );
}
