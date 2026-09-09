import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { apiErrorMessage } from "./api/client";
import { clearToken, getToken, UNAUTHORIZED_EVENT } from "./api/auth";
import { useContract, useContracts, useDeleteContract, useLogout, useMe } from "./api/hooks";
import AuthScreen from "./components/AuthScreen";
import ConfirmDialog from "./components/ConfirmDialog";
import ContractList from "./components/ContractList";
import PlaybookView from "./components/PlaybookView";
import ReviewReport from "./components/ReviewReport";
import UploadForm from "./components/UploadForm";
import { useToast } from "./context/ToastContext.jsx";

const NAV_TABS = [
  { id: "review", label: "Review" },
  { id: "playbook", label: "Playbook" },
];

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!getToken());
  const [selectedId, setSelectedId] = useState(null);
  const [activeNav, setActiveNav] = useState("review");
  const [pendingDelete, setPendingDelete] = useState(null);
  const queryClient = useQueryClient();
  const showToast = useToast();

  useEffect(() => {
    const handleUnauthorized = () => {
      clearToken();
      setIsAuthenticated(false);
      queryClient.clear();
    };
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
  }, [queryClient]);

  const meQuery = useMe(isAuthenticated);
  const contractsQuery = useContracts();
  const contractQuery = useContract(selectedId);
  const logout = useLogout();
  const deleteContract = useDeleteContract();

  if (!isAuthenticated) {
    return <AuthScreen onAuthenticated={() => setIsAuthenticated(true)} />;
  }

  const handleLogout = async () => {
    await logout.mutateAsync();
    setIsAuthenticated(false);
    setSelectedId(null);
    queryClient.clear();
  };

  const goToContract = (id) => {
    setSelectedId(id);
    setActiveNav("review");
  };

  const confirmDelete = async () => {
    const contract = pendingDelete;
    setPendingDelete(null);
    try {
      await deleteContract.mutateAsync(contract.id);
      if (selectedId === contract.id) setSelectedId(null);
      showToast(`Deleted "${contract.filename}"`, "success");
    } catch (err) {
      showToast(apiErrorMessage(err), "error");
    }
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__brand">
          <div className="brandmark brandmark--sm">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"
                stroke="#C4A25C"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
              <path d="M9 12.5h6M9 15.5h6M9 9.5h3" stroke="#C4A25C" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <h1 className="hl-heading">
              <span>ClauseGuard</span>
            </h1>
            <p>Upload a contract, get a clause-by-clause risk review against your playbook.</p>
          </div>
        </div>
        <div className="app-header__user">
          {meQuery.data && <span className="app-header__username">{meQuery.data.username}</span>}
          <button className="btn btn-ghost btn-sm" onClick={handleLogout} disabled={logout.isPending}>
            Log out
          </button>
        </div>
      </header>

      <nav className="app-nav">
        {NAV_TABS.map((t) => (
          <button
            key={t.id}
            className={t.id === activeNav ? "app-nav__tab is-active" : "app-nav__tab"}
            onClick={() => setActiveNav(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {activeNav === "playbook" ? (
        <main className="app-main app-main--full">
          <PlaybookView />
        </main>
      ) : (
        <div className="app-body">
          <aside className="app-sidebar">
            <UploadForm onReviewed={goToContract} />
            <div className="section-label">
              <h4>Recent</h4>
            </div>
            {contractsQuery.isLoading && <p className="empty-state">Loading...</p>}
            {contractsQuery.isError && (
              <p className="form-error">Couldn't reach the ClauseGuard backend. Is it running?</p>
            )}
            <ContractList
              contracts={contractsQuery.data}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onDelete={setPendingDelete}
            />
          </aside>

          <main className="app-main">
            <ReviewReport contract={contractQuery.data} />
          </main>
        </div>
      )}

      <ConfirmDialog
        open={!!pendingDelete}
        title="Delete this contract?"
        message={
          pendingDelete
            ? `"${pendingDelete.filename}" and its full review history and chat will be permanently deleted. This can't be undone.`
            : ""
        }
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  );
}
