import React, { useState, useEffect } from 'react';

const ConsentDashboard = ({ userId, token }) => {
  const [activeTab, setActiveTab] = useState('consents');
  const [consents, setConsents] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showRevokeModal, setShowRevokeModal] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, [userId]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/consent/dashboard/${userId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.clear();
          window.location.reload();
          return;
        }
        throw new Error('Failed to fetch dashboard data');
      }

      const data = await response.json();

      // Map backend field names to frontend expected format
      // Backend returns: active_consents, authentication_history
      // Frontend expects: consents, audit_logs with specific field names
      const mappedConsents = (data.active_consents || []).map(c => ({
        id: c.consent_id,
        purpose: c.purpose,
        granted_at: c.granted_at,
        expires_at: c.expires_at,
        is_active: c.is_valid,
        remaining_days: c.remaining_days
      }));

      const mappedAuditLogs = (data.authentication_history || []).map(log => ({
        action: log.action,
        timestamp: log.timestamp,
        success: log.result === 'success',
        metadata: {
          ip_address: log.location || 'Unknown',
          device: log.device || 'Unknown'
        }
      }));

      setConsents(mappedConsents);
      setAuditLogs(mappedAuditLogs);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };


  const handleRevokeConsent = async (consentId) => {
    try {
      const response = await fetch('/api/consent/revoke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          consent_id: showRevokeModal.id,
          revocation_reason: 'User requested revocation'
        })
      });

      if (!response.ok) throw new Error('Failed to revoke consent');

      setShowRevokeModal(null);
      fetchDashboardData();
    } catch (err) {
      alert('Failed to revoke consent: ' + err.message);
    }
  };


  const handleExportData = async () => {
    try {
      const response = await fetch('/api/consent/export-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ confirm: true })
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fhe-face-data-export-${Date.now()}.json`;
      a.click();
    } catch (err) {
      alert('Export failed: ' + err.message);
    }
  };

  const handleDeleteBiometricData = async () => {
    try {
      const response = await fetch('/api/consent/delete-biometric-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ confirmation: 'DELETE_MY_DATA' })
      });

      if (!response.ok) throw new Error('Deletion failed');

      alert('Your biometric data has been permanently deleted.');
      setShowDeleteModal(false);
      localStorage.clear();
      window.location.reload();
    } catch (err) {
      alert('Deletion failed: ' + err.message);
    }
  };

  const getDaysRemaining = (expiresAt) => {
    const days = Math.floor((new Date(expiresAt) - new Date()) / (1000 * 60 * 60 * 24));
    return days;
  };

  const getRowColor = (daysRemaining) => {
    if (daysRemaining > 30) return 'rgba(16, 185, 129, 0.1)';
    if (daysRemaining > 7) return 'rgba(234, 179, 8, 0.1)';
    return 'rgba(239, 68, 68, 0.1)';
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem' }}>
        <div className="mono">LOADING_DASHBOARD...</div>
      </div>
    );
  }

  return (
    <div className="portal-view">
      <h2>Privacy & Consent Center</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Manage your data, consents, and privacy settings
      </p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', borderBottom: '1px solid var(--glass-border)' }}>
        {['consents', 'history', 'data'].map(tab => (
          <button
            key={tab}
            className={`nav-item ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
            style={{
              border: 'none',
              borderBottom: activeTab === tab ? '2px solid var(--primary)' : '2px solid transparent',
              borderRadius: 0,
              background: 'transparent'
            }}
          >
            {tab === 'consents' && '✓ Active Consents'}
            {tab === 'history' && '📜 Auth History'}
            {tab === 'data' && '🗄️ Data Management'}
          </button>
        ))}
      </div>

      {/* Active Consents Tab */}
      {activeTab === 'consents' && (
        <div className="glass" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>Active Consents</h3>
          {consents.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No active consents found</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--glass-border)' }}>
                    <th style={{ padding: '1rem', textAlign: 'left' }}>Purpose</th>
                    <th style={{ padding: '1rem', textAlign: 'left' }}>Granted</th>
                    <th style={{ padding: '1rem', textAlign: 'left' }}>Expires In</th>
                    <th style={{ padding: '1rem', textAlign: 'left' }}>Status</th>
                    <th style={{ padding: '1rem', textAlign: 'left' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {consents.map(consent => {
                    const daysRemaining = getDaysRemaining(consent.expires_at);
                    return (
                      <tr key={consent.id} style={{ background: getRowColor(daysRemaining), borderBottom: '1px solid var(--glass-border)' }}>
                        <td style={{ padding: '1rem' }}>
                          <strong>{consent.purpose}</strong>
                        </td>
                        <td style={{ padding: '1rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                          {new Date(consent.granted_at).toLocaleDateString()}
                        </td>
                        <td style={{ padding: '1rem' }}>
                          {daysRemaining > 0 ? `${daysRemaining} days` : 'Expired'}
                        </td>
                        <td style={{ padding: '1rem' }}>
                          <span className={`status-badge ${consent.is_active ? 'status-secure' : ''}`}>
                            {consent.is_active ? 'Active' : 'Revoked'}
                          </span>
                        </td>
                        <td style={{ padding: '1rem' }}>
                          {consent.is_active && (
                            <button
                              className="btn btn-ghost"
                              style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                              onClick={() => setShowRevokeModal(consent)}
                            >
                              Revoke
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Authentication History Tab */}
      {activeTab === 'history' && (
        <div className="glass" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>Authentication History</h3>
          {auditLogs.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No authentication history available</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {auditLogs.slice(0, 10).map((log, idx) => (
                <div key={idx} style={{
                  padding: '1rem',
                  background: 'var(--surface)',
                  borderRadius: '8px',
                  borderLeft: `3px solid ${log.success ? 'var(--accent)' : 'var(--error)'}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong className="mono">{log.action}</strong>
                      <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      background: log.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      color: log.success ? 'var(--accent)' : 'var(--error)',
                      fontSize: '0.75rem',
                      fontWeight: 600
                    }}>
                      {log.success ? 'SUCCESS' : 'FAILED'}
                    </div>
                  </div>
                  {log.metadata && (
                    <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {log.metadata.ip_address && `IP: ${log.metadata.ip_address}`}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Data Management Tab */}
      {activeTab === 'data' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="glass" style={{ padding: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Export Your Data</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              Download all your consent records and authentication history as JSON
            </p>
            <button className="btn btn-primary" onClick={handleExportData}>
              📥 Download My Data
            </button>
          </div>

          <div className="glass" style={{ padding: '1.5rem', borderColor: 'var(--error)' }}>
            <h3 style={{ marginBottom: '1rem', color: 'var(--error)' }}>⚠️ Danger Zone</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              Permanently delete all your biometric data. This action cannot be undone.
            </p>
            <button
              className="btn"
              style={{ background: 'var(--error)', color: 'white' }}
              onClick={() => setShowDeleteModal(true)}
            >
              🗑️ Delete My Biometric Data
            </button>
          </div>

          <div className="glass" style={{ padding: '1.5rem' }}>
            <h4 style={{ marginBottom: '1rem' }}>Data Retention Policy</h4>
            <ul style={{ color: 'var(--text-muted)', lineHeight: 1.8, paddingLeft: '1.5rem' }}>
              <li>Biometric templates are stored as encrypted ciphertexts using CKKS FHE</li>
              <li>Templates are automatically deleted 90 days after consent expiration</li>
              <li>Audit logs are retained for 1 year for security purposes</li>
              <li>You can request immediate deletion at any time</li>
              <li>We comply with GDPR (EU) and DPDP Act 2023 (India)</li>
            </ul>
          </div>
        </div>
      )}

      {/* Revoke Confirmation Modal */}
      {showRevokeModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="glass" style={{ maxWidth: '400px', padding: '2rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Revoke Consent?</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
              Are you sure you want to revoke consent for <strong>{showRevokeModal.purpose}</strong>?
              This will prevent authentication until you grant consent again.
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setShowRevokeModal(null)}>
                Cancel
              </button>
              <button
                className="btn"
                style={{ background: 'var(--error)', color: 'white' }}
                onClick={() => handleRevokeConsent(showRevokeModal.id)}
              >
                Revoke
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="glass" style={{ maxWidth: '500px', padding: '2rem', borderColor: 'var(--error)' }}>
            <h3 style={{ marginBottom: '1rem', color: 'var(--error)' }}>⚠️ Permanently Delete Data?</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', lineHeight: 1.6 }}>
              This will permanently delete:
            </p>
            <ul style={{ color: 'var(--text-muted)', marginBottom: '2rem', lineHeight: 1.8, paddingLeft: '1.5rem' }}>
              <li>All encrypted biometric templates</li>
              <li>All consent records</li>
              <li>Authentication history (audit logs retained for 30 days for security)</li>
            </ul>
            <p style={{ color: 'var(--error)', marginBottom: '2rem' }}>
              <strong>This action cannot be undone. You will be logged out immediately.</strong>
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setShowDeleteModal(false)}>
                Cancel
              </button>
              <button
                className="btn"
                style={{ background: 'var(--error)', color: 'white' }}
                onClick={handleDeleteBiometricData}
              >
                Yes, Delete Everything
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConsentDashboard;
