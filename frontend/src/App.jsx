import { BrowserRouter, Routes, Route } from "react-router-dom";

import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Knowledge from "./pages/Knowledge";
import Documents from "./pages/Documents";
import Analytics from "./pages/Analytics";

function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/knowledge" element={<Knowledge />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}

export default App;