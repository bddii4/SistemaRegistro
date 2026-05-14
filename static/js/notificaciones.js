/**
 * notificaciones.js
 * Utilidad compartida para WebSocket y toasts en Regintra.
 * Se incluye desde base.html y lo usan dashboard_empleado y dashboard_admin.
 */

// ── Toast universal ────────────────────────────────────────────────────────
function regintraToast(mensaje, tipo = 'success', duracion = 4000) {
  let wrap = document.getElementById('rg-toast-wrap');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.id = 'rg-toast-wrap';
    wrap.className = 'toast-container position-fixed top-0 end-0 p-3';
    wrap.style.zIndex = 99999;
    document.body.appendChild(wrap);
  }
  const t = document.createElement('div');
  t.className = `toast align-items-center text-bg-${tipo} border-0 show`;
  t.setAttribute('role', 'alert');
  t.innerHTML = `
    <div class="d-flex">
      <div class="toast-body fw-semibold">${mensaje}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  wrap.appendChild(t);
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 300);
  }, duracion);
}

// ── Conexión WebSocket con reconexión automática ───────────────────────────
class RegintraWS {
  constructor({ onSolicitud, onNuevoReporte, onConectado, onDesconectado } = {}) {
    this.onSolicitud    = onSolicitud    || (() => {});
    this.onNuevoReporte = onNuevoReporte || (() => {});
    this.onConectado    = onConectado    || (() => {});
    this.onDesconectado = onDesconectado || (() => {});
    this.intentos = 0;
    this.connect();
  }

  connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    this.ws = new WebSocket(`${proto}://${location.host}/ws/monitor/`);

    this.ws.onopen = () => {
      this.intentos = 0;
      this.onConectado();
    };

    this.ws.onclose = () => {
      this.onDesconectado();
      // Reconexión exponencial: 2s, 4s, 8s … máx 30s
      const delay = Math.min(2000 * Math.pow(2, this.intentos), 30000);
      this.intentos++;
      setTimeout(() => this.connect(), delay);
    };

    this.ws.onerror = () => this.ws.close();

    this.ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.tipo === 'solicitud')     this.onSolicitud(data);
        if (data.tipo === 'nuevo_reporte') this.onNuevoReporte(data);
      } catch (_) {}
    };
  }

  send(obj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
    }
  }
}

// ── CSRF helper ───────────────────────────────────────────────────────────
function getCSRF() {
  return document.cookie.split(';').map(c => c.trim())
    .find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
}