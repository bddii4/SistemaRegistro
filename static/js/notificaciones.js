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

function solicitarPermisoNotificacion() {
  if (!('Notification' in window)) return false;
  if (Notification.permission === 'granted') return true;
  if (Notification.permission !== 'denied') {
    Notification.requestPermission();
  }
  return Notification.permission === 'granted';
}

function mostrarNotificacionOS(titulo, cuerpo) {
  if (!('Notification' in window)) return;
  if (Notification.permission === 'granted') {
    try {
      new Notification(titulo, {
        body: cuerpo,
        tag: 'regintra-recordatorio',
        requireInteraction: true,
      });
    } catch (_) {}
  }
}

function reproducirSonidoNotificacion() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();

    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.frequency.value = 660;
    osc1.type = 'sine';
    gain1.gain.setValueAtTime(0.2, ctx.currentTime);
    gain1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
    osc1.start(ctx.currentTime);
    osc1.stop(ctx.currentTime + 0.15);

    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.frequency.value = 880;
    osc2.type = 'sine';
    gain2.gain.setValueAtTime(0.2, ctx.currentTime + 0.12);
    gain2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
    osc2.start(ctx.currentTime + 0.12);
    osc2.stop(ctx.currentTime + 0.35);
  } catch (_) {}
}

class RegintraWS {
  constructor({ onSolicitud, onReSolicitud, onNuevoReporte, onConectado, onDesconectado } = {}) {
    this.onSolicitud    = onSolicitud    || (() => {});
    this.onReSolicitud  = onReSolicitud  || (() => {});
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
      const delay = Math.min(2000 * Math.pow(2, this.intentos), 30000);
      this.intentos++;
      setTimeout(() => this.connect(), delay);
    };

    this.ws.onerror = () => this.ws.close();

    this.ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.tipo === 'solicitud')      this.onSolicitud(data);
        if (data.tipo === 're_solicitud')   this.onReSolicitud(data);
        if (data.tipo === 'nuevo_reporte')  this.onNuevoReporte(data);
      } catch (_) {}
    };
  }

  send(obj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
    }
  }
}

function getCSRF() {
  return document.cookie.split(';').map(c => c.trim())
    .find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
}
