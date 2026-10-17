import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { loadSnapshot, type Snapshot } from "./data";
import "./styles.css";

function Root() {
  const [data, setData] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    loadSnapshot().then(setData, (e: Error) => setError(e.message));
  }, []);
  if (error)
    return (
      <div className="status">
        <h1>The data could not be loaded</h1>
        <p>{error}</p>
      </div>
    );
  if (!data) return <div className="status">Loading…</div>;
  return <App data={data} />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
