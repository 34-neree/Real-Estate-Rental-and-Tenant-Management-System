// Auth module - handles login/logout and token management
const Auth = {
  TOKEN_KEY: 'rental_token',
  USER_KEY: 'rental_user',

  getToken() { return localStorage.getItem(this.TOKEN_KEY); },
  getUser() { try { return JSON.parse(localStorage.getItem(this.USER_KEY)); } catch { return null; } },
  setSession(token, user) {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },
  clearSession() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  },
  isLoggedIn() { return !!this.getToken(); },
  headers() {
    const h = { 'Content-Type': 'application/json' };
    const t = this.getToken();
    if (t) h['Authorization'] = `Bearer ${t}`;
    return h;
  },
  async login(email, password) {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch('/api/auth/login', { method: 'POST', body });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Login failed'); }
    const data = await res.json();
    this.setSession(data.access_token, data.user);
    return data;
  },
  logout() { this.clearSession(); window.location.href = '/login'; }
};

// Login form handler
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('loginForm');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const errEl = document.getElementById('loginError');
    btn.disabled = true;
    btn.textContent = 'Signing in...';
    errEl.style.display = 'none';
    try {
      await Auth.login(form.email.value, form.password.value);
      window.location.href = '/';
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = 'block';
    } finally {
      btn.disabled = false;
      btn.textContent = 'Sign In';
    }
  });
});
