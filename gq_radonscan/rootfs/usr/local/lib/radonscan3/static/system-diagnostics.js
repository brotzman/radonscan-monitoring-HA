(() => {
  'use strict';

  function create({$,tr,escapeHtml,fmtDate,api,toast}) {
    function statusLabel(status) { return tr(`self_test_status_${status||'unknown'}`); }

    function render(payload) {
      const badge=$('selfTestBadge'), summary=$('selfTestSummary'), list=$('selfTestItems');
      const status=payload?.status||'unknown';
      if(badge) {badge.className=`badge ${status==='ok'?'normal':status==='warning'?'warning':status==='error'?'danger':'neutral'}`;badge.textContent=statusLabel(status);}
      if(summary) summary.textContent=payload?.generated_at?`${tr('last_self_test')}: ${fmtDate(payload.generated_at)} · ${tr('version')} ${payload.version||'–'}`:tr('self_test_not_run');
      if(!list) return;
      const items=payload?.items||[];
      if(!items.length) {list.innerHTML=`<div class="empty">${escapeHtml(tr('self_test_not_run'))}</div>`;return;}
      list.innerHTML=items.map(item=>`<article class="self-test-item ${escapeHtml(item.status)}"><span class="self-test-icon" aria-hidden="true">${item.status==='ok'?'✓':item.status==='warning'?'!':'×'}</span><div><strong>${escapeHtml(tr(`self_test_${item.id}`))}</strong><small>${escapeHtml(item.detail||statusLabel(item.status))}</small></div><span class="badge ${item.status==='ok'?'normal':item.status==='warning'?'warning':'danger'}">${escapeHtml(statusLabel(item.status))}</span></article>`).join('');
    }

    async function run() {
      const button=$('runSelfTest');
      if(button) {button.disabled=true;button.textContent=tr('self_test_running');}
      const summary=$('selfTestSummary');
      if(summary) summary.textContent=tr('self_test_running');
      try {
        const result=await api('api/self-test',{method:'POST',body:{}});
        render(result);
        toast(result.status==='ok'?tr('self_test_complete'):tr('self_test_attention'),result.status==='error');
      } catch(error) {
        render({status:'error',items:[{id:'api',status:'error',detail:error?.message||String(error)}]});
        toast(error,true);
      } finally {
        if(button) {button.disabled=false;button.textContent=tr('run_self_test');}
      }
    }

    function bind() { $('runSelfTest')?.addEventListener('click',run); }
    function initialize() { render(null); }
    return {bind,initialize,render,run};
  }

  window.RMSystemDiagnostics={create};
})();
