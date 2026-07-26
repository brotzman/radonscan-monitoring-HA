(() => {
  'use strict';

  function create(context) {
    const {
      $, tr, fmtInteger, fmtDate, fmtBytes, escapeHtml, api, toast,
      setView, loadAll, loadStateFast, resetClientData,
    } = context;
    let dataSummary = null;

    function renderOperationResult(targetId, title, rows) {
      const target=$(targetId); if(!target)return;
      target.hidden=false;
      target.innerHTML=`<strong>${escapeHtml(title)}</strong><dl>${rows.filter(row=>row[1]!==undefined&&row[1]!==null&&row[1]!=='' ).map(([label,value])=>`<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(String(value))}</dd></div>`).join('')}</dl>`;
    }

    async function loadDataSummary() {
      try { dataSummary=await api('api/data/summary'); renderDataSummary(); }
      catch(err) { toast(err.message,true); }
    }

    function renderDataSummary() {
      if(!dataSummary)return;
      $('dataMeasurements').textContent=fmtInteger(dataSummary.measurements);
      $('dataRange').textContent=`${fmtDate(dataSummary.first_measurement)} – ${fmtDate(dataSummary.last_measurement)}`;
      $('dataDbSize').textContent=fmtBytes(dataSummary.database_size_bytes);
      $('dataIntegrity').textContent=`${tr('integrity')}: ${dataSummary.integrity}`;
      $('dataFiles').textContent=fmtInteger(dataSummary.reports);
      $('dataFileSize').textContent=fmtBytes(Number(dataSummary.report_size_bytes||0));
      $('dataSchema').textContent=`v${dataSummary.schema_version}`;
    }

    async function deleteData(event) {
      event?.preventDefault();
      const input=$('deleteConfirmation');
      const confirmation=(input?.value||'').trim().toUpperCase().replace(/\s+/g,'');
      if(!['LÖSCHEN','LOESCHEN','DELETE','PURGE'].includes(confirmation)) {
        toast(tr('confirmation_delete_database_invalid'),true); input?.focus(); return;
      }
      if(!confirm(tr('confirm_delete_entire_database')))return;
      const button=$('deleteDatabaseNow'); if(button)button.disabled=true;
      try {
        const result=await api('api/data/reset',{method:'POST',body:{confirmed:true},confirmation});
        if(input)input.value='';
        dataSummary=null;
        resetClientData();
        renderOperationResult('deleteOperationResult',tr('database_delete_result'),[
          [tr('operation_id'),result.operation_id],[tr('deleted_records'),fmtInteger(result.deleted_total_records||0)],
          [tr('measurements'),fmtInteger(result.deleted_measurements||0)],[tr('removed_files'),fmtInteger(result.removed_files||0)],
          [tr('automatic_backup'),result.backup],[tr('integrity'),result.integrity],
          [tr('database_size'),`${fmtBytes(result.database_size_before||0)} → ${fmtBytes(result.database_size_after||0)}`],
          [tr('duration'),`${fmtInteger(result.duration_ms||result.server_duration_ms||0)} ms`]
        ]);
        setView('overview');
        await loadAll();
        toast(`${tr('database_deleted')}: ${fmtInteger(result.deleted_measurements||0)} ${tr('measurements')}`);
      } catch(err) { toast(err.message,true); }
      finally { if(button)button.disabled=false; }
    }

    async function loadAudit() {
      try {
        const payload=await api('api/audit?limit=200');
        const body=$('auditBody'),items=payload.items||[];
        if(!body)return;
        body.innerHTML=items.length?items.map(item=>`<tr><td>${fmtDate(item.created_at)}</td><td>${escapeHtml(item.action)}</td><td>${escapeHtml(item.target||'–')}</td><td>${escapeHtml(item.user_name||'–')}</td><td><code>${escapeHtml(JSON.stringify(item.details||{}))}</code></td></tr>`).join(''):`<tr><td colspan="5" class="empty-cell">${tr('no_data')}</td></tr>`;
      } catch(err) { toast(err.message,true); }
    }

    async function purgeHa(event) {
      event?.preventDefault();
      const input=$('haConfirmation');
      const confirmation=(input?.value||'').trim().toUpperCase().replace(/\s+/g,'');
      if(!['PURGE','LÖSCHEN','LOESCHEN','DELETE'].includes(confirmation)) {
        toast(tr('confirmation_invalid'),true); input?.focus(); return;
      }
      const button=$('purgeHaHistory'), verifyButton=$('verifyHaPurge'), status=$('haStatus');
      if(button)button.disabled=true;
      if(verifyButton)verifyButton.disabled=true;
      if(status)status.textContent=tr('ha_purge_running');
      try {
        const result=await api('api/homeassistant/purge-all',{method:'POST',body:{confirmed:true,confirmation},confirmation});
        if(input)input.value='';
        if(status)status.textContent=tr('ha_purge_started');
        renderOperationResult('haOperationResult',tr('ha_purge_result'),[
          [tr('operation_id'),result.operation_id],[tr('detected_entities'),fmtInteger(result.detected_entities||0)],
          [tr('submitted_patterns'),fmtInteger(result.submitted_globs||0)],[tr('authentication'),result.authentication],
          [tr('keep_days'),fmtInteger(result.keep_days||0)],[tr('duration'),`${fmtInteger(result.server_duration_ms||0)} ms`],
          [tr('verification'),tr('verification_pending')],[tr('status'),tr('ha_purge_async_note')]
        ]);
        setView('overview');
        await loadStateFast();
        const total=(result.entity_ids?.length||0)+(result.entity_globs?.length||0);
        toast(`${tr('purge_requested')}: ${fmtInteger(total)} ${tr('purge_targets')}`);
      } catch(err) {
        if(status)status.textContent=err.message;
        toast(err.message,true);
      } finally {
        if(button)button.disabled=false;
        if(verifyButton)verifyButton.disabled=false;
      }
    }

    async function verifyHaPurge(event) {
      event?.preventDefault();
      const button=$('verifyHaPurge'), status=$('haStatus');
      if(button)button.disabled=true;
      if(status)status.textContent=tr('ha_purge_verifying');
      try {
        const result=await api('api/homeassistant/verify-purge',{method:'POST',body:{confirmed:true}});
        const complete=Boolean(result.verified);
        if(status)status.textContent=complete?tr('ha_purge_verified'):tr('ha_purge_history_remaining');
        renderOperationResult('haOperationResult',tr('ha_purge_verification_result'),[
          [tr('operation_id'),result.operation_id],[tr('verification'),complete?tr('verified'):tr('pending')],
          [tr('checked_entities'),fmtInteger(result.checked_entities||0)],[tr('remaining_history_rows'),fmtInteger(result.remaining_rows||0)],
          [tr('checked_at'),fmtDate(result.checked_at)],[tr('verification_period'),`${fmtDate(result.period_start)} – ${fmtDate(result.period_end)}`],
          [tr('limitation'),result.limitation]
        ]);
        toast(complete?tr('ha_purge_verified'):tr('ha_purge_history_remaining'),!complete);
      } catch(err) {
        if(status)status.textContent=err.message;
        toast(err.message,true);
      } finally { if(button)button.disabled=false; }
    }

    return {loadDataSummary, deleteData, loadAudit, purgeHa, verifyHaPurge, renderOperationResult};
  }

  window.RMDataManagement={create};
})();
