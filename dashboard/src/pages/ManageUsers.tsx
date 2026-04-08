import { useEffect, useState, useCallback } from 'react';
import { CheckCircle, XCircle, Copy, RefreshCw, UserX, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './ManageUsers.css';

const API_BASE = 'http://localhost:8000/api';

interface Application {
  id: number;
  name: string;
  email: string;
  country: string;
  experience: string;
  reason: string;
  status: string;
  created_at: string;
}

interface Mentee {
  id: number;
  name: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
  last_login?: string;
}

interface Invite {
  id: number;
  code: string;
  email?: string;
  role: string;
  used: boolean;
  created_at: string;
}

type Tab = 'applications' | 'mentees' | 'invites';

function formatDate(v: string | undefined | null): string {
  if (!v) return '—';
  try {
    const d = new Date(v);
    const mo = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${mo}/${day} ${hh}:${mm}`;
  } catch { return '—'; }
}

function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  let cls = 'mb-grey';
  if (s === 'pending') cls = 'mb-amber';
  else if (s === 'approved' || s === 'active') cls = 'mb-green';
  else if (s === 'rejected' || s === 'suspended') cls = 'mb-red';
  return <span className={`manage-badge ${cls}`}>{status.toUpperCase()}</span>;
}

export default function ManageUsers() {
  const { token } = useAuth();
  const [tab, setTab] = useState<Tab>('applications');

  const [applications, setApplications] = useState<Application[]>([]);
  const [mentees, setMentees] = useState<Mentee[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);

  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [newInviteEmail, setNewInviteEmail] = useState('');
  const [newInviteResult, setNewInviteResult] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const headers = { Authorization: `Bearer ${token}` };

  const loadAll = useCallback(async () => {
    try {
      const [appRes, menteeRes, inviteRes] = await Promise.all([
        fetch(`${API_BASE}/users/applications`, { headers }),
        fetch(`${API_BASE}/users/mentees`, { headers }),
        fetch(`${API_BASE}/users/invites`, { headers }),
      ]);
      if (appRes.ok) {
        const d = await appRes.json() as { applications: Application[] };
        setApplications(d.applications ?? []);
      }
      if (menteeRes.ok) {
        const d = await menteeRes.json() as { mentees: Mentee[] };
        setMentees(d.mentees ?? []);
      }
      if (inviteRes.ok) {
        const d = await inviteRes.json() as { invites: Invite[] };
        setInvites(d.invites ?? []);
      }
    } catch { /* silent */ }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, refreshKey]);

  useEffect(() => { loadAll(); }, [loadAll]);

  async function approveApp(id: number) {
    setLoadingAction(`approve-${id}`);
    try {
      const res = await fetch(`${API_BASE}/users/applications/${id}/approve`, {
        method: 'POST', headers,
      });
      if (res.ok) setRefreshKey(k => k + 1);
    } finally { setLoadingAction(null); }
  }

  async function rejectApp(id: number) {
    setLoadingAction(`reject-${id}`);
    try {
      const res = await fetch(`${API_BASE}/users/applications/${id}/reject`, {
        method: 'POST', headers,
      });
      if (res.ok) setRefreshKey(k => k + 1);
    } finally { setLoadingAction(null); }
  }

  async function toggleUser(id: number, currentStatus: string) {
    const action = currentStatus === 'active' ? 'suspend' : 'activate';
    setLoadingAction(`${action}-${id}`);
    try {
      const res = await fetch(`${API_BASE}/users/${id}/${action}`, {
        method: 'POST', headers,
      });
      if (res.ok) setRefreshKey(k => k + 1);
    } finally { setLoadingAction(null); }
  }

  async function createInvite() {
    setLoadingAction('new-invite');
    setNewInviteResult(null);
    try {
      const res = await fetch(`${API_BASE}/users/invites`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newInviteEmail || null, role: 'mentee' }),
      });
      if (res.ok) {
        const d = await res.json() as { invite_code: string };
        setNewInviteResult(d.invite_code);
        setNewInviteEmail('');
        setRefreshKey(k => k + 1);
      }
    } finally { setLoadingAction(null); }
  }

  function copyCode(code: string) {
    navigator.clipboard.writeText(code).then(() => {
      setCopiedCode(code);
      setTimeout(() => setCopiedCode(null), 2000);
    });
  }

  const pendingApps = applications.filter(a => a.status === 'pending');
  const reviewedApps = applications.filter(a => a.status !== 'pending');

  return (
    <div className="manage-page">
      <div className="manage-inner">
        <div className="manage-header">
          <h1 className="manage-title">User Management</h1>
          <button className="manage-refresh" onClick={() => setRefreshKey(k => k + 1)} title="Refresh">
            <RefreshCw size={14} />
          </button>
        </div>

        {/* Tabs */}
        <div className="manage-tabs">
          <button
            className={`manage-tab${tab === 'applications' ? ' active' : ''}`}
            onClick={() => setTab('applications')}
          >
            Applications
            {pendingApps.length > 0 && (
              <span className="manage-tab-badge">{pendingApps.length}</span>
            )}
          </button>
          <button
            className={`manage-tab${tab === 'mentees' ? ' active' : ''}`}
            onClick={() => setTab('mentees')}
          >
            Mentees
            <span className="manage-tab-badge manage-tab-badge-grey">{mentees.length}</span>
          </button>
          <button
            className={`manage-tab${tab === 'invites' ? ' active' : ''}`}
            onClick={() => setTab('invites')}
          >
            Invites
          </button>
        </div>

        {/* APPLICATIONS */}
        {tab === 'applications' && (
          <div className="manage-section">
            {applications.length === 0 ? (
              <div className="manage-empty">No applications yet.</div>
            ) : (
              <>
                {pendingApps.length > 0 && (
                  <>
                    <div className="manage-section-label">Pending review</div>
                    {pendingApps.map(app => (
                      <div className="manage-app-card" key={app.id}>
                        <div className="manage-app-top">
                          <div className="manage-app-info">
                            <span className="manage-app-name">{app.name}</span>
                            <span className="manage-app-email">{app.email}</span>
                            <span className="manage-app-meta">
                              {app.country} · {app.experience} · {formatDate(app.created_at)}
                            </span>
                          </div>
                          <div className="manage-app-actions">
                            <button
                              className="manage-btn manage-btn-approve"
                              onClick={() => approveApp(app.id)}
                              disabled={loadingAction !== null}
                            >
                              <CheckCircle size={13} />
                              {loadingAction === `approve-${app.id}` ? '...' : 'Approve'}
                            </button>
                            <button
                              className="manage-btn manage-btn-reject"
                              onClick={() => rejectApp(app.id)}
                              disabled={loadingAction !== null}
                            >
                              <XCircle size={13} />
                              {loadingAction === `reject-${app.id}` ? '...' : 'Reject'}
                            </button>
                          </div>
                        </div>
                        <p className="manage-app-reason">"{app.reason}"</p>
                      </div>
                    ))}
                  </>
                )}
                {reviewedApps.length > 0 && (
                  <>
                    <div className="manage-section-label" style={{ marginTop: 24 }}>Reviewed</div>
                    {reviewedApps.map(app => (
                      <div className="manage-app-card manage-app-card-reviewed" key={app.id}>
                        <div className="manage-app-top">
                          <div className="manage-app-info">
                            <span className="manage-app-name">{app.name}</span>
                            <span className="manage-app-email">{app.email}</span>
                            <span className="manage-app-meta">{app.country} · {formatDate(app.created_at)}</span>
                          </div>
                          <StatusBadge status={app.status} />
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </>
            )}
          </div>
        )}

        {/* MENTEES */}
        {tab === 'mentees' && (
          <div className="manage-section">
            {mentees.length === 0 ? (
              <div className="manage-empty">No mentees registered yet.</div>
            ) : (
              <table className="manage-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                    <th>Last Login</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {mentees.map(m => (
                    <tr key={m.id}>
                      <td className="manage-td-name">{m.name}</td>
                      <td className="manage-td-email">{m.email}</td>
                      <td><span className="manage-role-badge">{m.role.toUpperCase()}</span></td>
                      <td><StatusBadge status={m.status} /></td>
                      <td className="manage-td-date">{formatDate(m.created_at)}</td>
                      <td className="manage-td-date">{formatDate(m.last_login)}</td>
                      <td>
                        <button
                          className={`manage-btn ${m.status === 'active' ? 'manage-btn-suspend' : 'manage-btn-activate'}`}
                          onClick={() => toggleUser(m.id, m.status)}
                          disabled={loadingAction !== null}
                        >
                          {m.status === 'active'
                            ? <><UserX size={12} /> Suspend</>
                            : <><UserCheck size={12} /> Activate</>
                          }
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* INVITES */}
        {tab === 'invites' && (
          <div className="manage-section">
            <div className="manage-invite-create">
              <div className="manage-section-label">Generate invite code</div>
              <div className="manage-invite-row">
                <input
                  className="manage-invite-input"
                  type="email"
                  placeholder="Tie to email (optional)"
                  value={newInviteEmail}
                  onChange={e => setNewInviteEmail(e.target.value)}
                />
                <button
                  className="manage-btn manage-btn-create"
                  onClick={createInvite}
                  disabled={loadingAction === 'new-invite'}
                >
                  {loadingAction === 'new-invite' ? 'Creating...' : 'Create Invite'}
                </button>
              </div>
              {newInviteResult && (
                <div className="manage-invite-result">
                  <span className="manage-invite-code mono">{newInviteResult}</span>
                  <button
                    className="manage-copy-btn"
                    onClick={() => copyCode(newInviteResult)}
                    title="Copy"
                  >
                    <Copy size={13} />
                    {copiedCode === newInviteResult ? 'Copied!' : 'Copy'}
                  </button>
                </div>
              )}
            </div>

            {invites.length === 0 ? (
              <div className="manage-empty">No invites generated yet.</div>
            ) : (
              <table className="manage-table" style={{ marginTop: 24 }}>
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {invites.map(inv => (
                    <tr key={inv.id} className={inv.used ? 'manage-row-used' : ''}>
                      <td className="manage-td-code mono">{inv.code}</td>
                      <td className="manage-td-email">{inv.email ?? '—'}</td>
                      <td><span className="manage-role-badge">{inv.role.toUpperCase()}</span></td>
                      <td>
                        <span className={`manage-badge ${inv.used ? 'mb-grey' : 'mb-green'}`}>
                          {inv.used ? 'USED' : 'ACTIVE'}
                        </span>
                      </td>
                      <td className="manage-td-date">{formatDate(inv.created_at)}</td>
                      <td>
                        {!inv.used && (
                          <button
                            className="manage-copy-btn"
                            onClick={() => copyCode(inv.code)}
                            title="Copy code"
                          >
                            <Copy size={13} />
                            {copiedCode === inv.code ? 'Copied!' : 'Copy'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
