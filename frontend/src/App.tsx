import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AdminPanel } from './components/admin/AdminPanel';
import { ChatContainer } from './components/ChatContainer';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Login } from './components/Login';
import { RAGPanel } from './components/rag/RAGPanel';
import { Register } from './components/Register';
import { Sidebar } from './components/Sidebar';
import { DocsPage } from './pages/DocsPage';
import { WidgetPage } from './pages/WidgetPage'; // Import your WidgetPage
import { apiService } from './services/api';
import { useStore } from './store/useStore';

function App() {
  const { user, isAuthenticated, setUser, logout, theme } = useStore();
  const [showRegister, setShowRegister] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showAdmin, setShowAdmin] = useState(false);
  const [showRAG, setShowRAG] = useState(false);

  // --- Auth & Theme Logic ---
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    const checkAuth = async () => {
      // apiService.getToken() checks localStorage for 'access_token'
      if (apiService.getToken()) {
        try {
          const user = await apiService.getCurrentUser();
          setUser(user);
        } catch (error) {
          logout();
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, [setUser, logout, theme]);

  const handleLoginSuccess = async () => {
    try {
      const userData = await apiService.getCurrentUser();
      setUser(userData);
      setLoading(false);
      if (window.location.pathname.includes('/widget')) {
        // Stay here or do nothing, the WidgetPage will re-render 
        // naturally because isAuthenticated is now true.
        return;
      }
    } catch (err) {
      console.error("Failed to fetch user after login", err);
      setLoading(false);
    }
  };

  // --- Loading State ---
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // --- Main Application Component (Authenticated Dashboard) ---
  const MainDashboard = () => {
    const isAdmin = (user?.username === 'junaidte14' && import.meta.env.VITE_SHOW_ADMIN == 'true');

    if (!isAuthenticated) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center p-4">
          <ErrorBoundary>
            {showRegister ? (
              <Register
                onRegisterSuccess={() => { }}
                onSwitchToLogin={() => setShowRegister(false)}
              />
            ) : (
              <Login
                onLoginSuccess={handleLoginSuccess}
                onSwitchToRegister={() => setShowRegister(true)}
              />
            )}
          </ErrorBoundary>
        </div>
      );
    }

    if (showRAG) {
      return (
        <ErrorBoundary>
          <div className="relative">
            <button
              onClick={() => setShowRAG(false)}
              className="absolute top-4 right-4 z-50 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-700"
            >
              ← Back to Chat
            </button>
            <RAGPanel />
          </div>
        </ErrorBoundary>
      );
    }

    if (showAdmin && isAdmin) {
      return (
        <ErrorBoundary>
          <div className="relative">
            <button
              onClick={() => setShowAdmin(false)}
              className="absolute top-4 right-4 z-50 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-700"
            >
              ← Back to Chat
            </button>
            <AdminPanel />
          </div>
        </ErrorBoundary>
      );
    }

    return (
      <div className="flex h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors duration-300">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 bg-white dark:bg-gray-900">
          <ErrorBoundary>
            <ChatContainer
              isAdmin={isAdmin}
              onOpenAdmin={() => setShowAdmin(true)}
              onOpenRAG={() => setShowRAG(true)}
            />
          </ErrorBoundary>
        </main>
      </div>
    );
  };

  // --- Root Router ---
  return (
    <BrowserRouter>
      <Routes>
        {/* The dedicated route for the embeddable iframe widget */}
        <Route path="/widget" element={<WidgetPage />} />

        <Route path="/demos" element={<DocsPage />} />

        {/* The main dashboard/login application */}
        <Route path="/" element={<MainDashboard />} />

        {/* Fallback to home if route not found */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;