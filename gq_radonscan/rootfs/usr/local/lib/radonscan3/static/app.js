(() => {
  'use strict';
  const {boot,translations:t,byId:$,all:$$,tr,locale,escapeHtml,fmtNumber,fmtInteger,fmtDate,fmtDateOnly,fmtFirmware,fmtBytes,toIso,toInput,storageGet,storageSet,api,toast} = window.RMCore;
  let state = null;
  let records = [];
  let catalog = {locations:[],sessions:[],campaigns:[],devices:[],events:[],reports:[]};
  let analysisData = null;
  let dataManagement = null;
  let chartDays = 7;
  let catalogInitialised = false;
  let loadInProgress = false;
  let initialLoadComplete = false;

  const unit = () => state?.settings?.preferred_unit === 'pCi/L' ? 'pCi/L' : 'Bq/m³';
  const radonValue = bq => unit()==='pCi/L' ? Number(bq)/37 : Number(bq);
  const radon = bq => bq === null || bq === undefined ? '–' : `${fmtNumber(radonValue(bq), unit()==='pCi/L'?3:1)} ${unit()}`;
  const bool = value => value ? tr('yes') : tr('no');
  const statusText = value => tr(value || 'unknown');

  function applyTranslations() {
    $$('[data-i18n]').forEach(el=>{const key=el.dataset.i18n;if(t[key]) el.textContent=t[key];});
    $$('[data-i18n-title]').forEach(el=>{const key=el.dataset.i18nTitle;if(t[key]) el.title=t[key];});
    $$('[data-i18n-placeholder]').forEach(el=>{const key=el.dataset.i18nPlaceholder;if(t[key]) el.placeholder=t[key];});
    $$('[data-i18n-aria-label]').forEach(el=>{const key=el.dataset.i18nAriaLabel;if(t[key]) el.setAttribute('aria-label',t[key]);});
    const select=$('languageSelect');
    select.innerHTML=Object.entries(boot.locales||{}).map(([code,name])=>`<option value="${code}" ${code===boot.locale?'selected':''}>${escapeHtml(name)}</option>`).join('');
  }

  function setSidebar(open) {
    const sidebar=$('sidebar'), backdrop=$('sidebarBackdrop'), button=$('menuButton');
    sidebar.classList.toggle('open',Boolean(open));
    backdrop.classList.toggle('visible',Boolean(open));
    button.setAttribute('aria-expanded',open?'true':'false');
    document.body.classList.toggle('menu-open',Boolean(open));
  }

  function closeSidebar() { setSidebar(false); }

  function dataManagementEnabled() { return state?.settings?.data_management_enabled !== false; }

  function applyFeatureVisibility() {
    const enabled=dataManagementEnabled();
    const nav=$('dataManagementNav'); if(nav) nav.hidden=!enabled;
    const view=$('view-data'); if(view) view.hidden=!enabled;
    if(!enabled && (location.hash==='#data' || storageGet('local','radonMonitoringView')==='data')) {
      storageSet('local','radonMonitoringView','overview');
      if(location.hash==='#data') history.replaceState(null,'','#overview');
    }
  }

  function setView(name) {
    if(name==='data' && !dataManagementEnabled()) name='overview';
    $$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
    $$('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${name}`));
    history.replaceState(null,'',`#${name}`);
    storageSet('local','radonMonitoringView',name);
    closeSidebar();
    if(name==='analysis'&&!analysisData) loadAnalysis();
    if(name==='data') {dataManagement?.loadDataSummary();dataManagement?.loadAudit();}
    if(name==='map') loadGmcmap();
  }

  function setConnection(connected) {
    connected=Boolean(connected);
    const pill=$('connectionPill');
    if(pill) {
      pill.className=`status-pill ${connected?'ok':'error'}`;
      const label=pill.querySelector('span:last-child');
      if(label) label.textContent=connected?tr('connected'):tr('disconnected');
    }
    const sidebar=$('sidebar');
    if(sidebar) {
      sidebar.classList.toggle('connected',connected);
      sidebar.classList.toggle('disconnected',!connected);
      const footer=sidebar.querySelector('.sidebar-footer');
      if(footer) footer.className=`sidebar-footer ${connected?'ok':'error'}`;
    }
    const sidebarConnection=$('sidebarConnection');
    if(sidebarConnection) sidebarConnection.textContent=connected?tr('connected'):tr('disconnected');
  }

  function periodReason(period) {
    if(period.reason==='no_data') return tr('no_data');
    if(period.reason==='period_not_reached') return `${tr('period_not_complete')} ${period.samples||0}/${period.required_samples||0} ${tr('hours_short')}`;
    if(period.reason==='coverage_too_low') return `${tr('coverage_too_low')}: ${fmtNumber(period.coverage_percent,0)} %`;
    return tr('not_yet_calculable');
  }

  function renderAverage(cardId,valueId,coverageId,key) {
    const p=state.statistics?.[key]||{}; const card=$(cardId);
    card.classList.toggle('unavailable',!p.available);
    if(p.available) {
      $(valueId).textContent=radon(p.mean_bq_m3);
      $(coverageId).textContent=`${tr('coverage')}: ${fmtNumber(p.coverage_percent,0)} % · ${p.samples||0}/${p.required_samples||p.samples||0}`;
    } else {
      $(valueId).textContent=tr('not_yet_calculable');
      $(coverageId).textContent=periodReason(p);
    }
  }

  function renderState() {
    if(!state) return;
    applyFeatureVisibility();
    const connected=!!state.connection?.connected; setConnection(connected);
    const m=state.measurement||{};
    $('currentValue').textContent=m.available?fmtNumber(unit()==='pCi/L'?m.pci_l:m.bq_m3,unit()==='pCi/L'?3:1):'–';
    $('currentUnit').textContent=unit(); $('currentTime').textContent=fmtDate(m.completed_at);
    $('currentAge').textContent=m.age_hours===null||m.age_hours===undefined?'':`${tr('data_age')}: ${fmtNumber(m.age_hours,1)} h`;
    $('currentRaw').textContent=m.raw_cph??'–'; $('sampleCount').textContent=fmtInteger(state.database?.sample_count||0);
    $('currentLocation').textContent=m.location_name||tr('not_assigned');
    const badge=$('currentStatus'); badge.className=`badge ${m.status||'neutral'}`; badge.textContent=statusText(m.status);
    renderAverage('metric24','avg24','coverage24','24h');
    renderAverage('metric7d','avg7d','coverage7d','7d');
    renderAverage('metric30d','avg30d','coverage30d','30d');
    const all=state.statistics?.all||{};
    $('avgAll').textContent=all.available?radon(all.mean_bq_m3):tr('not_yet_calculable');
    $('rangeAll').textContent=all.available?`${tr('minimum')}: ${radon(all.minimum_bq_m3)} · ${tr('maximum')}: ${radon(all.maximum_bq_m3)}`:tr('no_data');
    $('overviewDeviceStatus').textContent=connected?tr('connected'):tr('disconnected');
    $('overviewMqttStatus').textContent=state.mqtt?.connected?tr('online'):tr('offline');
    $('overviewLastUpdate').textContent=fmtDate(m.completed_at);
    $('overviewDatabaseStatus').textContent=`${fmtInteger(state.database?.sample_count||0)} ${tr('hours_short')} · ${fmtBytes(state.database?.size_bytes||0)}`;
    const q=state.statistics?.['30d']?.quality||state.statistics?.all?.quality||'insufficient';
    const qBadge=$('qualityBadge');qBadge.className=`badge ${q}`;qBadge.textContent=tr(`quality_${q}`);
    $('overviewCoverage').textContent=`${fmtNumber(state.statistics?.['30d']?.coverage_percent||0,0)} %`;
    renderFacts(); renderSettings(); renderExpert(); renderOverviewChart();
    $('manualLink').href=`docs/user-manual.pdf?lang=${boot.locale}`; $('protocolLink').href=`docs/protocol-reference.pdf?lang=${boot.locale}`;
  }

  const fact = (label,value) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value??tr('not_available'))}</dd></div>`;
  function renderFacts() {
    const d=state.device||{},p=state.protocol||{},c=state.connection||{};
    $('deviceFacts').innerHTML=[fact(tr('status'),c.connected?tr('connected'):tr('disconnected')),fact(tr('model'),d.model),fact(tr('firmware'),fmtFirmware(d.firmware)),fact(tr('serial_number'),d.serial_number),fact(tr('serial_port'),d.serial_port),fact(tr('last_scan'),fmtDate(c.last_scan))].join('');
    $('protocolFacts').innerHTML=[fact(tr('protocol'),p.transport||'GET/SPIR'),fact(tr('decoder'),p.decoder),fact(tr('detected_records'),p.hourly_record_count),fact(tr('latest_raw'),p.latest_raw_cph),fact(tr('hour_index'),p.latest_hour_index),fact(tr('conversion_factor'),`${state.settings.factor_bq_m3_per_cph} ${tr('factor_unit')}`)].join('');
    $('serviceFacts').innerHTML=[fact(tr('mqtt'),state.mqtt?.connected?tr('online'):tr('offline')),fact(tr('home_assistant'),state.homeassistant?.connected?tr('online'):tr('offline')),fact(tr('api'),tr('online')),fact(tr('version'),state.app?.version)].join('');
    $('databaseFacts').innerHTML=[fact(tr('sample_count'),fmtInteger(state.database?.sample_count)),fact(tr('database_size'),fmtBytes(state.database?.size_bytes)),fact(tr('schema'),state.database?.schema_version),fact(tr('integrity'),state.database?.integrity),fact(tr('start'),fmtDate(state.database?.first_measurement)),fact(tr('end'),fmtDate(state.database?.last_measurement))].join('');
  }

  function renderSettings() {
    const s=state.settings||{};
    const groups=[
      [tr('settings_group_device'),[[tr('scan_interval'),`${s.scan_interval} ${tr('seconds')}`],[tr('preferred_unit'),s.preferred_unit],[tr('language'),s.language==='auto'?tr('automatic'):s.language],[tr('conversion_factor'),`${s.factor_bq_m3_per_cph} ${tr('factor_unit')}`],[tr('serial_port'),s.serial_port]]],
      [tr('settings_group_statistics'),[[tr('warning_threshold'),`${s.warning_threshold_bq_m3} Bq/m³`],[tr('danger_threshold'),`${s.danger_threshold_bq_m3} Bq/m³`],[tr('minimum_coverage'),`${s.minimum_data_coverage_percent} %`],[tr('backfill'),bool(s.backfill_history)],[tr('retention'),`${s.history_retention_days} ${tr('days')}`]]],
      [tr('settings_group_worldmap'),[[tr('gmcmap_enabled'),bool(s.gmcmap_enabled)],[tr('gmcmap_auto_upload'),bool(s.gmcmap_auto_upload)],[tr('gmcmap_upload_interval_minutes'),`${s.gmcmap_upload_interval_minutes||'–'} min`],[tr('gmcmap_account_id'),s.gmcmap_account_id_masked||tr('not_set')],[tr('gmcmap_device_id'),s.gmcmap_device_id_masked||tr('not_set')]]],
      [tr('settings_group_reports'),[[tr('report_author'),s.report_author||tr('not_set')],[tr('report_organisation'),s.report_organisation||tr('not_set')]]],
      [tr('settings_group_data'),[[tr('data_management'),bool(s.data_management_enabled)],[tr('admin_token_status'),s.homeassistant_access_token_configured?tr('configured_securely'):tr('not_configured')]]],
      [tr('settings_group_diagnostics'),[[tr('diagnostic_logging'),bool(s.diagnostic_logging)],[tr('analysis_timezone'),s.analysis_timezone||tr('automatic')]]]
    ];
    $('settingsGrid').innerHTML=groups.map(([title,rows],index)=>`<section class="settings-group panel" aria-labelledby="settings-group-${index}"><div class="settings-group-heading"><h3 id="settings-group-${index}">${escapeHtml(title)}</h3>${title===tr('settings_group_data')?`<p>${escapeHtml(tr('security_note'))}</p>`:''}</div><div class="settings-grid">${rows.map(([a,b])=>`<div class="setting-row"><span>${escapeHtml(a)}</span><strong>${escapeHtml(b??tr('not_available'))}</strong></div>`).join('')}</div></section>`).join('');
  }

  function renderExpert() {
    const d=state.device||{},p=state.protocol||{},m=state.measurement||{};
    $('expertDeviceFacts').innerHTML=[fact(tr('model'),d.model),fact(tr('firmware'),fmtFirmware(d.firmware)),fact(tr('serial_number'),d.serial_number),fact(tr('serial_port'),d.serial_port),fact(tr('first_seen'),fmtDate(d.first_seen)),fact(tr('last_seen'),fmtDate(d.last_seen))].join('');
    $('expertProtocolFacts').innerHTML=[fact(tr('decoder'),p.decoder),fact(tr('protocol'),p.transport),fact(tr('raw_start_offset'),p.raw_start_offset),fact(tr('raw_end_offset'),p.raw_end_offset),fact('FD 0x270',p.fd_value_0x270),fact(tr('time_records'),p.time_record_count),fact(tr('hourly_records'),p.hourly_record_count)].join('');
    $('expertDataFacts').innerHTML=[fact(tr('hour_index'),m.hour_index),fact(tr('raw_cph'),m.raw_cph),fact(tr('conversion_factor'),m.factor_bq_m3_per_cph),fact(tr('source'),m.source),fact(tr('campaign'),p.imported?.latest_hour_index??'–'),fact(tr('database_integrity'),state.database?.integrity),fact(tr('data_age'),m.age_hours===null?'–':`${fmtNumber(m.age_hours,2)} h`)].join('');
  }

  function renderOverviewChart() {
    let rows=[...records].sort((a,b)=>new Date(a.completed_at)-new Date(b.completed_at));
    if(rows.length&&chartDays>0){const end=new Date(rows[rows.length-1].completed_at).getTime();const cutoff=end-chartDays*86400000;rows=rows.filter(r=>new Date(r.completed_at).getTime()>=cutoff);}
    $('chartSubtitle').textContent=`${rows.length} ${tr('samples')} · ${rows.length?`${fmtDate(rows[0].completed_at)} – ${fmtDate(rows[rows.length-1].completed_at)}`:'–'}`;
    renderLineChart($('chart'),rows,{moving:false});
  }

  function splitSegments(rows) {
    const segments=[];let current=[];let previous=null;
    rows.forEach(row=>{const time=new Date(row.completed_at).getTime();if(previous!==null&&time-previous>90*60000){if(current.length)segments.push(current);current=[];}current.push(row);previous=time;});if(current.length)segments.push(current);return segments;
  }

  function movingAverage(rows,window=24) {
    const out=[];let sum=0;const queue=[];rows.forEach(row=>{const value=Number(row.chart_value ?? radonValue(row.bq_m3));queue.push(value);sum+=value;if(queue.length>window)sum-=queue.shift();out.push(queue.length>=Math.min(window,rows.length)?sum/queue.length:null);});return out;
  }

  function renderLineChart(element,rows,options={}) {
    if(!element) return;
    if(rows.length<2){element.innerHTML=`<div class="empty">${tr('chart_empty')}</div>`;return;}
    const width=1000,height=300,padL=55,padR=18,padT=20,padB=38;
    const chartRows=rows.map(r=>({...r,chart_value:radonValue(r.bq_m3)}));
    const times=chartRows.map(r=>new Date(r.completed_at).getTime()), values=chartRows.map(r=>Number(r.chart_value));
    const minT=Math.min(...times),maxT=Math.max(...times),warning=radonValue(Number(state?.settings?.warning_threshold_bq_m3||100)),danger=radonValue(Number(state?.settings?.danger_threshold_bq_m3||300));
    const maxV=Math.max(5,Math.max(...values)*1.15,warning*1.05,Math.min(danger*1.03,Math.max(...values)*1.5||danger));
    const plotW=width-padL-padR,plotH=height-padT-padB;
    const x=t=>padL+plotW*((t-minT)/Math.max(1,maxT-minT));const y=v=>padT+plotH*(1-v/maxV);
    const grids=[0,.25,.5,.75,1].map(f=>{const yy=padT+plotH*f,val=maxV*(1-f);return `<line class="grid" x1="${padL}" y1="${yy}" x2="${width-padR}" y2="${yy}"/><text x="5" y="${yy+4}">${fmtNumber(val,0)}</text>`;}).join('');
    const thresholds=[[warning,'threshold-warning'],[danger,'threshold-danger']].filter(([v])=>v<=maxV).map(([v,c])=>`<line class="${c}" x1="${padL}" y1="${y(v)}" x2="${width-padR}" y2="${y(v)}"/>`).join('');
    const segmentSvg=splitSegments(chartRows).map(segment=>{const points=segment.map(r=>`${x(new Date(r.completed_at).getTime()).toFixed(1)},${y(Number(r.chart_value)).toFixed(1)}`).join(' ');return `<polyline class="line" points="${points}"/>`;}).join('');
    let moving='';if(options.moving){const avgs=movingAverage(chartRows,Math.min(24,chartRows.length));const points=chartRows.map((r,i)=>avgs[i]===null?null:`${x(times[i]).toFixed(1)},${y(avgs[i]).toFixed(1)}`).filter(Boolean).join(' ');moving=`<polyline class="moving-line" points="${points}"/>`;}
    const circles=chartRows.length<=180?chartRows.map((r,i)=>`<circle class="point" cx="${x(times[i])}" cy="${y(values[i])}" r="2.8"><title>${escapeHtml(fmtDate(r.completed_at))}: ${escapeHtml(radon(r.bq_m3))}</title></circle>`).join(''):'';
    const start=fmtDateOnly(rows[0].completed_at),end=fmtDateOnly(rows[rows.length-1].completed_at);
    element.innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img"><defs><linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f47b20" stop-opacity=".22"/><stop offset="1" stop-color="#f47b20" stop-opacity="0"/></linearGradient></defs>${grids}${thresholds}${segmentSvg}${moving}${circles}<text x="${padL}" y="${height-8}">${escapeHtml(start)}</text><text x="${width-padR}" y="${height-8}" text-anchor="end">${escapeHtml(end)}</text></svg>`;
  }

  function renderHistogram(element,histogram) {
    if(!histogram?.length){element.innerHTML=`<div class="empty">${tr('chart_empty')}</div>`;return;}
    const width=600,height=260,padL=45,padR=15,padT=15,padB=42,max=Math.max(...histogram.map(x=>Number(x.count)),1),barW=(width-padL-padR)/histogram.length;
    const bars=histogram.map((item,i)=>{const h=(height-padT-padB)*Number(item.count)/max;const x=padL+i*barW+2,y=height-padB-h;const from=radonValue(item.from),to=radonValue(item.to);return `<rect class="bar" x="${x}" y="${y}" width="${Math.max(1,barW-4)}" height="${h}"><title>${fmtNumber(from,unit()==='pCi/L'?2:1)}–${fmtNumber(to,unit()==='pCi/L'?2:1)}: ${item.count}</title></rect>${i%Math.max(1,Math.ceil(histogram.length/6))===0?`<text x="${x}" y="${height-18}">${fmtNumber(from,unit()==='pCi/L'?1:0)}</text>`:''}`;}).join('');
    const grids=[0,.5,1].map(f=>{const y=padT+(height-padT-padB)*f;return `<line class="grid" x1="${padL}" y1="${y}" x2="${width-padR}" y2="${y}"/><text x="3" y="${y+4}">${fmtNumber(max*(1-f),0)}</text>`;}).join('');
    element.innerHTML=`<svg viewBox="0 0 ${width} ${height}">${grids}${bars}<text x="${width/2}" y="${height-3}" text-anchor="middle">${unit()}</text></svg>`;
  }

  function analysisQuery() {
    const value=id=>$(id)?.value||'';const preset=value('analysisPreset')||'30d';const params=new URLSearchParams();
    if(preset!=='custom') params.set('days',preset);
    if(preset==='custom') {const start=toIso(value('analysisStart')),end=toIso(value('analysisEnd'));if(start)params.set('start',start);if(end)params.set('end',end);}
    if(value('analysisDevice'))params.set('device_id',value('analysisDevice'));if(value('analysisLocation'))params.set('location_id',value('analysisLocation'));if(value('analysisCampaign'))params.set('campaign_id',value('analysisCampaign'));
    return params;
  }

  async function loadAnalysis() {
    $('analysisApply').disabled=true;
    try {analysisData=await api(`api/analysis?${analysisQuery()}`);renderAnalysis();}
    catch(err){toast(err.message,true);} finally {$('analysisApply').disabled=false;}
  }

  function renderAnalysis() {
    if(!analysisData)return;const s=analysisData.statistics||{},thresholds=analysisData.thresholds||{};
    $('analysisMean').textContent=radon(s.mean_bq_m3);$('analysisCoverage').textContent=`${tr('coverage')}: ${fmtNumber(s.coverage_percent,1)} %`;
    $('analysisMedian').textContent=radon(s.median_bq_m3);$('analysisSamples').textContent=`${fmtInteger(s.samples)} / ${fmtInteger(s.expected_samples)} ${tr('samples')}`;
    $('analysisP95').textContent=radon(s.p95_bq_m3);$('analysisStddev').textContent=`σ ${radon(s.standard_deviation_bq_m3)}`;
    $('analysisTrend').textContent=s.slope_bq_m3_per_day===null?'–':`${fmtNumber(s.slope_bq_m3_per_day,2)} ${unit()}/${tr('day_short')}`;$('analysisR2').textContent=`R² ${fmtNumber(s.r_squared,2)}`;
    $('analysisWarning').textContent=`${fmtNumber(thresholds.warning?.percent||0,1)} %`;$('analysisWarningRun').textContent=`${tr('longest')}: ${fmtInteger(thresholds.warning?.longest_hours||0)} h`;
    $('analysisDanger').textContent=`${fmtNumber(thresholds.danger?.percent||0,1)} %`;$('analysisDangerRun').textContent=`${tr('longest')}: ${fmtInteger(thresholds.danger?.longest_hours||0)} h`;
    const u=analysisData.uncertainty||{},qc=analysisData.quality_control||{},cp=analysisData.change_point||{};
    $('analysisScienceClass').textContent=s.scientific_quality_class||'–';$('analysisQcStatus').textContent=tr(qc.status==='clean'?'quality_control_clean':'quality_control_review');
    const ess=analysisData.effective_sample_size||{},ci=analysisData.confidence_intervals?.mean||{},mk=analysisData.mann_kendall||{};
    $('analysisEffectiveN').textContent=ess.available?fmtNumber(ess.n_effective,1):'–';$('analysisCorrelation').textContent=ess.available?`${tr('from_observed')} ${fmtInteger(ess.n_observed)} · ${fmtInteger(ess.correlation_hours)} h` : tr('not_calculable');
    $('analysisMeanCi').textContent=ci.available?`${fmtNumber(radonValue(ci.lower),1)}–${fmtNumber(radonValue(ci.upper),1)} ${unit()}`:'–';
    $('analysisUncertainty').textContent=u.available?`± ${radonValue(u.expanded_uncertainty_95_bq_m3).toLocaleString(locale(),{maximumFractionDigits:0})} ${unit()}`:'–';$('analysisUncertaintyNote').textContent=u.available?tr('counting_uncertainty_95'):tr('uncertainty_unavailable');
    $('scientificFacts').innerHTML=[fact(tr('quality_class'),s.scientific_quality_class||'–'),fact(tr('qc_flags'),fmtInteger(qc.flagged_records||0)),fact(tr('autocorrelation_1h'),analysisData.autocorrelation?.[0]?fmtNumber(analysisData.autocorrelation[0].coefficient,2):'–'),fact(tr('candidate_change_point'),cp.available?fmtDate(cp.detected_at):tr('not_calculable')),fact(tr('change_amount'),cp.available?radon(cp.absolute_change_bq_m3):'–')].join('');
    $('scientificNotice').textContent=tr('scientific_notice');
    $('distributionFacts').innerHTML=[fact(tr('skewness'),s.skewness===null?'–':fmtNumber(s.skewness,2)),fact(tr('excess_kurtosis'),s.excess_kurtosis===null?'–':fmtNumber(s.excess_kurtosis,2)),fact(tr('mean_median_ratio'),s.mean_median_ratio===null?'–':fmtNumber(s.mean_median_ratio,2)),fact(tr('mann_kendall_tau'),mk.available?fmtNumber(mk.tau,2):'–'),fact(tr('p_value'),mk.available?fmtNumber(mk.p_value,3):'–'),fact(tr('sen_slope'),s.theil_sen_slope_bq_m3_per_day===null?'–':`${fmtNumber(s.theil_sen_slope_bq_m3_per_day,2)} ${unit()}/${tr('day_short')}`)].join('');
    const te=analysisData.threshold_events||{},we=te.warning||{},de=te.danger||{};
    $('thresholdEventFacts').innerHTML=[fact(tr('warning_events'),fmtInteger(we.event_count||0)),fact(tr('warning_excess_area'),`${fmtNumber(we.total_excess_area_bq_h_m3||0,1)} Bq·h/m³`),fact(tr('danger_events'),fmtInteger(de.event_count||0)),fact(tr('danger_excess_area'),`${fmtNumber(de.total_excess_area_bq_h_m3||0,1)} Bq·h/m³`)].join('');
    const sens=analysisData.sensitivity||{};
    $('sensitivityFacts').innerHTML=[fact(tr('mean'),radon(sens.mean_bq_m3)),fact(tr('median'),radon(sens.median_bq_m3)),fact(tr('trimmed_mean_10'),radon(sens.trimmed_mean_10_bq_m3)),fact(tr('mean_trimmed_difference'),sens.difference_mean_vs_trimmed_percent===null?'–':`${fmtNumber(sens.difference_mean_vs_trimmed_percent,1)} %`)].join('');
    const notice=$('analysisNotice');notice.className=`notice ${s.sufficient?'hidden':'warning'}`;notice.textContent=s.samples?`${tr('analysis_limited')}: ${fmtNumber(s.coverage_percent,1)} %`:tr('no_data');
    $('analysisPeriodLabel').textContent=`${fmtDate(s.period_start)} – ${fmtDate(s.period_end)}`;
    renderLineChart($('analysisChart'),analysisData.records||[],{moving:true});renderHistogram($('histogramChart'),analysisData.histogram||[]);renderHeatmap();renderProfiles();renderDaily();
    $('analysisQualityFacts').innerHTML=[fact(tr('quality'),tr(`quality_${s.quality}`)),fact(tr('expected_samples'),fmtInteger(s.expected_samples)),fact(tr('missing_samples'),fmtInteger(s.missing_samples)),fact(tr('longest_gap'),`${fmtNumber(s.longest_gap_hours,1)} h`),fact(tr('data_span'),`${fmtNumber(s.data_span_hours,1)} h`),fact(tr('exposure_index'),`${fmtNumber(s.exposure_index_bq_h_m3,1)} Bq·h/m³`),fact(tr('weekday_mean'),radon(s.weekday_mean_bq_m3)),fact(tr('weekend_mean'),radon(s.weekend_mean_bq_m3)),fact(tr('day_mean'),radon(s.day_mean_bq_m3)),fact(tr('night_mean'),radon(s.night_mean_bq_m3))].join('');
  }

  function renderHeatmap() {
    const heat=analysisData.weekly_heatmap||[];const names=locale()==='de'?['Mo','Di','Mi','Do','Fr','Sa','So']:['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];let html='<div class="heatmap-grid"><div></div>';
    for(let h=0;h<24;h++)html+=`<div class="heatmap-hour">${h%3===0?String(h).padStart(2,'0'):''}</div>`;
    const warning=Number(state.settings.warning_threshold_bq_m3),danger=Number(state.settings.danger_threshold_bq_m3);
    heat.forEach((row,d)=>{html+=`<div class="heatmap-label">${names[d]}</div>`;row.forEach(cell=>{const v=cell.mean_bq_m3;let cls='missing';if(v!==null&&v!==undefined){cls=v>=danger?'danger':v>=warning?'warning':v>=warning*.6?'medium':'low';}html+=`<div class="heatmap-cell ${cls}" title="${escapeHtml(names[d])} ${String(cell.hour).padStart(2,'0')}:00 · ${v===null||v===undefined?tr('not_available'):radon(v)} · n=${cell.samples}">${v===null||v===undefined?'':fmtNumber(radonValue(v),0)}</div>`;});});html+='</div>';$('weeklyHeatmap').innerHTML=html;
  }

  function renderProfiles() {
    const rows=analysisData.hourly_profile||[];const max=Math.max(...rows.map(r=>Number(r.mean_bq_m3||0)),1);$('profileBars').innerHTML=rows.map(r=>`<div class="profile-row"><span>${String(r.hour).padStart(2,'0')}:00</span><div class="profile-track"><div class="profile-fill" style="width:${Math.max(0,Number(r.mean_bq_m3||0)/max*100)}%"></div></div><span class="profile-value">${r.mean_bq_m3===null?'–':fmtNumber(radonValue(r.mean_bq_m3),0)}</span></div>`).join('');
  }

  function renderDaily() {
    const body=$('dailyBody'),rows=(analysisData.daily||[]).slice().reverse();if(!rows.length){body.innerHTML=`<tr><td colspan="7" class="empty-cell">${tr('no_data')}</td></tr>`;return;}body.innerHTML=rows.map(r=>`<tr><td>${escapeHtml(r.date)}</td><td>${r.samples}</td><td>${fmtNumber(r.coverage_percent,0)} %</td><td>${radon(r.minimum_bq_m3)}</td><td>${radon(r.median_bq_m3)}</td><td>${radon(r.maximum_bq_m3)}</td><td>${radon(r.mean_bq_m3)}</td></tr>`).join('');
  }

  function options(items,valueKey,labelFn,allLabel) {return `${allLabel!==undefined?`<option value="">${escapeHtml(allLabel)}</option>`:''}${items.map(item=>`<option value="${escapeHtml(item[valueKey])}">${escapeHtml(labelFn(item))}</option>`).join('')}`;}
  function renderCatalog() {
    const updateSelect=(id,html,restoreValue=true,preferredValue=null)=>{
      const element=$(id);
      if(!element) return;
      const old=element.value;
      element.innerHTML=html;
      if(restoreValue && old) element.value=old;
      if(preferredValue!==null && (!element.value || !Array.from(element.options).some(option=>option.value===element.value))) {
        element.value=String(preferredValue);
      }
    };
    const locOpts=options(catalog.locations,'id',l=>[l.building,l.floor,l.name].filter(Boolean).join(' · '),tr('all_sites'));
    ['analysisLocation','historyLocation','reportLocation','eventLocation'].forEach(id=>updateSelect(id,locOpts));
    ['assignLocation'].forEach(id=>updateSelect(id,options(catalog.locations,'id',l=>[l.building,l.floor,l.name].filter(Boolean).join(' · '))));
    const deviceLabel=d=>[d.model,d.serial_number||d.device_id].filter(Boolean).join(' · ');
    const allDeviceOpts=options(catalog.devices,'device_id',deviceLabel,tr('all_devices_combined'));
    ['analysisDevice','historyDevice'].forEach(id=>{
      const element=$(id); if(!element) return;
      const old=element.value; element.innerHTML=allDeviceOpts;
      if(old&&catalog.devices.some(d=>String(d.device_id)===old)) element.value=old;
      else if(!catalogInitialised&&catalog.devices.length) element.value=String(catalog.devices[0].device_id);
    });
    const singleDeviceOpts=options(catalog.devices,'device_id',deviceLabel);
    ['assignDevice','reportDevice'].forEach(id=>{
      const element=$(id); if(!element) return;
      const old=element.value; element.innerHTML=singleDeviceOpts;
      if(old&&catalog.devices.some(d=>String(d.device_id)===old)) element.value=old;
      else if(catalog.devices.length) element.value=String(catalog.devices[0].device_id);
    });
    const campOpts=options(catalog.campaigns,'id',c=>`#${c.id} · ${fmtDate(c.started_at)} · ${c.sample_count} ${tr('samples')}`,tr('all_campaigns'));
    ['analysisCampaign','historyCampaign'].forEach(id=>updateSelect(id,campOpts));
    catalogInitialised=true;
    if($('locationCards')) renderLocations();
    if($('eventList')) renderEvents();
    if($('reportList')) renderReports();
  }

  function renderLocations() {
    $('locationCount').textContent=catalog.locations.length;const wrap=$('locationCards');if(!catalog.locations.length){wrap.innerHTML=`<div class="empty">${tr('no_sites')}</div>`;return;}
    wrap.innerHTML=catalog.locations.map(l=>`<article class="location-card"><h4>${escapeHtml(l.name)}</h4><p>${escapeHtml([l.building,l.floor,l.room_type].filter(Boolean).join(' · ')||tr('not_available'))}</p><div class="location-value">${l.latest_bq_m3===null||l.latest_bq_m3===undefined?'–':radon(l.latest_bq_m3)}</div><p>${fmtInteger(l.sample_count||0)} ${tr('samples')} · ${fmtDate(l.latest_at)}</p><div class="location-actions"><button class="mini-button" data-action="edit-location" data-id="${l.id}">${tr('edit')}</button><button class="mini-button" data-action="delete-location" data-id="${l.id}">${tr('delete')}</button></div></article>`).join('');
    wrap.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',async()=>{const id=Number(button.dataset.id);if(button.dataset.action==='edit-location')editLocation(id);if(button.dataset.action==='delete-location'){if(!confirm(tr('confirm_delete_site')))return;try{await api(`api/locations/${id}`,{method:'DELETE'});toast(tr('deleted'));await reloadCatalog();}catch(err){toast(err.message,true);}}}));
  }

  function editLocation(id) {const l=catalog.locations.find(x=>Number(x.id)===Number(id));if(!l)return;$('locationId').value=l.id;$('locationName').value=l.name||'';$('locationBuilding').value=l.building||'';$('locationFloor').value=l.floor||'';$('locationRoomType').value=l.room_type||'';$('locationHeight').value=l.measurement_height_m??'';$('locationNotes').value=l.notes||'';$('locationName').focus();}

  function renderEvents() {$('eventCount').textContent=catalog.events.length;const wrap=$('eventList');if(!catalog.events.length){wrap.innerHTML=`<div class="empty">${tr('no_events')}</div>`;return;}wrap.innerHTML=catalog.events.slice(0,100).map(e=>`<div class="event-item"><small>${fmtDate(e.occurred_at)}</small><strong>${escapeHtml(tr(`event_${e.event_type}`)||e.event_type)}</strong><div><strong>${escapeHtml(e.title)}</strong><small>${escapeHtml([e.location_name,e.notes].filter(Boolean).join(' · '))}</small></div><button class="mini-button" data-delete-event="${e.id}">${tr('delete')}</button></div>`).join('');wrap.querySelectorAll('[data-delete-event]').forEach(btn=>btn.addEventListener('click',async()=>{if(!confirm(tr('confirm_delete_event')))return;try{await api(`api/events/${btn.dataset.deleteEvent}`,{method:'DELETE'});toast(tr('deleted'));await reloadCatalog();}catch(err){toast(err.message,true);}}));}

  function renderReports() {$('reportCount').textContent=catalog.reports.length;const wrap=$('reportList');if(!catalog.reports.length){wrap.innerHTML=`<div class="empty">${tr('no_reports')}</div>`;return;}wrap.innerHTML=catalog.reports.map(r=>`<div class="report-item"><small>${fmtDate(r.created_at)}</small><div><strong>${escapeHtml(r.title)}</strong><small>${escapeHtml(r.location_name||tr('all_sites'))} · ${escapeHtml(r.device_model||r.device_id||tr('not_available'))} · ${escapeHtml(r.profile)}</small></div><div><strong>${r.mean_bq_m3===null||r.mean_bq_m3===undefined?'–':radon(r.mean_bq_m3)}</strong><small>${fmtInteger(r.samples)} ${tr('samples')} · ${fmtNumber(r.coverage_percent,0)} %</small></div><div class="report-actions"><a class="mini-button" href="reports/${encodeURIComponent(r.report_id)}" target="_blank">PDF</a><button class="mini-button" data-delete-report="${escapeHtml(r.report_id)}">${tr('delete')}</button></div></div>`).join('');wrap.querySelectorAll('[data-delete-report]').forEach(btn=>btn.addEventListener('click',async()=>{if(!confirm(tr('confirm_delete_report')))return;try{await api(`api/reports/${encodeURIComponent(btn.dataset.deleteReport)}`,{method:'DELETE'});toast(tr('deleted'));await reloadCatalog();}catch(err){toast(err.message,true);}}));}

  function historyQuery() {const params=new URLSearchParams({limit:'10000'});const value=id=>$(id)?.value||'';const start=toIso(value('historyStart')),end=toIso(value('historyEnd'));if(start)params.set('start',start);if(end)params.set('end',end);if(value('historyDevice'))params.set('device_id',value('historyDevice'));if(value('historyLocation'))params.set('location_id',value('historyLocation'));if(value('historyCampaign'))params.set('campaign_id',value('historyCampaign'));return params;}
  async function loadHistoryFiltered() {try{const payload=await api(`api/history?${historyQuery()}`);records=payload.items||[];renderHistory();renderOverviewChart();const exportParams=historyQuery();exportParams.delete('limit');$('historyCsv').href=`export/history.csv?${exportParams}`;}catch(err){toast(err.message,true);}}
  function renderHistory() {const body=$('historyBody');$('historySummary').textContent=`${fmtInteger(records.length)} ${tr('samples')}`;if(!records.length){body.innerHTML=`<tr><td colspan="7" class="empty-cell">${tr('history_empty')}</td></tr>`;return;}body.innerHTML=records.slice(0,1000).map(row=>`<tr><td>${fmtDate(row.completed_at)}</td><td>${radon(row.bq_m3)}</td><td>${row.raw_cph}</td><td>${escapeHtml([row.model,row.serial_number||row.device_id].filter(Boolean).join(' · '))}</td><td>${escapeHtml(row.location_name||tr('not_assigned'))}</td><td>#${row.campaign_id}</td><td>${tr('source_spir')}</td></tr>`).join('');}

  async function loadGmcmap() {
    try {
      const payload=await api('api/gmcmap?limit=100'); const st=payload.status||{};
      const badge=$('gmcmapStatusBadge'); badge.className=`badge ${st.enabled&&st.configured?'normal':'neutral'}`; badge.textContent=st.enabled?(st.configured?tr('ready'):tr('not_configured')):tr('disabled');
      $('gmcmapFacts').innerHTML=[fact(tr('enabled'),bool(st.enabled)),fact(tr('automatic_upload'),bool(st.auto_upload)),fact(tr('account_id'),st.account_id_masked||tr('not_configured')),fact(tr('device_id'),st.device_id_masked||tr('not_configured')),fact(tr('upload_interval'),`${st.interval_minutes||60} min`),fact(tr('pending_uploads'),st.queue?.pending_total??0),fact(tr('oldest_pending'),fmtDate(st.queue?.oldest_pending)),fact(tr('endpoint'),st.endpoint||'–')].join('');
      $('gmcmapNotice').textContent=st.enabled&&st.configured?tr('gmcmap_ready_notice'):tr('gmcmap_setup_notice');
      const latest=state?.measurement||{};$('gmcmapLatestValue').textContent=latest.available?`${fmtNumber(latest.bq_m3,1)} Bq/m³ · ${fmtNumber(latest.pci_l,3)} pCi/L`:tr('no_data');$('gmcmapLatestTime').textContent=fmtDate(latest.completed_at);
      const rows=payload.uploads||[];$('gmcmapHistoryBody').innerHTML=rows.length?rows.map(r=>`<tr><td>${fmtDate(r.attempted_at)}</td><td>${fmtDate(r.measurement_at)}</td><td>${fmtNumber(r.bq_m3,1)}</td><td>${fmtNumber(r.pci_l,4)}</td><td>${escapeHtml(tr(r.trigger)||r.trigger)}</td><td><span class="badge ${r.ok?'normal':'danger'}">${r.ok?tr('successful'):tr('failed')}</span></td><td><code>${escapeHtml(r.response||'–')}</code></td></tr>`).join(''):`<tr><td colspan="7" class="empty-cell">${tr('no_uploads')}</td></tr>`;
    } catch(err) {toast(err.message,true);}
  }

  async function retryGmcmap() {const button=$('gmcmapRetryButton');button.disabled=true;try{const result=await api('api/gmcmap/retry',{method:'POST',body:{}});toast(`${tr('retry_scheduled')}: ${result.retried||0}`);await loadGmcmap();}catch(err){toast(err.message,true);}finally{button.disabled=false;}}
  async function uploadGmcmap() {const button=$('gmcmapUploadButton');button.disabled=true;try{await api('api/gmcmap/upload',{method:'POST',body:{confirmation:$('gmcmapConfirmation').value}});toast(tr('upload_successful'));$('gmcmapConfirmation').value='';await loadGmcmap();loadAudit();}catch(err){toast(err.message,true);}finally{button.disabled=false;}}

  async function reloadCatalog() {catalog=await api('api/catalog');renderCatalog();}
  async function loadStateFast() {
    const refreshed=await api('api/state');
    state=refreshed;
    renderState();
    const ha=state.homeassistant||{};
    const haStatus=$('haStatus');
    if(haStatus)haStatus.textContent=ha.connected?`${tr('connected')} · ${ha.location_name||''} · ${ha.version||''}`:(ha.error||tr('offline'));
    return state;
  }
  async function loadAll() {
    if(loadInProgress) return;
    loadInProgress=true;
    const refreshButton=$('refreshButton'); if(refreshButton) refreshButton.disabled=true;
    try {
      // Load and render the compact state first. Slow history, catalogue or analysis
      // requests must never keep the complete dashboard in its loading state.
      const s=await api('api/state');
      state=s;
      renderState();
      const ha=state.homeassistant||{};
      $('haStatus').textContent=ha.connected?`${tr('connected')} · ${ha.location_name||''} · ${ha.version||''}`:(ha.error||tr('offline'));
      initialLoadComplete=true;

      // If an Ingress iframe survived an add-on update, reload once so HTML,
      // JavaScript and backend use the same release.
      if(state.app?.version && boot.version && state.app.version!==boot.version && !storageGet('session','radonVersionReloaded')) {
        storageSet('session','radonVersionReloaded','1');
        location.reload();
        return;
      }

      const results=await Promise.allSettled([
        api('api/catalog'),
        api(`api/history?${historyQuery()}`),
      ]);
      if(results[0].status==='fulfilled') {catalog=results[0].value;renderCatalog();}
      else console.warn('Catalogue refresh failed',results[0].reason);
      if(results[1].status==='fulfilled') {
        records=results[1].value.items||[];
        renderHistory();
        renderOverviewChart();
        const exportParams=historyQuery();exportParams.delete('limit');$('historyCsv').href=`export/history.csv?${exportParams}`;
      } else console.warn('History refresh failed',results[1].reason);
    } catch(err) {
      // Only a failed state request means that the app/device status is unknown.
      // Rendering or secondary catalogue/history errors must not overwrite a
      // successfully received connection state with “Not connected”.
      if(!state) setConnection(false);
      toast(err.message,true);
      console.error(err);
    } finally {
      loadInProgress=false;
      if(refreshButton) refreshButton.disabled=false;
    }
  }

  function bindEvents() {
    $$('.nav-item').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
    $('menuButton').addEventListener('click',()=>setSidebar(!$('sidebar').classList.contains('open')));
    $('sidebarBackdrop').addEventListener('click',closeSidebar);
    document.addEventListener('keydown',event=>{if(event.key==='Escape')closeSidebar();});
    $('refreshButton')?.addEventListener('click',loadAll);
    $('languageSelect').addEventListener('change',event=>{const url=new URL(location.href);url.searchParams.set('lang',event.target.value);location.href=url.toString();});
    $$('#rangeSwitch button').forEach(button=>button.addEventListener('click',()=>{chartDays=Number(button.dataset.days);$$('#rangeSwitch button').forEach(x=>x.classList.toggle('active',x===button));renderOverviewChart();}));
    $('analysisApply')?.addEventListener('click',loadAnalysis);$('analysisPreset')?.addEventListener('change',()=>{const custom=$('analysisPreset')?.value==='custom';if($('analysisStart'))$('analysisStart').disabled=!custom;if($('analysisEnd'))$('analysisEnd').disabled=!custom;});
    $('analysisCsvButton').addEventListener('click',()=>{const params=analysisQuery();location.href=`export/history.csv?${params}`;});
    $('locationForm').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget;const payload={id:$('locationId').value||null,name:$('locationName').value,building:$('locationBuilding').value,floor:$('locationFloor').value,room_type:$('locationRoomType').value,map_id:null,x_percent:null,y_percent:null,measurement_height_m:$('locationHeight').value||null,notes:$('locationNotes').value,active:true};try{await api('api/locations',{method:'POST',body:payload});toast(tr('saved'));form.reset();$('locationId').value='';await reloadCatalog();}catch(err){toast(err.message,true);}});
    $('assignForm').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget;try{const result=await api('api/locations/assign',{method:'POST',body:{device_id:$('assignDevice').value,location_id:$('assignLocation').value,title:$('assignTitle').value,start:toIso($('assignStart').value),end:toIso($('assignEnd').value),purpose:$('assignPurpose').value,notes:$('assignNotes').value}});toast(`${tr('assigned')}: ${result.assigned}`);form.reset();await loadAll();}catch(err){toast(err.message,true);}});
    $('eventForm').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget;try{await api('api/events',{method:'POST',body:{event_type:$('eventType').value,occurred_at:toIso($('eventTime').value),location_id:$('eventLocation').value||null,title:$('eventTitle').value,notes:$('eventNotes').value}});toast(tr('saved'));form.reset();$('eventTime').value=toInput(new Date());await reloadCatalog();}catch(err){toast(err.message,true);}});
    $('gmcmapUploadButton').addEventListener('click',uploadGmcmap);$('gmcmapRetryButton').addEventListener('click',retryGmcmap);$('refreshGmcmap').addEventListener('click',loadGmcmap);
    $('historyApply').addEventListener('click',loadHistoryFiltered);
    $('reportForm').addEventListener('submit',async event=>{event.preventDefault();const button=$('createReportButton');button.disabled=true;button.textContent=tr('generating');try{const result=await api('api/reports',{method:'POST',body:{title:$('reportTitle').value,profile:$('reportProfile').value,locale:$('reportLocale').value,device_id:$('reportDevice').value,location_id:$('reportLocation').value||null,days:Number($('reportDays').value),start:toIso($('reportStart').value),end:toIso($('reportEnd').value)}});toast(tr('report_created'));await reloadCatalog();window.open(`reports/${encodeURIComponent(result.item.report_id)}`,'_blank');}catch(err){toast(err.message,true);}finally{button.disabled=false;button.textContent=tr('generate_pdf');}});
    $('deleteDataForm').addEventListener('submit',dataManagement.deleteData);
    $('restoreForm').addEventListener('submit',async event=>{event.preventDefault();if(!confirm(tr('confirm_restore')))return;const formElement=event.currentTarget;const form=new FormData(formElement);form.set('file',$('restoreFile').files[0]);form.set('confirmation',$('restoreConfirmation').value);try{await api('api/data/restore',{method:'POST',body:form});toast(tr('restored'));formElement.reset();await loadAll();}catch(err){toast(err.message,true);}});
    $('purgeHaHistory').addEventListener('click',dataManagement.purgeHa);$('verifyHaPurge').addEventListener('click',dataManagement.verifyHaPurge);$('refreshAudit').addEventListener('click',dataManagement.loadAudit);
    $('modalClose').addEventListener('click',()=> $('modal').classList.add('hidden'));
  }

  function resetClientData() {
    records=[];
    catalog={locations:[],sessions:[],campaigns:[],devices:[],events:[],reports:[]};
    analysisData=null;
    catalogInitialised=false;
  }

  dataManagement=window.RMDataManagement.create({
    $,tr,fmtInteger,fmtDate,fmtBytes,escapeHtml,api,toast,setView,loadAll,loadStateFast,resetClientData,
  });

  function initializeDefaults() {
    if($('analysisStart')) $('analysisStart').disabled=true;
    if($('analysisEnd')) $('analysisEnd').disabled=true;
    if($('eventTime')) $('eventTime').value=toInput(new Date());
    const latest=state?.measurement?.completed_at||new Date();
    if($('assignStart')) $('assignStart').value=toInput(latest);
    if($('reportLocale')) $('reportLocale').value=locale()==='de'?'de':'en';
  }

  applyTranslations();bindEvents();initializeDefaults();
  const requested=(location.hash||'').slice(1)||storageGet('local','radonMonitoringView')||'overview';setView($(`view-${requested}`)?requested:'overview');
  loadAll().then(initializeDefaults);
  // Retry quickly during startup; after the first successful state response use a
  // shorter regular refresh so newly imported USB measurements appear promptly.
  setInterval(()=>{if(!document.hidden)loadAll();},30000);
  const startupRetry=setInterval(()=>{if(initialLoadComplete){clearInterval(startupRetry);}else if(!document.hidden){loadAll();}},3000);
})();
