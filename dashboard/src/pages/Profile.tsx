import { useState } from 'react';
import type { FormEvent } from 'react';
import { User, Lock, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Profile.css';

const API_BASE = 'http://localhost:8000/api';

const ROLE_LABEL: Record<string, string> = {
  owner: 'Owner',
  mentee: 'Mentee',
  trial: 'Trial',
};

export default function Profile() {
  const { user, token } = useAuth();

  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  async function handleChangePw(e: FormEvent) {
    e.preventDefault();
    setError('');
    setSuccess(false);

    if (newPw.length < 8) {
      setError('New password must be at least 8 characters.');
      return;
    }
    if (newPw !== confirmPw) {
      setError('New passwords do not match.');
      return;
    }

    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPw,
          new_password: newPw,
        }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({ detail: 'Failed' })) as { detail?: string };
        throw new Error(d.detail || 'Failed to change password');
      }
      setSuccess(true);
      setCurrentPw('');
      setNewPw('');
      setConfirmPw('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setSaving(false);
    }
  }

  if (!user) return null;

  return (
    <div className="profile-page">
      <div className="profile-inner">

        <div className="profile-header">
          <h1 className="profile-title">Account</h1>
        </div>

        {/* Account info */}
        <div className="profile-card">
          <div className="profile-card-header">
            <User size={14} />
            <span>Account Info</span>
          </div>

          <div className="profile-info-grid">
            <div className="profile-info-row">
              <span className="profile-info-label">Name</span>
              <span className="profile-info-val">{user.name}</span>
            </div>
            <div className="profile-info-row">
              <span className="profile-info-label">Email</span>
              <span className="profile-info-val">{user.email}</span>
            </div>
            <div className="profile-info-row">
              <span className="profile-info-label">Role</span>
              <span className="profile-info-val">
                <span className={`profile-role-badge role-${user.role}`}>
                  {ROLE_LABEL[user.role] ?? user.role}
                </span>
              </span>
            </div>
            <div className="profile-info-row">
              <span className="profile-info-label">Status</span>
              <span className="profile-info-val">
                <span className={`profile-status-badge status-${user.status}`}>
                  {user.status?.toUpperCase()}
                </span>
              </span>
            </div>
          </div>
        </div>

        {/* Change password */}
        <div className="profile-card">
          <div className="profile-card-header">
            <Lock size={14} />
            <span>Change Password</span>
          </div>

          <form className="profile-pw-form" onSubmit={handleChangePw} noValidate>
            <div className="profile-field">
              <label className="profile-label">Current Password</label>
              <input
                className="profile-input"
                type="password"
                value={currentPw}
                onChange={e => setCurrentPw(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            <div className="profile-field">
              <label className="profile-label">New Password</label>
              <input
                className="profile-input"
                type="password"
                value={newPw}
                onChange={e => setNewPw(e.target.value)}
                autoComplete="new-password"
                required
                minLength={8}
              />
            </div>
            <div className="profile-field">
              <label className="profile-label">Confirm New Password</label>
              <input
                className="profile-input"
                type="password"
                value={confirmPw}
                onChange={e => setConfirmPw(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>

            {error && <div className="profile-error">{error}</div>}
            {success && (
              <div className="profile-success">
                <CheckCircle size={13} />
                Password changed successfully.
              </div>
            )}

            <button
              type="submit"
              className="profile-save-btn"
              disabled={saving || !currentPw || !newPw || !confirmPw}
            >
              {saving ? 'Saving...' : 'Update Password'}
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}
