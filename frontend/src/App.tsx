import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { DashboardsPage } from "./pages/dashboards/DashboardsPage";
import { AssessmentsListPage } from "./pages/assessor/AssessmentsListPage";
import { NewAssessmentPage } from "./pages/assessor/NewAssessmentPage";
import { AssessmentDetailPage } from "./pages/assessor/AssessmentDetailPage";
import { ApprovalsPage } from "./pages/approver/ApprovalsPage";
import { QuestionEditorPage } from "./pages/admin/QuestionEditorPage";
import { UsersPage } from "./pages/admin/UsersPage";

export function App() {
  const { user, loading } = useAuth();

  if (loading) return <p style={{ padding: 24 }}>Loading…</p>;
  if (!user) return <LoginPage />;

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardsPage />} />
        <Route path="/assessments" element={<AssessmentsListPage />} />
        <Route path="/assessments/new" element={<NewAssessmentPage />} />
        <Route path="/assessments/:id" element={<AssessmentDetailPage />} />
        <Route path="/approvals" element={<ApprovalsPage />} />
        <Route path="/admin/questions" element={<QuestionEditorPage />} />
        <Route path="/admin/users" element={<UsersPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
