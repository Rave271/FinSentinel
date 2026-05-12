import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { AuthPage } from "../components/Auth";
import { useAuthContext } from "../lib/authContext";

export function LoginPage() {
  const auth = useAuthContext();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/dashboard";

  if (auth.user) {
    return <Navigate to={from} replace />;
  }

  return (
    <div className="route-auth">
      <AuthPage
        onAuth={{
          ...auth,
          login: async (email: string, password: string) => {
            const ok = await auth.login(email, password);
            if (ok) navigate(from, { replace: true });
            return ok;
          },
          register: async (email: string, password: string) => {
            const ok = await auth.register(email, password);
            if (ok) navigate(from, { replace: true });
            return ok;
          },
          guestLogin: async () => {
            const ok = await auth.guestLogin();
            if (ok) navigate(from, { replace: true });
            return ok;
          }
        }}
      />
    </div>
  );
}

