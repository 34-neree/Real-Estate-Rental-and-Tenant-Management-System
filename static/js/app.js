// Main application logic
const API = {
  async request(url, options = {}) {
    const res = await fetch(url, { ...options, headers: Auth.headers() });
    if (res.status === 401) { Auth.logout(); return; }
    if (res.status === 204) return null;
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Request failed'); }
    return res.json();
  },
  get(url) { return this.request(url); },
  post(url, data) { return this.request(url, { method: 'POST', body: JSON.stringify(data) }); },
  put(url, data) { return this.request(url, { method: 'PUT', body: JSON.stringify(data) }); },
  del(url) { return this.request(url, { method: 'DELETE' }); }
};

const Toast = {
  show(msg, type = 'info') {
    let c = document.querySelector('.toast-container');
    if (!c) { c = document.createElement('div'); c.className = 'toast-container'; document.body.appendChild(c); }
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<span class="toast-message">${msg}</span>`;
    c.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3500);
  }
};

function openModal(id) { document.getElementById(id)?.classList.add('active'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('active'); }
function badge(val) { return `<span class="badge-status badge-${val}">${val.replace('_',' ')}</span>`; }
function formatDate(d) { return d ? new Date(d).toLocaleDateString() : '—'; }
function formatMoney(v) { return v != null ? `$${Number(v).toLocaleString()}` : '—'; }

// Sidebar toggle for mobile
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle)
        sidebar.classList.remove('open');
    });
  }
  // Set user info in header
  const user = Auth.getUser();
  if (user) {
    const nameEl = document.getElementById('userName');
    const roleEl = document.getElementById('userRole');
    const avatarEl = document.getElementById('userAvatar');
    if (nameEl) nameEl.textContent = user.full_name;
    if (roleEl) roleEl.textContent = user.role;
    if (avatarEl) avatarEl.textContent = user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2);
  }
  // Active nav highlight
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item[data-page]').forEach(el => {
    const page = el.getAttribute('data-page');
    if (path === page || (page !== '/' && path.startsWith(page))) el.classList.add('active');
  });
});

// ── Page-specific loaders ──────────────────────

async function loadDashboard() {
  try {
    const data = await API.get('/api/reports/dashboard');
    document.getElementById('kpiProperties').textContent = data.total_properties;
    document.getElementById('kpiOccupancy').textContent = data.occupancy_rate + '%';
    document.getElementById('kpiTenants').textContent = data.total_active_tenants;
    document.getElementById('kpiLeases').textContent = data.active_leases;
    document.getElementById('kpiIncome').textContent = formatMoney(data.monthly_income);
    document.getElementById('kpiOverdue').textContent = data.overdue_payments;
    document.getElementById('kpiMaintenance').textContent = data.open_maintenance;
    document.getElementById('kpiNet').textContent = formatMoney(data.net_income);
  } catch (e) { Toast.show(e.message, 'error'); }
  // Load income chart
  try {
    const inc = await API.get(`/api/reports/income?year=${new Date().getFullYear()}`);
    const chartData = inc.monthly_breakdown.map(m => ({ label: Charts.monthName(m.month), value: m.total_income }));
    Charts.renderBar('incomeChart', chartData, 'label', 'value', '$');
  } catch (e) { console.error(e); }
}

async function loadProperties() {
  try {
    const props = await API.get('/api/properties/');
    const tbody = document.getElementById('propertiesTable');
    if (!tbody) return;
    tbody.innerHTML = props.length ? props.map(p => `<tr>
      <td><strong>${p.name}</strong></td><td>${p.address}</td><td>${p.city || '—'}</td>
      <td>${p.property_type}</td><td>${badge(p.status)}</td><td>${formatMoney(p.rent_amount)}</td>
      <td>${p.bedrooms}bd/${p.bathrooms}ba</td>
      <td><button class="btn-icon" onclick="editProperty(${p.id})">✏️</button>
          <button class="btn-icon" onclick="deleteProperty(${p.id})">🗑️</button></td>
    </tr>`).join('') : '<tr><td colspan="8" class="empty-state">No properties found</td></tr>';
  } catch (e) { Toast.show(e.message, 'error'); }
}

async function saveProperty(e) {
  e.preventDefault();
  const form = e.target;
  const id = form.dataset.editId;
  const data = {
    name: form.name.value, address: form.address.value, city: form.city.value,
    state: form.state.value, property_type: form.property_type.value,
    rent_amount: parseFloat(form.rent_amount.value), deposit_amount: parseFloat(form.deposit_amount.value || 0),
    bedrooms: parseInt(form.bedrooms.value || 1), bathrooms: parseFloat(form.bathrooms.value || 1),
    description: form.description.value, amenities: form.amenities.value
  };
  try {
    if (id) { await API.put(`/api/properties/${id}`, data); Toast.show('Property updated', 'success'); }
    else { await API.post('/api/properties/', data); Toast.show('Property created', 'success'); }
    closeModal('propertyModal'); loadProperties();
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function editProperty(id) {
  const p = await API.get(`/api/properties/${id}`);
  const form = document.getElementById('propertyForm');
  form.dataset.editId = id;
  form.name.value = p.name; form.address.value = p.address; form.city.value = p.city || '';
  form.state.value = p.state || ''; form.property_type.value = p.property_type;
  form.rent_amount.value = p.rent_amount; form.deposit_amount.value = p.deposit_amount;
  form.bedrooms.value = p.bedrooms; form.bathrooms.value = p.bathrooms;
  form.description.value = p.description || ''; form.amenities.value = p.amenities || '';
  document.querySelector('#propertyModal .modal-header h2').textContent = 'Edit Property';
  openModal('propertyModal');
}
async function deleteProperty(id) {
  if (!confirm('Delete this property?')) return;
  try { await API.del(`/api/properties/${id}`); Toast.show('Property deleted', 'success'); loadProperties(); }
  catch (e) { Toast.show(e.message, 'error'); }
}

async function loadTenants() {
  try {
    const tenants = await API.get('/api/tenants/');
    const tbody = document.getElementById('tenantsTable');
    if (!tbody) return;
    tbody.innerHTML = tenants.length ? tenants.map(t => `<tr>
      <td><strong>${t.first_name} ${t.last_name}</strong></td><td>${t.email}</td>
      <td>${t.phone || '—'}</td><td>${t.occupation || '—'}</td><td>${badge(t.is_active ? 'active' : 'inactive')}</td>
      <td><button class="btn-icon" onclick="editTenant(${t.id})">✏️</button>
          <button class="btn-icon" onclick="deleteTenant(${t.id})">🗑️</button></td>
    </tr>`).join('') : '<tr><td colspan="6" class="empty-state">No tenants found</td></tr>';
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function saveTenant(e) {
  e.preventDefault();
  const form = e.target; const id = form.dataset.editId;
  const data = {
    first_name: form.first_name.value, last_name: form.last_name.value, email: form.email.value,
    phone: form.phone.value, national_id: form.national_id.value, occupation: form.occupation.value,
    employer: form.employer.value, notes: form.notes.value
  };
  try {
    if (id) { await API.put(`/api/tenants/${id}`, data); Toast.show('Tenant updated', 'success'); }
    else { await API.post('/api/tenants/', data); Toast.show('Tenant created', 'success'); }
    closeModal('tenantModal'); loadTenants();
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function editTenant(id) {
  const t = await API.get(`/api/tenants/${id}`);
  const form = document.getElementById('tenantForm');
  form.dataset.editId = id;
  form.first_name.value = t.first_name; form.last_name.value = t.last_name;
  form.email.value = t.email; form.phone.value = t.phone || '';
  form.national_id.value = t.national_id || ''; form.occupation.value = t.occupation || '';
  form.employer.value = t.employer || ''; form.notes.value = t.notes || '';
  document.querySelector('#tenantModal .modal-header h2').textContent = 'Edit Tenant';
  openModal('tenantModal');
}
async function deleteTenant(id) {
  if (!confirm('Delete this tenant?')) return;
  try { await API.del(`/api/tenants/${id}`); Toast.show('Tenant deleted', 'success'); loadTenants(); }
  catch (e) { Toast.show(e.message, 'error'); }
}

async function loadLeases() {
  try {
    const leases = await API.get('/api/leases/');
    const tbody = document.getElementById('leasesTable');
    if (!tbody) return;
    tbody.innerHTML = leases.length ? leases.map(l => `<tr>
      <td>#${l.id}</td><td>${l.property ? l.property.name : l.property_id}</td>
      <td>${l.tenant ? l.tenant.first_name + ' ' + l.tenant.last_name : l.tenant_id}</td>
      <td>${formatDate(l.start_date)}</td><td>${formatDate(l.end_date)}</td>
      <td>${formatMoney(l.rent_amount)}</td><td>${badge(l.status)}</td>
      <td><button class="btn-icon" onclick="editLease(${l.id})">✏️</button>
          <button class="btn-icon" onclick="deleteLease(${l.id})">🗑️</button></td>
    </tr>`).join('') : '<tr><td colspan="8" class="empty-state">No leases found</td></tr>';
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function saveLease(e) {
  e.preventDefault();
  const form = e.target; const id = form.dataset.editId;
  const data = {
    property_id: parseInt(form.property_id.value), tenant_id: parseInt(form.tenant_id.value),
    start_date: form.start_date.value, end_date: form.end_date.value,
    rent_amount: parseFloat(form.rent_amount.value), deposit_amount: parseFloat(form.deposit_amount.value || 0),
    payment_due_day: parseInt(form.payment_due_day.value || 1), late_fee: parseFloat(form.late_fee.value || 0),
    notes: form.notes.value
  };
  try {
    if (id) {
      await API.put(`/api/leases/${id}`, { end_date: data.end_date, rent_amount: data.rent_amount, notes: data.notes });
      Toast.show('Lease updated', 'success');
    } else { await API.post('/api/leases/', data); Toast.show('Lease created', 'success'); }
    closeModal('leaseModal'); loadLeases();
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function editLease(id) {
  const l = await API.get(`/api/leases/${id}`);
  const form = document.getElementById('leaseForm');
  form.dataset.editId = id;
  form.property_id.value = l.property_id; form.tenant_id.value = l.tenant_id;
  form.start_date.value = l.start_date?.slice(0,16); form.end_date.value = l.end_date?.slice(0,16);
  form.rent_amount.value = l.rent_amount; form.deposit_amount.value = l.deposit_amount;
  form.payment_due_day.value = l.payment_due_day; form.late_fee.value = l.late_fee;
  form.notes.value = l.notes || '';
  openModal('leaseModal');
}
async function deleteLease(id) {
  if (!confirm('Delete this lease?')) return;
  try { await API.del(`/api/leases/${id}`); Toast.show('Lease deleted', 'success'); loadLeases(); }
  catch (e) { Toast.show(e.message, 'error'); }
}

async function loadPayments() {
  try {
    const payments = await API.get('/api/payments/');
    const tbody = document.getElementById('paymentsTable');
    if (!tbody) return;
    tbody.innerHTML = payments.length ? payments.map(p => `<tr>
      <td>#${p.id}</td><td>Lease #${p.lease_id}</td><td>${formatMoney(p.amount_due)}</td>
      <td>${formatMoney(p.amount)}</td><td>${p.payment_method.replace('_',' ')}</td>
      <td>${badge(p.status)}</td><td>${formatDate(p.due_date)}</td><td>${formatDate(p.payment_date)}</td>
      <td><button class="btn-icon" onclick="editPayment(${p.id})">✏️</button>
          <button class="btn-icon" onclick="deletePayment(${p.id})">🗑️</button></td>
    </tr>`).join('') : '<tr><td colspan="9" class="empty-state">No payments found</td></tr>';
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function savePayment(e) {
  e.preventDefault();
  const form = e.target; const id = form.dataset.editId;
  const data = {
    lease_id: parseInt(form.lease_id.value), tenant_id: parseInt(form.tenant_id.value),
    amount: parseFloat(form.amount.value), amount_due: parseFloat(form.amount_due.value),
    payment_method: form.payment_method.value, due_date: form.due_date.value,
    period_month: parseInt(form.period_month.value || 0) || null,
    period_year: parseInt(form.period_year.value || 0) || null,
    notes: form.notes.value, transaction_ref: form.transaction_ref.value
  };
  try {
    if (id) {
      await API.put(`/api/payments/${id}`, { amount: data.amount, payment_method: data.payment_method,
        payment_date: form.payment_date?.value || null, notes: data.notes, transaction_ref: data.transaction_ref });
      Toast.show('Payment updated', 'success');
    } else { await API.post('/api/payments/', data); Toast.show('Payment recorded', 'success'); }
    closeModal('paymentModal'); loadPayments();
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function editPayment(id) {
  const p = await API.get(`/api/payments/${id}`);
  const form = document.getElementById('paymentForm');
  form.dataset.editId = id;
  form.lease_id.value = p.lease_id; form.tenant_id.value = p.tenant_id;
  form.amount.value = p.amount; form.amount_due.value = p.amount_due;
  form.payment_method.value = p.payment_method; form.due_date.value = p.due_date?.slice(0,16);
  form.notes.value = p.notes || ''; form.transaction_ref.value = p.transaction_ref || '';
  openModal('paymentModal');
}
async function deletePayment(id) {
  if (!confirm('Delete this payment?')) return;
  try { await API.del(`/api/payments/${id}`); Toast.show('Payment deleted', 'success'); loadPayments(); }
  catch (e) { Toast.show(e.message, 'error'); }
}

async function loadMaintenance() {
  try {
    const reqs = await API.get('/api/maintenance/');
    const tbody = document.getElementById('maintenanceTable');
    if (!tbody) return;
    tbody.innerHTML = reqs.length ? reqs.map(r => `<tr>
      <td>#${r.id}</td><td><strong>${r.title}</strong></td><td>${r.property_id}</td>
      <td>${badge(r.priority)}</td><td>${badge(r.status)}</td>
      <td>${r.assigned_to || '—'}</td><td>${formatDate(r.created_at)}</td>
      <td><button class="btn-icon" onclick="editMaintenance(${r.id})">✏️</button>
          <button class="btn-icon" onclick="deleteMaintenance(${r.id})">🗑️</button></td>
    </tr>`).join('') : '<tr><td colspan="8" class="empty-state">No requests found</td></tr>';
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function saveMaintenance(e) {
  e.preventDefault();
  const form = e.target; const id = form.dataset.editId;
  const data = {
    property_id: parseInt(form.property_id.value), title: form.title.value,
    description: form.description.value, priority: form.priority.value,
    assigned_to: form.assigned_to.value, estimated_cost: parseFloat(form.estimated_cost.value || 0) || null,
    notes: form.notes.value
  };
  try {
    if (id) {
      await API.put(`/api/maintenance/${id}`, { ...data, status: form.status?.value });
      Toast.show('Request updated', 'success');
    } else { await API.post('/api/maintenance/', data); Toast.show('Request created', 'success'); }
    closeModal('maintenanceModal'); loadMaintenance();
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function editMaintenance(id) {
  const r = await API.get(`/api/maintenance/${id}`);
  const form = document.getElementById('maintenanceForm');
  form.dataset.editId = id;
  form.property_id.value = r.property_id; form.title.value = r.title;
  form.description.value = r.description; form.priority.value = r.priority;
  form.assigned_to.value = r.assigned_to || ''; form.estimated_cost.value = r.estimated_cost || '';
  form.notes.value = r.notes || '';
  if (form.status) form.status.value = r.status;
  openModal('maintenanceModal');
}
async function deleteMaintenance(id) {
  if (!confirm('Delete this request?')) return;
  try { await API.del(`/api/maintenance/${id}`); Toast.show('Request deleted', 'success'); loadMaintenance(); }
  catch (e) { Toast.show(e.message, 'error'); }
}

async function loadExpenses() {
  try {
    const expenses = await API.get('/api/expenses/');
    const tbody = document.getElementById('expensesTable');
    if (!tbody) return;
    tbody.innerHTML = expenses.length ? expenses.map(ex => `<tr>
      <td>#${ex.id}</td><td>${ex.category}</td><td>${formatMoney(ex.amount)}</td>
      <td>${ex.vendor || '—'}</td><td>${ex.description || '—'}</td><td>${formatDate(ex.date)}</td>
      <td><button class="btn-icon" onclick="editExpense(${ex.id})">✏️</button>
          <button class="btn-icon" onclick="deleteExpense(${ex.id})">🗑️</button></td>
    </tr>`).join('') : '<tr><td colspan="7" class="empty-state">No expenses found</td></tr>';
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function saveExpense(e) {
  e.preventDefault();
  const form = e.target; const id = form.dataset.editId;
  const data = {
    category: form.category.value, amount: parseFloat(form.amount.value),
    description: form.description.value, date: form.date.value,
    vendor: form.vendor.value, receipt_ref: form.receipt_ref.value,
    property_id: parseInt(form.property_id.value) || null
  };
  try {
    if (id) { await API.put(`/api/expenses/${id}`, data); Toast.show('Expense updated', 'success'); }
    else { await API.post('/api/expenses/', data); Toast.show('Expense recorded', 'success'); }
    closeModal('expenseModal'); loadExpenses();
  } catch (e) { Toast.show(e.message, 'error'); }
}
async function editExpense(id) {
  const ex = await API.get(`/api/expenses/${id}`);
  const form = document.getElementById('expenseForm');
  form.dataset.editId = id;
  form.category.value = ex.category; form.amount.value = ex.amount;
  form.description.value = ex.description || ''; form.date.value = ex.date?.slice(0,16);
  form.vendor.value = ex.vendor || ''; form.receipt_ref.value = ex.receipt_ref || '';
  form.property_id.value = ex.property_id || '';
  openModal('expenseModal');
}
async function deleteExpense(id) {
  if (!confirm('Delete this expense?')) return;
  try { await API.del(`/api/expenses/${id}`); Toast.show('Expense deleted', 'success'); loadExpenses(); }
  catch (e) { Toast.show(e.message, 'error'); }
}

async function loadReports() {
  try {
    const pl = await API.get(`/api/reports/profit-loss?year=${new Date().getFullYear()}`);
    const chartData = pl.monthly.map(m => ({ label: Charts.monthName(m.month), value: m.profit }));
    Charts.renderBar('profitChart', chartData, 'label', 'value', '$');
    document.getElementById('annualIncome').textContent = formatMoney(pl.annual_income);
    document.getElementById('annualExpenses').textContent = formatMoney(pl.annual_expenses);
    document.getElementById('annualProfit').textContent = formatMoney(pl.annual_profit);
  } catch (e) { console.error(e); }
  try {
    const exp = await API.get(`/api/reports/expenses?year=${new Date().getFullYear()}`);
    const tbody = document.getElementById('expenseCategoryTable');
    if (tbody) tbody.innerHTML = exp.by_category.map(c =>
      `<tr><td>${c.category}</td><td>${formatMoney(c.total)}</td></tr>`).join('');
  } catch (e) { console.error(e); }
}

function resetForm(formId) {
  const form = document.getElementById(formId);
  if (form) { form.reset(); delete form.dataset.editId; }
}
