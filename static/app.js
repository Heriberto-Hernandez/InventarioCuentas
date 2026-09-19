let cuentas = [];
let usuarioActual = null;
let rarezas = [];

// ELEMENTOS DOM
const contenedorCuentas = document.getElementById("contenedorCuentas");
const modal = document.getElementById("modalCuadricula");
const btnCerrarModal = document.getElementById("btnCerrarModal");
const gridContenedor = document.getElementById("gridContenedor");
const modalTituloCuenta = document.getElementById("modalTituloCuenta");
const modalSubtituloCuenta = document.getElementById("modalSubtituloCuenta");
const buscadorInput = document.getElementById("buscadorInput");
const btnAgregarCuenta = document.getElementById("btnAgregarCuenta");
const btnHamburguesa = document.getElementById("btnHamburguesa");
const sidebarMenu = document.getElementById("sidebarMenu");
const loginVista = document.getElementById("loginVista");
const appVista = document.getElementById("appVista");
const btnLoginLocal = document.getElementById("btnLoginLocal");
const googleButton = document.getElementById("googleButton");
const btnCerrarSesion = document.getElementById("btnCerrarSesion");
const modalAgregarCuenta = document.getElementById("modalAgregarCuenta");
const formAgregarCuenta = document.getElementById("formAgregarCuenta");
const btnCerrarAgregarCuenta = document.getElementById("btnCerrarAgregarCuenta");
const btnCancelarAgregarCuenta = document.getElementById("btnCancelarAgregarCuenta");
const btnGuardarCuenta = document.getElementById("btnGuardarCuenta");
const errorAgregarCuenta = document.getElementById("errorAgregarCuenta");
const btnAgregarBrainrot = document.getElementById("btnAgregarBrainrot");
const modalAgregarBrainrot = document.getElementById("modalAgregarBrainrot");
const formAgregarBrainrot = document.getElementById("formAgregarBrainrot");
const btnCerrarAgregarBrainrot = document.getElementById("btnCerrarAgregarBrainrot");
const btnCancelarAgregarBrainrot = document.getElementById("btnCancelarAgregarBrainrot");
const btnGuardarBrainrot = document.getElementById("btnGuardarBrainrot");
const errorAgregarBrainrot = document.getElementById("errorAgregarBrainrot");
const tituloFormularioBrainrot = document.getElementById("tituloFormularioBrainrot");
let cuentaSeleccionada = null;
let brainrotEditando = null;

function estiloRareza(nombre) {
  const rareza = rarezas.find(item => item.nombre === nombre);
  if (!rareza) return "";
  return `background:${rareza.color};color:${rareza.texto};border-color:${rareza.color}`;
}

async function cargarRarezas() {
  const res = await fetch("/api/rarezas");
  if (!res.ok) throw new Error("No se pudieron cargar las rarezas");
  rarezas = await res.json();
  const selector = document.getElementById("rarezaBrainrotInput");
  selector.innerHTML = rarezas.map(rareza =>
    `<option value="${rareza.nombre}">${rareza.nombre}</option>`
  ).join("");
}

// MENÚ LATERAL Y MODAL
btnHamburguesa.addEventListener("click", () => sidebarMenu.classList.toggle("abierto"));
btnCerrarModal.addEventListener("click", () => modal.classList.remove("activo"));
modal.addEventListener("click", (e) => {
  if (e.target === modal) modal.classList.remove("activo");
});

// 1. CARGAR DATOS DESDE LA BASE DE DATOS
async function cargarDatosBD() {
  try {
    const res = await fetch("/api/cuentas", { credentials: "same-origin" });
    if (res.status === 401) return mostrarLogin();
    cuentas = await res.json();
    renderizarCuentas();
  } catch (error) {
    console.error("Error al conectar con la base de datos:", error);
  }
}

function mostrarLogin() {
  loginVista.classList.remove("oculta");
  appVista.classList.add("oculta");
}

function mostrarApp(usuario) {
  usuarioActual = usuario;
  loginVista.classList.add("oculta");
  appVista.classList.remove("oculta");
  document.getElementById("labelUsuario").textContent = usuario.nombre;
  document.querySelector(".avatar-mini").textContent = usuario.nombre.charAt(0).toUpperCase();
  cargarDatosBD();
}

// 2. RENDERIZAR
function renderizarCuentas(lista = cuentas) {
  contenedorCuentas.innerHTML = "";

  lista.forEach(cuenta => {
    const bloque = document.createElement("div");
    bloque.className = "cuenta-bloque";

    bloque.innerHTML = `
      <div class="cuenta-header">
        <div>
          <h3>🎮 @${cuenta.user_cuenta}</h3>
          <span class="subtitulo">Espacio: ${cuenta.inventario.length} / ${cuenta.espacio_maximo} slots</span>
        </div>
        <button class="btn-secondary" onclick="abrirModalCuadricula(${cuenta.id_cuenta})">Ver Cuadrícula</button>
      </div>
      <div class="scroll-horizontal">
        ${cuenta.inventario.map(item => `
          <div class="card-mini" style="${estiloRareza(item.rareza)}" onclick="abrirModalCuadricula(${cuenta.id_cuenta})">
            <span style="font-size: 1.8rem;">${item.icono}</span>
            <strong style="font-size: 0.85rem;">${item.nombre}</strong>
            <span class="tag-mutacion" style="${estiloRareza(item.rareza)}">${item.rareza}</span>
          </div>
        `).join("")}
      </div>
    `;

    contenedorCuentas.appendChild(bloque);
  });
}

// 3. ABRIR MODAL
window.abrirModalCuadricula = function(idCuenta) {
  const cuenta = cuentas.find(c => c.id_cuenta === idCuenta);
  if (!cuenta) return;
  cuentaSeleccionada = idCuenta;

  modalTituloCuenta.textContent = `@${cuenta.user_cuenta}`;
  modalSubtituloCuenta.textContent = `Capacidad: ${cuenta.inventario.length} de ${cuenta.espacio_maximo} slots`;

  gridContenedor.innerHTML = cuenta.inventario.map(item => `
    <div class="card-grid" style="${estiloRareza(item.rareza)}">
      <span style="font-size: 2.2rem;">${item.icono}</span>
      <strong>${item.nombre}</strong>
      <span class="tag-mutacion" style="${estiloRareza(item.rareza)}">${item.rareza}</span>
      <span class="mutacion-label">Mutación: ${item.mutacion}</span>
      <span style="color: var(--verde-dinero); font-size: 0.85rem;">+$${item.dinero.toLocaleString()}/s</span>
      <div class="card-actions">
        <button class="btn-secondary btn-small" type="button" onclick="editarBrainrot(${item.id_inventario})">Editar</button>
        <button class="btn-secondary btn-small" type="button" onclick="duplicarBrainrot(${item.id_inventario})">Duplicar</button>
      </div>
    </div>
  `).join("");

  modal.classList.add("activo");
};

function cerrarModalAgregarBrainrot() {
  modalAgregarBrainrot.classList.remove("activo");
  formAgregarBrainrot.reset();
  brainrotEditando = null;
  tituloFormularioBrainrot.textContent = "Agregar brainrot";
  errorAgregarBrainrot.textContent = "";
  btnGuardarBrainrot.disabled = false;
  btnGuardarBrainrot.textContent = "Guardar brainrot";
}

btnAgregarBrainrot.addEventListener("click", () => {
  brainrotEditando = null;
  tituloFormularioBrainrot.textContent = "Agregar brainrot";
  btnGuardarBrainrot.textContent = "Guardar brainrot";
  errorAgregarBrainrot.textContent = "";
  modalAgregarBrainrot.classList.add("activo");
  document.getElementById("nombreBrainrotInput").focus();
});

window.editarBrainrot = function(inventoryId) {
  const cuenta = cuentas.find(item => item.id_cuenta === cuentaSeleccionada);
  const brainrot = cuenta?.inventario.find(item => item.id_inventario === inventoryId);
  if (!brainrot) return;
  brainrotEditando = inventoryId;
  tituloFormularioBrainrot.textContent = "Editar brainrot";
  document.getElementById("nombreBrainrotInput").value = brainrot.nombre;
  document.getElementById("rarezaBrainrotInput").value = brainrot.rareza;
  document.getElementById("iconoBrainrotInput").value = brainrot.icono;
  document.getElementById("mutacionBrainrotInput").value = brainrot.mutacion;
  document.getElementById("dineroBrainrotInput").value = brainrot.dinero;
  errorAgregarBrainrot.textContent = "";
  modalAgregarBrainrot.classList.add("activo");
  document.getElementById("nombreBrainrotInput").focus();
};

window.duplicarBrainrot = async function(inventoryId) {
  try {
    const res = await fetch(`/api/inventario/${inventoryId}/duplicar`, {
      method: "POST", credentials: "same-origin"
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      alert(error.detail || `Error al duplicar (${res.status})`);
      return;
    }
    await cargarDatosBD();
    abrirModalCuadricula(cuentaSeleccionada);
  } catch (error) {
    alert("No se pudo conectar con el servidor");
  }
};
btnCerrarAgregarBrainrot.addEventListener("click", cerrarModalAgregarBrainrot);
btnCancelarAgregarBrainrot.addEventListener("click", cerrarModalAgregarBrainrot);
modalAgregarBrainrot.addEventListener("click", (event) => {
  if (event.target === modalAgregarBrainrot) cerrarModalAgregarBrainrot();
});

formAgregarBrainrot.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(formAgregarBrainrot));
  data.generacion_dinero = Number(data.generacion_dinero);
  btnGuardarBrainrot.disabled = true;
  btnGuardarBrainrot.textContent = "Guardando...";
  try {
    const url = brainrotEditando
      ? `/api/inventario/${brainrotEditando}`
      : `/api/cuentas/${cuentaSeleccionada}/inventario`;
    const res = await fetch(url, {
      method: brainrotEditando ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin", body: JSON.stringify(data)
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      errorAgregarBrainrot.textContent = error.detail || `Error (${res.status})`;
      btnGuardarBrainrot.disabled = false;
      btnGuardarBrainrot.textContent = "Guardar brainrot";
      return;
    }
    cerrarModalAgregarBrainrot();
    modal.classList.remove("activo");
    await cargarDatosBD();
  } catch (error) {
    errorAgregarBrainrot.textContent = "No se pudo conectar con el servidor";
    btnGuardarBrainrot.disabled = false;
    btnGuardarBrainrot.textContent = "Guardar brainrot";
  }
});

// 4. AGREGAR CUENTA
function cerrarModalAgregarCuenta() {
  modalAgregarCuenta.classList.remove("activo");
  formAgregarCuenta.reset();
  errorAgregarCuenta.textContent = "";
  btnGuardarCuenta.disabled = false;
  btnGuardarCuenta.textContent = "Guardar cuenta";
}

btnAgregarCuenta.addEventListener("click", () => {
  errorAgregarCuenta.textContent = "";
  modalAgregarCuenta.classList.add("activo");
  document.getElementById("nombreCuentaInput").focus();
});
btnCerrarAgregarCuenta.addEventListener("click", cerrarModalAgregarCuenta);
btnCancelarAgregarCuenta.addEventListener("click", cerrarModalAgregarCuenta);
modalAgregarCuenta.addEventListener("click", (event) => {
  if (event.target === modalAgregarCuenta) cerrarModalAgregarCuenta();
});

formAgregarCuenta.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(formAgregarCuenta);
  const nombre = formData.get("user_cuenta").trim();
  const espacioMaximo = Number(formData.get("espacio_maximo"));
  if (!nombre || espacioMaximo < 1) return;
  btnGuardarCuenta.disabled = true;
  btnGuardarCuenta.textContent = "Guardando...";
  try {
    const res = await fetch("/api/cuentas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ user_cuenta: nombre, espacio_maximo: espacioMaximo })
    });

    if (res.ok) {
      cerrarModalAgregarCuenta();
      await cargarDatosBD();
    } else {
      const err = await res.json().catch(() => ({}));
      errorAgregarCuenta.textContent = err.detail || `Error al guardar la cuenta (${res.status})`;
      btnGuardarCuenta.disabled = false;
      btnGuardarCuenta.textContent = "Guardar cuenta";
      if (res.status === 401) mostrarLogin();
    }
  } catch (error) {
    errorAgregarCuenta.textContent = "No se pudo conectar con el servidor";
    btnGuardarCuenta.disabled = false;
    btnGuardarCuenta.textContent = "Guardar cuenta";
  }
});

// 5. BUSCADOR EN VIVO
buscadorInput.addEventListener("input", (e) => {
  const texto = e.target.value.toLowerCase().trim();
  if (!texto) {
    renderizarCuentas();
    return;
  }

  const filtradas = cuentas.map(c => {
    const items = c.inventario.filter(i =>
      i.nombre.toLowerCase().includes(texto) ||
      i.mutacion.toLowerCase().includes(texto)
    );
    if (c.user_cuenta.toLowerCase().includes(texto) || items.length > 0) {
      return { ...c, inventario: items };
    }
    return null;
  }).filter(Boolean);

  renderizarCuentas(filtradas);
});

btnLoginLocal.addEventListener("click", async () => {
  const res = await fetch("/api/auth/local", { method: "POST", credentials: "same-origin" });
  if (res.ok) mostrarApp(await res.json());
});

btnCerrarSesion.addEventListener("click", async () => {
  await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
  cuentas = [];
  mostrarLogin();
});

async function iniciarSesion() {
  await cargarRarezas();
  const res = await fetch("/api/auth/me", { credentials: "same-origin" });
  if (res.ok) mostrarApp(await res.json());
  else mostrarLogin();
}

window.handleGoogleCredential = async function(response) {
  const result = await fetch("/api/auth/google", {
    method: "POST", headers: { "Content-Type": "application/json" },
    credentials: "same-origin", body: JSON.stringify({ credential: response.credential })
  });
  if (result.ok) mostrarApp(await result.json());
};

function configurarGoogle() {
  if (!window.GOOGLE_CLIENT_ID || !window.google?.accounts?.id) return;
  window.google.accounts.id.initialize({ client_id: window.GOOGLE_CLIENT_ID, callback: window.handleGoogleCredential });
  window.google.accounts.id.renderButton(googleButton, { theme: "outline", size: "large", width: 280 });
}

window.addEventListener("load", configurarGoogle);

iniciarSesion();