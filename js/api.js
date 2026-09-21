/* =====================================================================
   Uong Bi GO - API helper (PHIEN BAN FRONTEND-ONLY / MOCK)
   -----------------------------------------------------------------------
   File nay thay the hoan toan cho backend that. Khong co request mang nao
   duoc goi di ca - moi "API" (dang nhap, thuc don, gio hang, don hang,
   thanh toan QR, KDS, quan tri...) deu duoc gia lap va luu trong
   localStorage cua trinh duyet, dong vai tro nhu mot co so du lieu nho.
   Tat ca cac trang HTML/JS khac (index.html, menu.html, cart.html,
   orders.html, kds.html, admin/*.html, js/cart.js) khong can sua doi gi
   vi chung chi goi qua cac ham dung chung: Auth, apiFetch, goTo,
   formatCurrency, formatDateTime, statusPillHtml... y het ban goc.
   ===================================================================== */

/* ---------- "Dia chi API" chi con mang tinh trang tri, khong con dung ---------- */
const API_BASE = "(mock-local)";

/* ---------- Duong dan goc cua site (hoat dong ca khi host trong thu muc con) ---------- */
const SITE_ROOT = new URL("../", document.currentScript.src).href;
function goTo(page) {
  window.location.href = SITE_ROOT + String(page).replace(/^\/+/, "");
}

/* ===================== Auth (luu phien dang nhap trong localStorage) ===================== */
const Auth = {
  getToken() {
    try { return localStorage.getItem("ubg_token"); } catch (e) { return null; }
  },
  getUser() {
    try { return JSON.parse(localStorage.getItem("ubg_user") || "null"); } catch (e) { return null; }
  },
  setSession(token, user) {
    try {
      localStorage.setItem("ubg_token", token);
      localStorage.setItem("ubg_user", JSON.stringify(user));
    } catch (e) { /* trinh duyet chan luu tru - bo qua */ }
  },
  clear() {
    try {
      localStorage.removeItem("ubg_token");
      localStorage.removeItem("ubg_user");
    } catch (e) { /* noop */ }
  },
  isLoggedIn() { return !!this.getToken(); },
  requireRole(allowedRoles) {
    const user = this.getUser();
    if (!this.isLoggedIn() || !user) {
      goTo("index.html");
      return null;
    }
    if (allowedRoles && !allowedRoles.includes(user.vaiTro)) {
      alert("Tai khoan cua ban khong co quyen truy cap trang nay.");
      redirectByRole(user.vaiTro);
      return null;
    }
    return user;
  },
};

function redirectByRole(vaiTro) {
  const map = { ROLE_BUYER: "menu.html", ROLE_STAFF: "kds.html", ROLE_ADMIN: "admin/dashboard.html" };
  goTo(map[vaiTro] || "index.html");
}

/* ===================== API ONLINE (VERCEL) ===================== */
const API_BASE = "/api";
window.__UBG_API_SCRIPT_URL = document.currentScript ? document.currentScript.src : location.href;

const Auth = {
  getToken() { try { return localStorage.getItem("ubg_token"); } catch(e) { return null; } },
  getUser() { try { return JSON.parse(localStorage.getItem("ubg_user") || "null"); } catch(e) { return null; } },
  setSession(token, user) { localStorage.setItem("ubg_token", token); localStorage.setItem("ubg_user", JSON.stringify(user)); },
  clear() { localStorage.removeItem("ubg_token"); localStorage.removeItem("ubg_user"); },
  isLoggedIn() { return !!this.getToken(); },
  requireRole(allowedRoles) {
    const user=this.getUser();
    if(!this.isLoggedIn() || !user){ goTo("index.html"); return null; }
    if(allowedRoles && !allowedRoles.includes(user.vaiTro)){ alert("Tai khoan cua ban khong co quyen truy cap trang nay."); redirectByRole(user.vaiTro); return null; }
    return user;
  }
};
function redirectByRole(vaiTro){ const map={ROLE_BUYER:"menu.html",ROLE_STAFF:"kds.html",ROLE_ADMIN:"admin/dashboard.html"}; goTo(map[vaiTro]||"index.html"); }

function makeFakeQrDataUri(seedText) {
  let hash=0; for(let i=0;i<seedText.length;i++) hash=(hash*31+seedText.charCodeAt(i))>>>0;
  function rand(){hash=(hash*1103515245+12345)>>>0;return(hash>>>8)/16777216;}
  const cells=21, cellSize=8, size=cells*cellSize; let rects="";
  for(let y=0;y<cells;y++)for(let x=0;x<cells;x++){const a=x<7&&y<7,b=x>=cells-7&&y<7,c=x<7&&y>=cells-7;if(a||b||c)continue;if(rand()>.55)rects+=`<rect x="${x*cellSize}" y="${y*cellSize}" width="${cellSize}" height="${cellSize}" fill="#111"/>`;}
  function finder(ox,oy){return `<rect x="${ox}" y="${oy}" width="${7*cellSize}" height="${7*cellSize}" fill="#111"/><rect x="${ox+cellSize}" y="${oy+cellSize}" width="${5*cellSize}" height="${5*cellSize}" fill="#fff"/><rect x="${ox+2*cellSize}" y="${oy+2*cellSize}" width="${3*cellSize}" height="${3*cellSize}" fill="#111"/>`;}
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" width="240" height="240"><rect width="${size}" height="${size}" fill="#fff"/>${rects}${finder(0,0)+finder((cells-7)*cellSize,0)+finder(0,(cells-7)*cellSize)}</svg>`;
  return "data:image/svg+xml;utf8,"+encodeURIComponent(svg);
}

async function apiFetch(path, options={}) {
  const [rawPath,queryStr]=path.split("?");
  const qs=new URLSearchParams({path:rawPath});
  if(queryStr)new URLSearchParams(queryStr).forEach((v,k)=>qs.set(k,v));
  const headers={"Content-Type":"application/json"}; const token=Auth.getToken(); if(token)headers["X-UBG-Token"]=token;
  let response;
  try { response=await fetch(API_BASE+"?"+qs.toString(),{method:(options.method||"GET").toUpperCase(),headers,body:options.body?(typeof options.body==="string"?options.body:JSON.stringify(options.body)):undefined}); }
  catch(e){throw {status:0,message:"Khong ket noi duoc server Vercel."};}
  let data={}; try{data=await response.json();}catch(e){}
  if(!response.ok)throw {status:response.status,message:data.message||"Server tra ve loi."};
  if(rawPath.startsWith("/thanhtoan/")&&data&&!data.qrImageBase64&&data.maQr)data.qrImageBase64=makeFakeQrDataUri(data.maQr);
  return data;
}

/* ===================== Tien ich dung chung (giu nguyen nhu ban goc) ===================== */
function formatCurrency(value) {
  return new Intl.NumberFormat("vi-VN").format(Math.round(value)) + "đ";
}

function formatDateTime(isoString) {
  try {
    const d = new Date(isoString);
    return d.toLocaleString("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit", year: "numeric" });
  } catch (e) { return isoString; }
}

const STATUS_LABEL = {
  CHO_THANH_TOAN: "Cho thanh toan",
  DA_THANH_TOAN: "Da thanh toan",
  DANG_CHUAN_BI: "Dang chuan bi",
  SAN_SANG_NHAN: "San sang nhan",
  HOAN_THANH: "Hoan thanh",
  DA_HUY: "Da huy",
};

function statusPillHtml(trangThai) {
  const label = STATUS_LABEL[trangThai] || trangThai;
  return `<span class="status-pill status-${trangThai}">${label}</span>`;
}

/* ---------- Banner mat mang (van dung navigator.onLine that cua trinh duyet) ---------- */
function initOfflineBanner() {
  const banner = document.createElement("div");
  banner.className = "offline-banner hidden";
  banner.innerHTML = '<span class="dot"></span><span>Mat ket noi mang - dang cho ket noi lai de dong bo...</span>';
  document.body.appendChild(banner);

  function updateStatus() {
    if (navigator.onLine) {
      banner.classList.add("hidden");
    } else {
      banner.classList.remove("hidden");
    }
  }
  window.addEventListener("online", () => {
    updateStatus();
    window.dispatchEvent(new CustomEvent("ubg:reconnected"));
  });
  window.addEventListener("offline", updateStatus);
  updateStatus();
}

document.addEventListener("DOMContentLoaded", initOfflineBanner);
