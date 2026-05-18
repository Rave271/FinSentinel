import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useEffect } from "react";

import { SiteLayout } from "./components/SiteLayout";
import { AuthProvider } from "./lib/authContext";
import { AboutPage } from "./pages/About";
import { DashboardPage } from "./pages/Dashboard";
import { HomePage } from "./pages/Home";
import { LoginPage } from "./pages/Login";

function detectTheme() {
  const saved = window.localStorage.getItem("finsentinel-theme");
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  useEffect(() => {
    const theme = detectTheme();
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("finsentinel-theme", theme);
  }, []);

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
