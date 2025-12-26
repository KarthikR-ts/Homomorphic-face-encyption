import React, { useState } from 'react';

const ConsentOnboarding = ({ userId, onComplete }) => {
  const [step, setStep] = useState(0);
  const [consents, setConsents] = useState({
    authentication: false,
    dataProcessing: false,
    analytics: false
  });

  const steps = [
    {
      title: 'Welcome to FHE.Face',
      description: 'Privacy-preserving biometric authentication powered by homomorphic encryption',
      icon: '🔐'
    },
    {
      title: 'How It Works',
      description: 'Your face is converted to an encrypted mathematical representation. All matching happens in encrypted space - we never see your actual face data.',
      icon: '🧮'
    },
    {
      title: 'Your Consent',
      description: 'We need your permission to process your biometric data. You can revoke these at any time.',
      icon: '✓'
    }
  ];

  const handleGrantConsent = async () => {
    try {
      const token = localStorage.getItem('token');

      // Grant authentication consent
      const authResponse = await fetch('/api/consent/grant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: userId,
          purpose: 'AUTHENTICATION',
          consent_text: 'I consent to the processing of my biometric data for authentication purposes using homomorphic encryption.',
          expiry_days: 365
        })
      });

      if (!authResponse.ok) throw new Error('Failed to grant consent');

      onComplete();
    } catch (err) {
      alert('Failed to grant consent: ' + err.message);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      background: 'rgba(5, 6, 15, 0.95)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div className="glass" style={{
        maxWidth: '600px',
        padding: '3rem',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>
          {steps[step].icon}
        </div>

        <h2 style={{ marginBottom: '1rem' }}>{steps[step].title}</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', lineHeight: 1.6 }}>
          {steps[step].description}
        </p>

        {step === 2 && (
          <div style={{
            background: 'var(--surface)',
            padding: '1.5rem',
            borderRadius: '12px',
            marginBottom: '2rem',
            textAlign: 'left'
          }}>
            <h4 style={{ marginBottom: '1rem' }}>Required Permissions:</h4>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={consents.authentication}
                onChange={(e) => setConsents({ ...consents, authentication: e.target.checked })}
              />
              <span>
                <strong>Biometric Authentication</strong><br />
                <small style={{ color: 'var(--text-muted)' }}>
                  Process encrypted face embeddings for secure login
                </small>
              </span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={consents.dataProcessing}
                onChange={(e) => setConsents({ ...consents, dataProcessing: e.target.checked })}
              />
              <span>
                <strong>Data Processing</strong><br />
                <small style={{ color: 'var(--text-muted)' }}>
                  Store encrypted templates in our secure database
                </small>
              </span>
            </label>

            <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '8px' }}>
              <small style={{ color: 'var(--text-muted)' }}>
                ✓ Your biometric data is encrypted with 128-bit FHE<br />
                ✓ You can revoke consent and delete data anytime<br />
                ✓ We comply with GDPR and India's DPDP Act 2023
              </small>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          {step > 0 && (
            <button className="btn btn-ghost" onClick={() => setStep(step - 1)}>
              Back
            </button>
          )}

          {step < 2 ? (
            <button className="btn btn-primary" onClick={() => setStep(step + 1)}>
              Next
            </button>
          ) : (
            <button
              className="btn btn-primary"
              onClick={handleGrantConsent}
              disabled={!consents.authentication || !consents.dataProcessing}
            >
              Grant Consent & Continue
            </button>
          )}
        </div>

        <div style={{ marginTop: '2rem', display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
          {steps.map((_, i) => (
            <div
              key={i}
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: i === step ? 'var(--primary)' : 'var(--surface)'
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ConsentOnboarding;
