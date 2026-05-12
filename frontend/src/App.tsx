import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { SiteLayout } from "./components/SiteLayout";
import { AuthProvider } from "./lib/authContext";
import { AboutPage } from "./pages/About";
import { DashboardPage } from "./pages/Dashboard";
import { HomePage } from "./pages/Home";
import { LoginPage } from "./pages/Login";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<SiteLayout />}>
            <Route index element={<HomePage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
          </Route>

          <Route path="login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

