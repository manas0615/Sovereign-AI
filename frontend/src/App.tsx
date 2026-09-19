import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ChatWorkbench } from './pages/ChatWorkbench';
import { CodingStudio } from './pages/CodingStudio';
import { Dashboard } from './pages/Dashboard';
import { NewTask } from './pages/NewTask';
import { TaskExecution } from './pages/TaskExecution';
import { KnowledgeBase } from './pages/KnowledgeBase';
import { ArtifactsLibrary } from './pages/ArtifactsLibrary';
import { Passports } from './pages/Passports';
import { MoonVisualization } from './pages/MoonVisualization';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* Primary Conversational Workbench */}
          <Route index element={<ChatWorkbench />} />
          <Route path="coding" element={<CodingStudio />} />
          <Route path="knowledge" element={<KnowledgeBase />} />
          <Route path="artifacts" element={<ArtifactsLibrary />} />
          <Route path="tasks" element={<Dashboard />} />
          <Route path="tasks/new" element={<NewTask />} />
          <Route path="tasks/:id" element={<TaskExecution />} />
          <Route path="passports" element={<Passports />} />
          <Route path="moon" element={<MoonVisualization />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
