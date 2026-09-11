/**
 * ============================================================================
 * Classiq SC-QFCM Platform - Security Gateway & Access Control Module
 * ============================================================================
 * Provides client-side defense barrier for published deployments.
 * Requires case-sensitive access key before displaying workspace content.
 */

(function () {
  'use strict';

  // Target SHA-256 Hash of access key "Y#N)q"
  const TARGET_HASH = 'c63b02095b0fd019c70cba8ee68cb7d5d982c461f10b85953e578d7de63bc684';
  
  // Obfuscated char-code fallback for non-crypto environments
  const _O_FALLBACK = String.fromCharCode(89, 35, 78, 41, 113);

  const STORAGE_KEY_SESSION = 'sc_qfcm_auth_session';
  const STORAGE_KEY_LOCAL = 'sc_qfcm_auth_remember';

  // Immediate lock state application to prevent FOUC (Flash of Unauthenticated Content)
  function isAlreadyAuthenticated() {
    try {
      return (
        sessionStorage.getItem(STORAGE_KEY_SESSION) === TARGET_HASH ||
        localStorage.getItem(STORAGE_KEY_LOCAL) === TARGET_HASH
      );
    } catch (e) {
      return false;
    }
  }

  if (!isAlreadyAuthenticated()) {
    document.documentElement.classList.add('auth-locked');
  }

  /**
   * Computes SHA-256 hex string using Web Crypto API
   */
  async function computeSHA256(str) {
    if (window.crypto && window.crypto.subtle && window.crypto.subtle.digest) {
      const buffer = new TextEncoder().encode(str);
      const digest = await window.crypto.subtle.digest('SHA-256', buffer);
      return Array.from(new Uint8Array(digest))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');
    }
    return null;
  }

  /**
   * Validates access key input (case-sensitive)
   */
  async function verifyKey(inputKey) {
    if (!inputKey) return false;
    const computed = await computeSHA256(inputKey);
    if (computed) {
      return computed === TARGET_HASH;
    }
    return inputKey === _O_FALLBACK;
  }

  /**
   * Initializes the Security Gateway UI
   */
  function initSecurityGate() {
    if (isAlreadyAuthenticated()) {
      document.documentElement.classList.remove('auth-locked');
      const existingGate = document.getElementById('security-gate');
      if (existingGate) existingGate.remove();
      setupLockButtons();
      return;
    }

    document.documentElement.classList.add('auth-locked');

    // Create gate overlay if not present
    let gate = document.getElementById('security-gate');
    if (!gate) {
      gate = document.createElement('div');
      gate.id = 'security-gate';
      gate.className = 'security-gate-overlay';
      gate.innerHTML = `
        <div class="security-card" id="security-card">
          <div class="security-card-glow"></div>
          
          <div class="security-badge">
            <span class="security-pulse"></span>
            <span>RESTRICTED ACCESS • CLASSIQ SC-QFCM</span>
          </div>

          <div class="security-icon-wrap">
            <svg class="security-shield-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="M9 12l2 2 4-4"/>
            </svg>
          </div>

          <h2 class="security-title">Quantum Workspace Defense</h2>
          <p class="security-desc">
            Authentication required to enter the Classiq Quantum Multi-Depot Field-Technician Dispatch platform and technical case study.
          </p>

          <form id="security-form" class="security-form" onsubmit="return false;">
            <div class="security-input-group">
              <label for="security-key-input" class="security-label">
                <span>Security Access Key</span>
                <span class="security-case-hint">Case-Sensitive</span>
              </label>
              <div class="security-input-wrapper">
                <span class="security-input-icon">🔑</span>
                <input 
                  type="password" 
                  id="security-key-input" 
                  class="security-input" 
                  placeholder="Enter access password..." 
                  autocomplete="current-password"
                  autofocus
                  required
                />
                <button type="button" id="security-toggle-visibility" class="security-eye-btn" title="Show/Hide Password" tabindex="-1">
                  👁️
                </button>
              </div>
            </div>

            <div class="security-options-row">
              <label class="security-checkbox-label">
                <input type="checkbox" id="security-remember" />
                <span>Remember session on this device</span>
              </label>
            </div>

            <div id="security-error-msg" class="security-error-msg" style="display: none;"></div>

            <button type="submit" id="security-submit-btn" class="security-submit-btn">
              <span id="security-btn-text">Unlock Workspace</span>
              <span class="security-btn-arrow">→</span>
            </button>
          </form>

          <div class="security-footer">
            <span>Classiq Technologies &copy; 2026</span>
            <span>•</span>
            <span>Protected Dynamic Simulation Environment</span>
          </div>
        </div>
      `;
      document.body.appendChild(gate);
    }

    // Bind DOM interactions
    const form = document.getElementById('security-form');
    const input = document.getElementById('security-key-input');
    const toggleBtn = document.getElementById('security-toggle-visibility');
    const submitBtn = document.getElementById('security-submit-btn');
    const btnText = document.getElementById('security-btn-text');
    const errorMsg = document.getElementById('security-error-msg');
    const rememberCheck = document.getElementById('security-remember');
    const card = document.getElementById('security-card');

    if (input) {
      setTimeout(() => input.focus(), 100);
    }

    if (toggleBtn && input) {
      toggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (input.type === 'password') {
          input.type = 'text';
          toggleBtn.textContent = '🔒';
        } else {
          input.type = 'password';
          toggleBtn.textContent = '👁️';
        }
      });
    }

    async function handleUnlock() {
      const val = (input ? input.value : '').trim();
      if (!val) {
        showError('Please enter the security access key.');
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        if (btnText) btnText.textContent = 'Verifying...';
      }

      const isValid = await verifyKey(val);

      if (isValid) {
        // Success
        if (errorMsg) errorMsg.style.display = 'none';
        if (card) {
          card.classList.add('auth-success');
        }
        if (btnText) btnText.textContent = 'Access Granted ✓';

        try {
          if (rememberCheck && rememberCheck.checked) {
            localStorage.setItem(STORAGE_KEY_LOCAL, TARGET_HASH);
          } else {
            sessionStorage.setItem(STORAGE_KEY_SESSION, TARGET_HASH);
          }
        } catch (e) {
          console.warn('Storage permission issue', e);
        }

        setTimeout(() => {
          if (gate) {
            gate.classList.add('gate-fade-out');
            setTimeout(() => {
              gate.remove();
              document.documentElement.classList.remove('auth-locked');
              setupLockButtons();
            }, 350);
          } else {
            document.documentElement.classList.remove('auth-locked');
            setupLockButtons();
          }
        }, 400);
      } else {
        // Failed
        if (submitBtn) {
          submitBtn.disabled = false;
          if (btnText) btnText.textContent = 'Unlock Workspace';
        }
        showError('Access Denied: Invalid Security Key. Key is strictly case-sensitive.');
        if (card) {
          card.classList.add('card-shake');
          setTimeout(() => card.classList.remove('card-shake'), 600);
        }
        if (input) {
          input.select();
          input.focus();
        }
      }
    }

    function showError(msg) {
      if (errorMsg) {
        errorMsg.textContent = msg;
        errorMsg.style.display = 'block';
      }
    }

    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        handleUnlock();
      });
    }
  }

  /**
   * Sets up Lock/Sign Out buttons in header nav
   */
  function setupLockButtons() {
    const lockBtns = document.querySelectorAll('.btn-lock-session');
    lockBtns.forEach((btn) => {
      btn.style.display = 'inline-flex';
      btn.onclick = (e) => {
        e.preventDefault();
        window.lockSecurityGate();
      };
    });
  }

  /**
   * Public lock function
   */
  window.lockSecurityGate = function () {
    try {
      sessionStorage.removeItem(STORAGE_KEY_SESSION);
      localStorage.removeItem(STORAGE_KEY_LOCAL);
    } catch (e) {}
    location.reload();
  };

  // Run on DOM content ready or immediately if already loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSecurityGate);
  } else {
    initSecurityGate();
  }
})();
