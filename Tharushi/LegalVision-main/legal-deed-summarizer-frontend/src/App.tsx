import { Route, Routes, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import AnalyzerPage from "./pages/AnalyzerPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<AnalyzerPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}