(() => {
  'use strict';
  const boot = window.RADONSCAN_BOOT || {};
  const translations = boot.translations || {};
  const byId = id => document.getElementById(id);
  const all = selector => Array.from(document.querySelectorAll(selector));
  const tr = key => translations[key] || key;
  const locale = () => boot.locale || 'en';
  const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const fmtNumber = (value, digits=1) => value === null || value === undefined || Number.isNaN(Number(value)) ? '–' : Number(value).toLocaleString(locale(), {minimumFractionDigits:digits, maximumFractionDigits:digits});
  const fmtInteger = value => value === null || value === undefined ? '–' : Number(value).toLocaleString(locale(), {maximumFractionDigits:0});
  const fmtDate = value => value ? new Date(value).toLocaleString(locale(), {dateStyle:'medium',timeStyle:'short'}) : '–';
  const fmtDateOnly = value => value ? new Date(value).toLocaleDateString(locale(), {dateStyle:'medium'}) : '–';
  const fmtFirmware = value => value ? String(value).replace(/RadonScan(?=Re\d)/g, 'RadonScan ') : '–';
  const fmtBytes = value => {
    const n=Number(value||0); if(n<1024) return `${n} B`; const units=['KB','MB','GB','TB']; let v=n/1024,i=0; while(v>=1024&&i<units.length-1){v/=1024;i++;} return `${fmtNumber(v,v>=10?1:2)} ${units[i]}`;
  };
  const toIso = value => value ? new Date(value).toISOString() : null;
  const toInput = value => {
    if(!value) return '';
    const date=new Date(value); const local=new Date(date.getTime()-date.getTimezoneOffset()*60000); return local.toISOString().slice(0,16);
  };
  const errorMessage = error => {
    if(error instanceof Error && error.message) return error.message;
    if(typeof error === 'string') return error;
    try { return JSON.stringify(error); } catch (_) { return tr('unknown_error'); }
  };
  const storageArea = kind => kind === 'session' ? window.sessionStorage : window.localStorage;
  const storageGet = (kind, key) => {
    try { return storageArea(kind).getItem(key); } catch (_) { return null; }
  };
  const storageSet = (kind, key, value) => {
    try { storageArea(kind).setItem(key, String(value)); return true; } catch (_) { return false; }
  };
  const storageRemove = (kind, key) => {
    try { storageArea(kind).removeItem(key); return true; } catch (_) { return false; }
  };
  async function api(path, options={}) {
    const opts={cache:'no-store',...options,headers:{...(options.headers||{})}};
    if(opts.method && opts.method !== 'GET') opts.headers['X-Radon-Action']=boot.actionToken;
    if(options.confirmation) opts.headers['X-Radon-Confirmation']=options.confirmation;
    if(opts.body && !(opts.body instanceof FormData) && typeof opts.body !== 'string') {
      opts.headers['Content-Type']='application/json';
      opts.body=JSON.stringify(opts.body);
    }
    const response=await fetch(path,opts);
    const type=response.headers.get('content-type')||'';
    const payload=type.includes('application/json') ? await response.json() : await response.text();
    if(!response.ok) throw new Error(payload?.error || payload || `HTTP ${response.status}`);
    return payload;
  }
  function toast(message, error=false) {
    const el=byId('toast');
    if(!el) return;
    el.textContent=errorMessage(message);
    el.className=`toast show${error?' error':''}`;
    clearTimeout(toast.timer);
    toast.timer=setTimeout(()=>{ if(el) el.className='toast'; },3500);
  }
  window.RMCore={boot,translations,byId,all,tr,locale,escapeHtml,fmtNumber,fmtInteger,fmtDate,fmtDateOnly,fmtFirmware,fmtBytes,toIso,toInput,errorMessage,storageGet,storageSet,storageRemove,api,toast};
})();
