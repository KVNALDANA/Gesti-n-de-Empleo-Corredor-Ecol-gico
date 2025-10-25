// js/main.js
const API = "http://127.0.0.1:5000/api"; // ajusta si tu backend usa otra ruta

/* ---------- Helpers ---------- */
function escapeHtml(str) {
  return String(str || "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'", "&#039;");
}

function showElement(el) { if(el) el.style.display = ""; }
function hideElement(el) { if(el) el.style.display = "none"; }

/* ---------- Auth: register / login / logout ---------- */
async function register(nombre, email, password) {
  const res = await fetch(`${API}/register`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({nombre, email, password})
  });
  return res;
}

async function login(email, password) {
  const res = await fetch(`${API}/login`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({email, password})
  });
  return res;
}

async function logoutServer(token) {
  return fetch(`${API}/logout`, {
    method: "POST",
    headers: {"Authorization": `Token ${token}`}
  });
}

function saveSession(token, nombre) {
  localStorage.setItem("token", token);
  localStorage.setItem("nombre", nombre || "");
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("nombre");
}

/* ---------- UI: mostrar estado de autenticación ---------- */
function renderUserArea() {
  const area = document.getElementById("user-area");
  area.innerHTML = "";
  const nombre = localStorage.getItem("nombre");
  const token = localStorage.getItem("token");

  if (token && nombre) {
    // mostrar usuario y logout
    const div = document.createElement("div");
    div.innerHTML = `Conectado: <strong>${escapeHtml(nombre)}</strong> <button id="logoutBtn" class="btn small">Cerrar sesión</button>`;
    area.appendChild(div);
    // mostrar panel de publicar
    showElement(document.getElementById("publish-panel"));
    // ocultar auth panel
    hideElement(document.getElementById("auth-panel"));
    // attach logout handler
    document.getElementById("logoutBtn").addEventListener("click", async () => {
      const token = localStorage.getItem("token");
      try {
        await logoutServer(token);
      } catch(e) { console.warn("logout server error", e); }
      clearSession();
      location.reload();
    });
  } else {
    // mostrar los forms de login/registro
    document.getElementById("auth-panel").style.display = "";
    hideElement(document.getElementById("publish-panel"));
    // mostrar formularios en user-area (opcional) o dejar en su lugar
    // aquí no agregamos nada extra
  }
}

/* ---------- Ofertas: listar y crear (protegido) ---------- */
async function listarOfertas() {
  try {
    const res = await fetch(`${API}/ofertas`);
    const data = await res.json();
    const cont = document.getElementById("lista-ofertas");
    cont.innerHTML = "";
    if (!Array.isArray(data) || data.length === 0) {
      cont.innerHTML = "<p>No hay ofertas publicadas.</p>";
      return;
    }
    data.forEach(o => {
      const div = document.createElement("div");
      div.className = "oferta";
      div.innerHTML = `
        <h3>${escapeHtml(o.titulo)}</h3>
        <p><strong>Empresa:</strong> ${escapeHtml(o.empresa || "-")}</p>
        <p><strong>Contacto:</strong> ${escapeHtml(o.contacto || "-")}</p>
        <p><strong>Salario:</strong> ${escapeHtml(o.salario || "-")}</p>
        <p>${escapeHtml(o.descripcion || "")}</p>
      `;
      cont.appendChild(div);
    });
  } catch (err) {
    console.error("Error al listar ofertas:", err);
    document.getElementById("lista-ofertas").innerHTML = "<p>Error al cargar las ofertas.</p>";
  }
}

async function crearOferta(titulo, empresa, contacto, salario, descripcion) {
  const token = localStorage.getItem("token") || "";
  const res = await fetch(`${API}/ofertas`, {
    method: "POST",
    headers: {
      "Content-Type":"application/json",
      "Authorization": `Token ${token}`
    },
    body: JSON.stringify({titulo, empresa, contacto, salario, descripcion})
  });
  return res;
}

/* ---------- DOMContentLoaded: enlazar handlers ---------- */
document.addEventListener("DOMContentLoaded", () => {
  renderUserArea();
  listarOfertas();

  // Registro
  document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nombre = document.getElementById("r_nombre").value.trim();
    const email = document.getElementById("r_email").value.trim();
    const password = document.getElementById("r_password").value;
    if (!nombre || !email || !password) { alert("Completa todos los campos de registro."); return; }

    const res = await register(nombre, email, password);
    const data = await res.json().catch(()=>({error:"Respuesta no JSON"}));
    if (res.status === 201) {
      // guardar token si backend devuelve token en register; si no, pedir login
      if (data.token) {
        saveSession(data.token, nombre);
        renderUserArea();
        listarOfertas();
        alert("Registro exitoso. Ya estás conectado.");
      } else {
        alert("Registro exitoso. Por favor inicia sesión.");
      }
    } else {
      alert(data.error || "Error en registro");
    }
  });

  // Login
  document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("l_email").value.trim();
    const password = document.getElementById("l_password").value;
    if (!email || !password) { alert("Completa email y contraseña."); return; }

    const res = await login(email, password);
    const data = await res.json().catch(()=>({error:"Respuesta no JSON"}));
    if (res.ok && data.token) {
      saveSession(data.token, data.nombre || "");
      renderUserArea();
      listarOfertas();
      alert("Inicio de sesión correcto");
    } else {
      alert(data.error || "Credenciales inválidas");
    }
  });

  // Publicar oferta (protegido)
  document.getElementById("publicarForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const titulo = document.getElementById("titulo").value.trim();
    const empresa = document.getElementById("empresa").value.trim();
    const contacto = document.getElementById("contacto").value.trim();
    const salario = document.getElementById("salario").value.trim();
    const descripcion = document.getElementById("descripcion").value.trim();

    if (!titulo || !empresa || !contacto) { alert("Completa título, empresa y contacto."); return; }

    const res = await crearOferta(titulo, empresa, contacto, salario, descripcion);
    const data = await res.json().catch(()=>({error:"No JSON"}));
    if (res.status === 201) {
      alert("Oferta creada correctamente");
      document.getElementById("publicarForm").reset();
      listarOfertas();
    } else if (res.status === 401) {
      alert("No autorizado. Por favor inicia sesión.");
    } else {
      alert(data.error || "Error al crear oferta");
    }
  });

});
