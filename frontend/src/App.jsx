import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import AppLayout from "./layouts/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import MachineDetailPage from "./pages/MachineDetailPage";
import MachineFormPage from "./pages/MachineFormPage";
import MachinesPage from "./pages/MachinesPage";
import ProfilePage from "./pages/ProfilePage";
import ScanPage from "./pages/ScanPage";
import { ForbiddenPage, NotFoundPage } from "./pages/StatusPages";
import UsersPage from "./pages/UsersPage";
import ProtectedRoute from "./routes/ProtectedRoute";
import { ROLES } from "./utils/roles";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="machines" element={<MachinesPage />} />
              <Route path="scan" element={<ScanPage />} />
              <Route path="machine/:code" element={<MachineDetailPage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="forbidden" element={<ForbiddenPage />} />
              <Route element={<ProtectedRoute roles={[ROLES.ADMIN]} />}>
                <Route path="users" element={<UsersPage />} />
                <Route path="machines/new" element={<MachineFormPage />} />
                <Route path="machine/:code/edit" element={<MachineFormPage />} />
              </Route>
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
