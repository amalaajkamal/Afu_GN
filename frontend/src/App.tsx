import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";

// Route-level code splitting: only the Global Overview and Impact Map pages
// pull in Plotly (the largest dependency in the bundle), so keeping every
// page lazy means a visitor landing on e.g. Best Practices never downloads
// map code at all — worthwhile on the slower mobile connections this
// dashboard is meant to be usable on.
const GlobalOverviewPage = lazy(() =>
  import("./pages/GlobalOverviewPage").then((m) => ({ default: m.GlobalOverviewPage })),
);
const PrincipleGapAnalysisPage = lazy(() =>
  import("./pages/PrincipleGapAnalysisPage").then((m) => ({ default: m.PrincipleGapAnalysisPage })),
);
const RegionalEquityPage = lazy(() =>
  import("./pages/RegionalEquityPage").then((m) => ({ default: m.RegionalEquityPage })),
);
const BestPracticesExplorerPage = lazy(() =>
  import("./pages/BestPracticesExplorerPage").then((m) => ({
    default: m.BestPracticesExplorerPage,
  })),
);
const ImpactMapPage = lazy(() =>
  import("./pages/ImpactMapPage").then((m) => ({ default: m.ImpactMapPage })),
);
const AboutUsPage = lazy(() =>
  import("./pages/AboutUsPage").then((m) => ({ default: m.AboutUsPage })),
);
const ResearchPage = lazy(() =>
  import("./pages/ResearchPage").then((m) => ({ default: m.ResearchPage })),
);

function PageFallback() {
  return <div className="h-96 animate-pulse rounded-xl bg-surface-muted" />;
}

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          index
          element={
            <Suspense fallback={<PageFallback />}>
              <GlobalOverviewPage />
            </Suspense>
          }
        />
        <Route
          path="principles"
          element={
            <Suspense fallback={<PageFallback />}>
              <PrincipleGapAnalysisPage />
            </Suspense>
          }
        />
        <Route
          path="regional-equity"
          element={
            <Suspense fallback={<PageFallback />}>
              <RegionalEquityPage />
            </Suspense>
          }
        />
        <Route
          path="best-practices"
          element={
            <Suspense fallback={<PageFallback />}>
              <BestPracticesExplorerPage />
            </Suspense>
          }
        />
        <Route
          path="impact-map"
          element={
            <Suspense fallback={<PageFallback />}>
              <ImpactMapPage />
            </Suspense>
          }
        />
        <Route
          path="research"
          element={
            <Suspense fallback={<PageFallback />}>
              <ResearchPage />
            </Suspense>
          }
        />
        <Route
          path="about"
          element={
            <Suspense fallback={<PageFallback />}>
              <AboutUsPage />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  );
}

export default App;
