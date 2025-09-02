import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-100">
          <header className="bg-blue-600 text-white p-4">
            <h1 className="text-2xl font-bold">NEPL LIMS - Calibration Management System</h1>
          </header>
          
          <main className="container mx-auto mt-8 p-4">
            <Routes>
              <Route path="/" element={<Dashboard />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

// Simple Dashboard component
const Dashboard = () => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Dashboard</h2>
      <p>Welcome to NEPL LIMS! System is running successfully.</p>
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded border">
          <h3 className="font-medium text-blue-800">Total SRFs</h3>
          <p className="text-2xl font-bold text-blue-600">0</p>
        </div>
        <div className="bg-green-50 p-4 rounded border">
          <h3 className="font-medium text-green-800">Active Jobs</h3>
          <p className="text-2xl font-bold text-green-600">0</p>
        </div>
        <div className="bg-yellow-50 p-4 rounded border">
          <h3 className="font-medium text-yellow-800">Pending Certificates</h3>
          <p className="text-2xl font-bold text-yellow-600">0</p>
        </div>
      </div>
    </div>
  );
};

export default App;
