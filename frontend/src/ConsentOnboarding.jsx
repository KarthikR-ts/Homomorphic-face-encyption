import React, { useState } from 'react';
import Button from './components/Button';

const ConsentOnboarding = ({ userId, onComplete }) => {
  const [step, setStep] = useState(0);
  const [consents, setConsents] = useState({
    authentication: false,
    dataProcessing: false,
    analytics: false
  });
  const [isLoading, setIsLoading] = useState(false);

  const steps = [
    {
      title: 'Welcome to FHE.Face',
      description: 'Next-generation biometric authentication powered by fully homomorphic encryption. Your privacy is mathematically guaranteed.',
      icon: '🔐',
      gradient: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)'
    },
    {
      title: 'How It Works',
      description: 'Your face is converted to an encrypted mathematical representation using CKKS homomorphic encryption. All matching computations happen entirely in encrypted space — we never see your actual biometric data.',
      icon: '🧮',
      gradient: 'linear-gradient(135deg, #06b6d4 0%, #10b981 100%)'
    },
    {
      title: 'Your Consent Matters',
      description: 'We require your explicit permission to process biometric data. You maintain full control and can revoke access or delete your data at any time.',
      icon: '✓',
      gradient: 'linear-gradient(135deg, #f472b6 0%, #ec4899 100%)'
    }
  ];

  const handleGrantConsent = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('token');

      if (!token) {
        throw new Error('Authentication token not found. Please log in again.');
      }
      if (!userId) {
        throw new Error('User ID not found. Please log in again.');
      }

      console.log('Granting consent for user:', userId);
      const apiUrl = import.meta.env.VITE_API_URL || '';

      const authResponse = await fetch(`${apiUrl}/api/consent/grant`, {

        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: userId,
          purpose: 'AUTHENTICATION',
          consent_text: 'I consent to the processing of my biometric data for authentication purposes using homomorphic encryption.',
          expires_in_days: 365
        })
      });

      if (!authResponse.ok) {
        const errorData = await authResponse.json().catch(() => ({}));
        const errorMsg = errorData.error || errorData.message || `Server error: ${authResponse.status}`;

        if (authResponse.status === 401 || errorMsg.toLowerCase().includes('token')) {
          console.error('JWT token invalid - clearing session');
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          alert('Session expired. Please log in again.');
          window.location.reload();
          return;
        }

        throw new Error(errorMsg);
      }

      onComplete();
    } catch (err) {
      console.error('Consent grant error:', err);
      alert('Failed to grant consent: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Styles object
  const styles = {
    container: {
      position: 'fixed',
      inset: 0,
      width: '100%',
      height: '100%',
      background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, #030308 50%, rgba(16, 185, 129, 0.05) 100%)',
      backgroundColor: '#030308',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem',
      zIndex: 50,
      overflow: 'hidden',
      fontFamily: 'Outfit, sans-serif'
    },
    card: {
      width: '100%',
      maxWidth: '560px',
      background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%)',
      backdropFilter: 'blur(24px)',
      WebkitBackdropFilter: 'blur(24px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '28px',
      padding: '2.5rem',
      textAlign: 'center',
      boxShadow: '0 24px 80px rgba(0, 0, 0, 0.5), 0 0 60px rgba(139, 92, 246, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
      display: 'flex',
      flexDirection: 'column',
      animation: 'scaleIn 0.5s ease-out'
    },
    skipButton: {
      background: 'transparent',
      border: 'none',
      color: 'var(--text-dim)',
      fontSize: '0.875rem',
      fontWeight: 500,
      cursor: 'pointer',
      padding: '0.5rem',
      marginLeft: 'auto',
      transition: 'color 0.3s ease'
    },
    iconContainer: {
      width: '96px',
      height: '96px',
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      margin: '0 auto 2rem',
      fontSize: '2.5rem',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), inset 0 -2px 0 rgba(0, 0, 0, 0.2), inset 0 2px 0 rgba(255, 255, 255, 0.2)',
      border: '1px solid rgba(255, 255, 255, 0.15)'
    },
    title: {
      fontSize: '2rem',
      fontWeight: 700,
      color: 'var(--text-main)',
      marginBottom: '1rem',
      letterSpacing: '-0.02em',
      background: 'linear-gradient(135deg, #f8fafc 0%, #a78bfa 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text'
    },
    description: {
      color: 'var(--text-muted)',
      fontSize: '1rem',
      lineHeight: 1.7,
      marginBottom: '2rem',
      maxWidth: '480px',
      margin: '0 auto 2rem'
    },
    consentBox: {
      background: 'rgba(255, 255, 255, 0.03)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '20px',
      padding: '1.5rem',
      marginBottom: '2rem',
      textAlign: 'left'
    },
    consentTitle: {
      color: 'var(--text-main)',
      fontWeight: 600,
      marginBottom: '1.25rem',
      fontSize: '0.9375rem'
    },
    checkboxLabel: (isChecked) => ({
      display: 'flex',
      alignItems: 'flex-start',
      gap: '1rem',
      padding: '1rem',
      borderRadius: '14px',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      border: `1px solid ${isChecked ? 'rgba(139, 92, 246, 0.4)' : 'rgba(255, 255, 255, 0.05)'}`,
      background: isChecked ? 'rgba(139, 92, 246, 0.12)' : 'rgba(255, 255, 255, 0.02)',
      marginBottom: '0.75rem'
    }),
    checkbox: {
      width: '22px',
      height: '22px',
      border: '2px solid rgba(139, 92, 246, 0.5)',
      borderRadius: '6px',
      background: 'rgba(139, 92, 246, 0.1)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      marginTop: '2px',
      transition: 'all 0.3s ease'
    },
    checkboxChecked: {
      width: '22px',
      height: '22px',
      border: '2px solid #8b5cf6',
      borderRadius: '6px',
      background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      marginTop: '2px',
      boxShadow: '0 0 16px rgba(139, 92, 246, 0.4)'
    },
    checkmark: {
      color: 'white',
      fontSize: '0.75rem',
      fontWeight: 'bold'
    },
    labelTitle: {
      color: 'var(--text-main)',
      fontWeight: 600,
      fontSize: '0.9375rem',
      marginBottom: '0.25rem',
      display: 'block'
    },
    labelDesc: {
      color: 'var(--text-muted)',
      fontSize: '0.8125rem',
      lineHeight: 1.5,
      display: 'block'
    },
    securityNote: {
      background: 'rgba(139, 92, 246, 0.06)',
      border: '1px solid rgba(139, 92, 246, 0.15)',
      borderRadius: '14px',
      padding: '1.25rem',
      marginTop: '1.25rem'
    },
    securityItem: {
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      fontSize: '0.875rem',
      color: 'var(--text-secondary)',
      marginBottom: '0.625rem'
    },
    securityCheck: {
      color: '#10b981',
      fontWeight: 700,
      fontSize: '1rem'
    },
    navigation: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '1rem',
      marginTop: '0.5rem'
    },
    stepIndicators: {
      display: 'flex',
      gap: '0.75rem',
      justifyContent: 'center',
      marginTop: '2rem'
    },
    stepDot: (isActive) => ({
      width: isActive ? '32px' : '10px',
      height: '10px',
      borderRadius: '5px',
      background: isActive
        ? 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)'
        : 'rgba(255, 255, 255, 0.15)',
      border: 'none',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      boxShadow: isActive ? '0 0 20px rgba(139, 92, 246, 0.4)' : 'none'
    })
  };

  return (
    <div style={styles.container}>
      {/* Background Orbs */}
      <div style={{
        position: 'fixed',
        top: '10%',
        left: '10%',
        width: '400px',
        height: '400px',
        background: 'radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%)',
        borderRadius: '50%',
        filter: 'blur(80px)',
        animation: 'float 10s ease-in-out infinite',
        pointerEvents: 'none'
      }} />
      <div style={{
        position: 'fixed',
        bottom: '10%',
        right: '10%',
        width: '300px',
        height: '300px',
        background: 'radial-gradient(circle, rgba(16, 185, 129, 0.12) 0%, transparent 70%)',
        borderRadius: '50%',
        filter: 'blur(60px)',
        animation: 'float 12s ease-in-out infinite reverse',
        pointerEvents: 'none'
      }} />

      {/* Glass Card */}
      <div style={styles.card}>
        {/* Skip Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.5rem', height: '28px' }}>
          {step === 0 && (
            <button
              onClick={() => setStep(2)}
              style={styles.skipButton}
              onMouseOver={(e) => e.target.style.color = 'var(--text-secondary)'}
              onMouseOut={(e) => e.target.style.color = 'var(--text-dim)'}
            >
              Skip →
            </button>
          )}
        </div>

        {/* Icon */}
        <div style={{ ...styles.iconContainer, background: steps[step].gradient }}>
          {steps[step].icon}
        </div>

        {/* Title */}
        <h2 style={styles.title}>{steps[step].title}</h2>

        {/* Description */}
        <p style={styles.description}>{steps[step].description}</p>

        {/* Consent Form (Step 3) */}
        {step === 2 && (
          <div style={styles.consentBox}>
            <h4 style={styles.consentTitle}>Required Permissions</h4>

            {/* Biometric Authentication */}
            <label
              style={styles.checkboxLabel(consents.authentication)}
              onClick={() => setConsents({ ...consents, authentication: !consents.authentication })}
            >
              <div style={consents.authentication ? styles.checkboxChecked : styles.checkbox}>
                {consents.authentication && <span style={styles.checkmark}>✓</span>}
              </div>
              <div>
                <span style={styles.labelTitle}>Biometric Authentication</span>
                <span style={styles.labelDesc}>Process encrypted face embeddings for secure passwordless login</span>
              </div>
            </label>

            {/* Encrypted Data Storage */}
            <label
              style={styles.checkboxLabel(consents.dataProcessing)}
              onClick={() => setConsents({ ...consents, dataProcessing: !consents.dataProcessing })}
            >
              <div style={consents.dataProcessing ? styles.checkboxChecked : styles.checkbox}>
                {consents.dataProcessing && <span style={styles.checkmark}>✓</span>}
              </div>
              <div>
                <span style={styles.labelTitle}>Encrypted Data Storage</span>
                <span style={styles.labelDesc}>Store encrypted biometric templates in our zero-knowledge database</span>
              </div>
            </label>

            {/* Security Note */}
            <div style={styles.securityNote}>
              <div style={styles.securityItem}>
                <span style={styles.securityCheck}>✓</span>
                128-bit Fully Homomorphic Encryption (CKKS)
              </div>
              <div style={styles.securityItem}>
                <span style={styles.securityCheck}>✓</span>
                Revoke consent and delete data anytime
              </div>
              <div style={{ ...styles.securityItem, marginBottom: 0 }}>
                <span style={styles.securityCheck}>✓</span>
                GDPR & India's DPDP Act 2023 compliant
              </div>
            </div>
          </div>
        )}

        {/* Navigation & Actions */}
        <div style={styles.navigation}>
          {step > 0 && (
            <Button variant="ghost" onClick={() => setStep(step - 1)}>
              ← Back
            </Button>
          )}

          {step < 2 ? (
            <Button onClick={() => setStep(step + 1)}>
              Continue →
            </Button>
          ) : (
            <Button
              onClick={handleGrantConsent}
              disabled={!consents.authentication || !consents.dataProcessing}
              loading={isLoading}
              glow
            >
              🔐 Grant Consent & Continue
            </Button>
          )}
        </div>

        {/* Step Indicators */}
        <div style={styles.stepIndicators}>
          {steps.map((_, i) => (
            <button
              key={i}
              onClick={() => setStep(i)}
              aria-label={`Go to step ${i + 1}`}
              style={styles.stepDot(i === step)}
            />
          ))}
        </div>
      </div>

      {/* Keyframe animations */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-20px); }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
};

export default ConsentOnboarding;
