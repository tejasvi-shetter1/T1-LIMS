import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import { useDispatch, useSelector } from 'react-redux';
import { initializeAuth } from './store/slices/authSlice';
import { RootState } from './store';
import { ROUTES } from './utils/constants';

// Pages
import LoginPage from './pages/auth/LoginPage';
import LoadingSpinner from './components/common/LoadingSpinner';

// Temporary placeholder components (we'll build these next)
const CustomerDashboard = () => (
  <div className="p-8">
    <h1 className="text-2xl font-bold">Customer Dashboard</h1>
    <p>Customer portal coming soon...</p>
  </div>
);

const StaffDashboard = () => (
  <div className="p-8">
    <h1 className="text-2xl font-bold">Staff Dashboard</h1>
    <p>Staff portal coming soon...</p>
  </div>
);

const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  requiredUserType?: 'staff' | 'customer';
  requiredRole?: string[];
}> = ({ children, requiredUserType, requiredRole }) => {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  if (requiredUserType && user?.user_type !== requiredUserType) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  if (requiredRole && !requiredRole.includes(user?.role || '')) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  return <>{children}</>;
};

const AppContent: React.FC = () => {
  const dispatch = useDispatch();
  const { isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    dispatch(initializeAuth());
  }, [dispatch]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path={ROUTES.LOGIN} element={<LoginPage />} />
        
        {/* Customer Routes */}
        <Route
          path={ROUTES.CUSTOMER_DASHBOARD}
          element={
            <ProtectedRoute requiredUserType="customer">
              <CustomerDashboard />
            </ProtectedRoute>
          }
        />
        
        {/* Staff Routes */}
        <Route
          path={ROUTES.STAFF_DASHBOARD}
          element={
            <ProtectedRoute requiredUserType="staff">
              <StaffDashboard />
            </ProtectedRoute>
          }
        />
        
        {/* Default Redirects */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Navigate to={ROUTES.STAFF_DASHBOARD} replace />
            ) : (
              <Navigate to={ROUTES.LOGIN} replace />
            )
          }
        />
        
        {/* 404 - Catch all */}
        <Route
          path="*"
          element={
            <div className="min-h-screen flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-4xl font-bold text-gray-900">404</h1>
                <p className="text-gray-600">Page not found</p>
                <button
                  onClick={() => window.history.back()}
                  className="mt-4 btn-primary"
                >
                  Go Back
                </button>
              </div>
            </div>
          }
        />
      </Routes>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <div className="App">
        <AppContent />
      </div>
    </Provider>
  );
};

export default App;
