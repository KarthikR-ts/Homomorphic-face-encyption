import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ConsentOnboarding from './ConsentOnboarding';
import ConsentDashboard from './ConsentDashboard';

// SVG Icons as components
const ShieldIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>;
const UserIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>;
const GridIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></svg>;
const LockIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>;
const SettingsIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m6.36 6.36l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m6.36-6.36l4.24-4.24" /></svg>;

const App = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isScanning, setIsScanning] = useState(false);
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [needsConsent, setNeedsConsent] = useState(false);
  const [hasConsent, setHasConsent] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    if (token) {
      // Fetch user info and check consent
      checkUserAndConsent();
    }
  }, [token]);

  const checkUserAndConsent = async () => {
    try {
      // Get user info from token endpoint (or create a /api/me endpoint)
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const userData = JSON.parse(storedUser);
        setUser(userData);

        // Check if user has granted consent
        const consentCheck = await fetch(`/api/consent/verify/${userData.id}/AUTHENTICATION`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (consentCheck.ok) {
          const consentData = await consentCheck.json();
          setHasConsent(consentData.valid);
          setNeedsConsent(!consentData.valid);
        } else {
          setNeedsConsent(true);
        }
      }
    } catch (err) {
      console.error('Failed to check consent:', err);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const username = e.target.username.value;
    try {
      const resp = await fetch('/api/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      });

      if (!resp.ok) throw new Error('Login failed');

      const data = await resp.json();
      if (data.access_token) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify({
          username: data.username,
          id: data.user_id
        }));
        setUser({ username: data.username, id: data.user_id });
        setNeedsConsent(true); // Show consent onboarding for new users
      }
    } catch (err) {
      alert('Login failed: ' + err.message);
    }
  };

  const handleConsentComplete = () => {
    setNeedsConsent(false);
    setHasConsent(true);
  };

  const startScanner = async () => {
    setIsScanning(true);
    setStatus('capturing');
    setMessage('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 640 },
          height: { ideal: 480 }
        }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      setMessage('Camera access denied: ' + err.message);
      setStatus('error');
      setIsScanning(false);
    }
  };

  const stopScanner = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
    }
    setIsScanning(false);
    setStatus('idle');
    setMessage('');
  };

  const captureAndProcess = async () => {
    setStatus('processing');
    setMessage('Capturing and encrypting...');

    const canvas = canvasRef.current;
    const video = videoRef.current;

    if (!canvas || !video) {
      setStatus('error');
      setMessage('Camera not ready');
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    const imageData = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];

    try {
      const endpoint = activeTab === 'enroll' ? '/api/register' : '/api/verify';
      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ image: imageData })
      });

      const result = await resp.json();

      if (resp.ok) {
        setStatus('success');
        if (activeTab === 'enroll') {
          setMessage(`✓ Identity Secured! Template ID: ${result.template_id}`);
        } else {
          setMessage(`Confidence: ${(result.confidence * 100).toFixed(1)}%`);
        }

        setTimeout(() => {
          stopScanner();
          setActiveTab('dashboard');
        }, 3000);
      } else {
        throw new Error(result.error || result.message || 'Operation failed');
      }
    } catch (err) {
      setStatus('error');
      setMessage('Error: ' + err.message);
    }
  };

  if (!token) {
    return (
      <div className="login-screen">
        <div className="login-card glass">
          <div className="logo"><ShieldIcon /> FHE.Face</div>
          <h3>Secure Gateway</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Privacy-Preserving Homomorphic Facial Recognition
          </p>
          <form className="nav-links" onSubmit={handleLogin}>
            <div className="form-group">
              <label>Identity Handle</label>
              <input name="username" placeholder="e.g. Satoshi" required />
            </div>
            <button type="submit" className="btn btn-primary">Initialize Session</button>
          </form>
        </div>
      </div>
    );
  }

  // Show consent onboarding if needed
  if (needsConsent) {
    return <ConsentOnboarding userId={user?.id} onComplete={handleConsentComplete} />;
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="logo"><ShieldIcon /> FHE.Face</div>
        <nav className="nav-links">
          <div className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => { stopScanner(); setActiveTab('dashboard'); }}>
            <GridIcon /> Dashboard
          </div>
          <div className={`nav-item ${activeTab === 'enroll' ? 'active' : ''}`} onClick={() => { stopScanner(); setActiveTab('enroll'); }}>
            <UserIcon /> Enroll Identity
          </div>
          <div className={`nav-item ${activeTab === 'verify' ? 'active' : ''}`} onClick={() => { stopScanner(); setActiveTab('verify'); }}>
            <LockIcon /> Secure Auth
          </div>
          <div className={`nav-item ${activeTab === 'privacy' ? 'active' : ''}`} onClick={() => { stopScanner(); setActiveTab('privacy'); }}>
            <SettingsIcon /> Privacy Center
          </div>
        </nav>
        <div style={{ marginTop: 'auto' }}>
          <div className="nav-item" onClick={() => { localStorage.clear(); window.location.reload(); }}>
            Logout
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="dashboard-header">
          <div>
            <h1>Shield Portal</h1>
            <p style={{ color: 'var(--text-muted)' }}>Welcome back, <span className="mono">{user?.username}</span></p>
          </div>
          <div className="status-badge status-secure">
            {hasConsent ? 'FHE Active' : 'Consent Required'}
          </div>
        </header>

        {activeTab === 'dashboard' && (
          <div className="portal-view">
            <div className="stats-grid">
              <div className="stat-card glass">
                <div className="stat-header">Identity Protection <span>FHE-CKKS</span></div>
                <div className="stat-value">128-bit</div>
                <div className="stat-footer">Quantum Resistant Standard</div>
              </div>
              <div className="stat-card glass">
                <div className="stat-header">Consent Status <span>DPDP Standard</span></div>
                <div className="stat-value">{hasConsent ? 'Active' : 'Pending'}</div>
                <div className="stat-footer">{hasConsent ? 'All requirements met' : 'Consent required'}</div>
              </div>
              <div className="stat-card glass">
                <div className="stat-header">Polynomial Degree <span>CKKS</span></div>
                <div className="stat-value">8192</div>
                <div className="stat-footer">Ring Dimension</div>
              </div>
            </div>

            <div className="glass" style={{ width: '100%', padding: '2rem' }}>
              <h3>Quick Actions</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
                <button className="btn btn-primary" onClick={() => setActiveTab('enroll')}>
                  👤 Enroll New Template
                </button>
                <button className="btn btn-ghost" onClick={() => setActiveTab('verify')}>
                  🔓 Authenticate
                </button>
                <button className="btn btn-ghost" onClick={() => setActiveTab('privacy')}>
                  ⚙️ Privacy Settings
                </button>
              </div>
            </div>
          </div>
        )}

        {(activeTab === 'enroll' || activeTab === 'verify') && (
          <div className="portal-view">
            <h2>{activeTab === 'enroll' ? 'Biometric Enrollment' : 'Identity Verification'}</h2>
            <p style={{ color: 'var(--text-muted)' }}>
              Computations are performed on encrypted data. Your actual face image is never stored.
            </p>

            {!isScanning ? (
              <div className="glass" style={{ padding: '4rem', textAlign: 'center', width: '100%' }}>
                <button className="btn btn-primary" onClick={startScanner}>Activate Bio-Scanner</button>
              </div>
            ) : (
              <>
                <div className="scanner-container">
                  <video ref={videoRef} autoPlay playsInline muted className="video-feed" />
                  <div className="scan-overlay">
                    <div className="scan-line" />
                    <div className="face-portal" />
                  </div>
                </div>

                <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
                  {status === 'capturing' && (
                    <>
                      <button className="btn btn-primary" onClick={captureAndProcess} style={{ marginRight: '1rem' }}>
                        Capture & Encrypt
                      </button>
                      <button className="btn btn-ghost" onClick={stopScanner}>
                        Cancel
                      </button>
                    </>
                  )}
                  {status === 'processing' && (
                    <div className="btn btn-ghost" style={{ cursor: 'wait' }}>
                      <div className="mono">{message}</div>
                    </div>
                  )}
                  {status === 'success' && (
                    <div style={{ color: 'var(--accent)', fontWeight: 600, fontSize: '1.1rem' }}>{message}</div>
                  )}
                  {status === 'error' && (
                    <div>
                      <div style={{ color: 'var(--error)', fontWeight: 600, marginBottom: '1rem' }}>{message}</div>
                      <button className="btn btn-ghost" onClick={stopScanner}>Close</button>
                    </div>
                  )}
                </div>
              </>
            )}
            <canvas ref={canvasRef} style={{ display: 'none' }} />
          </div>
        )}

        {activeTab === 'privacy' && (
          <ConsentDashboard userId={user?.id} token={token} />
        )}
      </main>
    </div>
  );
};

export default App;
