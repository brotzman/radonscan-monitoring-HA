(() => {
  'use strict';
  const boot = window.RADONSCAN_BOOT || {};
  const t = boot.translations || {};
  let state = null;
  let records = [];
  let catalog = {locations:[],sessions:[],campaigns:[],devices:[],events:[],reports:[]};
  let analysisData = null;
  let dataSummary = null;
  let chartDays = 7;
  let catalogInitialised = false;

  const $ = id => document.getElementById(id);
  const $$ = selector => Array.from(document.querySelectorAll(selector));
  const tr = key => t[key] || key;
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
  const unit = () => state?.settings?.preferred_unit === 'pCi/L' ? 'pCi/L' : 'Bq/m³';
  const radonValue = bq => unit()==='pCi/L' ? Number(bq)/37 : Number(bq);
  const radon = bq => bq === null || bq === undefined ? '–' : `${fmtNumber(radonValue(bq), unit()==='pCi/L'?3:1)} ${unit()}`;
  const bool = value => value ? tr('yes') : tr('no');
  const toIso = value => value ? new Date(value).toISOString() : null;
  const toInput = value => {
    if(!value) return '';
    const date=new Date(value); const local=new Date(date.getTime()-date.getTimezoneOffset()*60000); return local.toISOString().slice(0,16);
  };
  const statusText = value => tr(value || 'unknown');

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
    const el=$('toast'); el.textContent=message; el.className=`toast show${error?' error':''}`;
    clearTimeout(toast.timer); toast.timer=setTimeout(()=>el.className='toast',3500);
  }

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
    if(!enabled && (location.hash==='#data' || localStorage.getItem('radonMonitoringView')==='data')) {
      localStorage.setItem('radonMonitoringView','overview');
      if(location.hash==='#data') history.replaceState(null,'','#overview');
    }
  }

  function setView(name) {
    if(name==='data' && !dataManagementEnabled()) name='overview';
    $$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
    $$('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${name}`));
    history.replaceState(null,'',`#${name}`);
    localStorage.setItem('radonMonitoringView',name);
    closeSidebar();
    if(name==='analysis'&&!analysisData) loadAnalysis();
    if(name==='data') {loadDataSummary();loadAudit();}
    if(name==='map') loadGmcmap();
  }

  function setConnection(connected) {
    const pill=$('connectionPill'); pill.className=`status-pill ${connected?'ok':'error'}`;
    pill.querySelector('span:last-child').textContent=connected?tr('connected'):tr('disconnected');
    $('sidebar').classList.toggle('connected',connected);
    $('sidebar').classList.toggle('disconnected',!connected);
    const footer=$('sidebar').querySelector('.sidebar-footer'); footer.className=`sidebar-footer ${connected?'ok':'error'}`;
    $('sidebarConnection').textContent=connected?tr('connected'):tr('disconnected');
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
    const rows=[[tr('scan_interval'),`${s.scan_interval} ${tr('seconds')}`],[tr('preferred_unit'),s.preferred_unit],[tr('language'),s.language==='auto'?tr('automatic'):s.language],[tr('conversion_factor'),`${s.factor_bq_m3_per_cph} ${tr('factor_unit')}`],[tr('warning_threshold'),`${s.warning_threshold_bq_m3} Bq/m³`],[tr('danger_threshold'),`${s.danger_threshold_bq_m3} Bq/m³`],[tr('minimum_coverage'),`${s.minimum_data_coverage_percent} %`],[tr('backfill'),bool(s.backfill_history)],[tr('retention'),`${s.history_retention_days} ${tr('days')}`],[tr('serial_port'),s.serial_port],[tr('data_management'),bool(s.data_management_enabled)],[tr('diagnostic_logging'),bool(s.diagnostic_logging)],[tr('report_author'),s.report_author||tr('not_set')],[tr('report_organisation'),s.report_organisation||tr('not_set')]];
    $('settingsGrid').innerHTML=rows.map(([a,b])=>`<div class="setting-row"><span>${escapeHtml(a)}</span><strong>${escapeHtml(b)}</strong></div>`).join('');
  }

  function renderExpert() {
    const d=state.device||{},p=state.protocol||{},m=state.measurement||{},c=state.connection||{};
    $('expertDeviceFacts').innerHTML=[fact(tr('model'),d.model),fact(tr('firmware'),fmtFirmware(d.firmware)),fact(tr('serial_number'),d.serial_number),fact(tr('serial_port'),d.serial_port),fact(tr('first_seen'),fmtDate(d.first_seen)),fact(tr('last_seen'),fmtDate(d.last_seen))].join('');
    $('expertProtocolFacts').innerHTML=[fact(tr('decoder'),p.decoder),fact(tr('protocol'),p.transport),fact(tr('raw_start_offset'),p.raw_start_offset),fact(tr('raw_end_offset'),p.raw_end_offset),fact('FD 0x270',p.fd_value_0x270),fact(tr('time_records'),p.time_record_count),fact(tr('hourly_records'),p.hourly_record_count)].join('');
    $('expertDataFacts').innerHTML=[fact(tr('hour_index'),m.hour_index),fact(tr('raw_cph'),m.raw_cph),fact(tr('conversion_factor'),m.factor_bq_m3_per_cph),fact(tr('source'),m.source),fact(tr('campaign'),p.imported?.latest_hour_index??'–'),fact(tr('database_integrity'),state.database?.integrity),fact(tr('data_age'),m.age_hours===null?'–':`${fmtNumber(m.age_hours,2)} h`)].join('');
    $('hashes').textContent=JSON.stringify(p.block_sha256||{},null,2);
    $('runtimeSummary').textContent=JSON.stringify({connection:c,mqtt:state.mqtt,protocol_import:p.imported,database:state.database,catalog:state.catalog},null,2);
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
    const preset=$('analysisPreset').value;const params=new URLSearchParams();
    if(preset!=='custom') params.set('days',preset);
    if(preset==='custom') {const start=toIso($('analysisStart').value),end=toIso($('analysisEnd').value);if(start)params.set('start',start);if(end)params.set('end',end);}
    if($('analysisDevice').value)params.set('device_id',$('analysisDevice').value);if($('analysisLocation').value)params.set('location_id',$('analysisLocation').value);if($('analysisCampaign').value)params.set('campaign_id',$('analysisCampaign').value);
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
    $('analysisUncertainty').textContent=u.available?`± ${radonValue(u.expanded_uncertainty_95_bq_m3).toLocaleString(locale(),{maximumFractionDigits:0})} ${unit()}`:'–';$('analysisUncertaintyNote').textContent=u.available?tr('counting_uncertainty_95'):tr('uncertainty_unavailable');
    $('scientificFacts').innerHTML=[fact(tr('quality_class'),s.scientific_quality_class||'–'),fact(tr('qc_flags'),fmtInteger(qc.flagged_records||0)),fact(tr('autocorrelation_1h'),analysisData.autocorrelation?.[0]?fmtNumber(analysisData.autocorrelation[0].coefficient,2):'–'),fact(tr('candidate_change_point'),cp.available?fmtDate(cp.detected_at):tr('not_calculable')),fact(tr('change_amount'),cp.available?radon(cp.absolute_change_bq_m3):'–')].join('');
    $('scientificNotice').textContent=tr('scientific_notice');
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
    const locOpts=options(catalog.locations,'id',l=>[l.building,l.floor,l.name].filter(Boolean).join(' · '),tr('all_sites'));
    ['analysisLocation','historyLocation','reportLocation','deleteLocation','eventLocation'].forEach(id=>{const old=$(id).value;$(id).innerHTML=locOpts;$(id).value=old;});
    ['assignLocation'].forEach(id=>{const old=$(id).value;$(id).innerHTML=options(catalog.locations,'id',l=>[l.building,l.floor,l.name].filter(Boolean).join(' · '));$(id).value=old;});
    const deviceLabel=d=>[d.model,d.serial_number||d.device_id].filter(Boolean).join(' · ');
    const allDeviceOpts=options(catalog.devices,'device_id',deviceLabel,tr('all_devices_combined'));
    ['analysisDevice','historyDevice','deleteDevice'].forEach(id=>{const old=$(id).value;$(id).innerHTML=allDeviceOpts;if(old&&catalog.devices.some(d=>String(d.device_id)===old))$(id).value=old;else if(!catalogInitialised&&catalog.devices.length)$(id).value=String(catalog.devices[0].device_id);});
    const singleDeviceOpts=options(catalog.devices,'device_id',deviceLabel);
    ['assignDevice','reportDevice'].forEach(id=>{const old=$(id).value;$(id).innerHTML=singleDeviceOpts;if(old&&catalog.devices.some(d=>String(d.device_id)===old))$(id).value=old;else if(catalog.devices.length)$(id).value=String(catalog.devices[0].device_id);});
    const campOpts=options(catalog.campaigns,'id',c=>`#${c.id} · ${fmtDate(c.started_at)} · ${c.sample_count} ${tr('samples')}`,tr('all_campaigns'));
    ['analysisCampaign','historyCampaign','deleteCampaign'].forEach(id=>{const old=$(id).value;$(id).innerHTML=campOpts;$(id).value=old;});
    catalogInitialised=true;
    renderLocations();renderEvents();renderReports();
  }

  function renderLocations() {
    $('locationCount').textContent=catalog.locations.length;const wrap=$('locationCards');if(!catalog.locations.length){wrap.innerHTML=`<div class="empty">${tr('no_sites')}</div>`;return;}
    wrap.innerHTML=catalog.locations.map(l=>`<article class="location-card"><h4>${escapeHtml(l.name)}</h4><p>${escapeHtml([l.building,l.floor,l.room_type].filter(Boolean).join(' · ')||tr('not_available'))}</p><div class="location-value">${l.latest_bq_m3===null||l.latest_bq_m3===undefined?'–':radon(l.latest_bq_m3)}</div><p>${fmtInteger(l.sample_count||0)} ${tr('samples')} · ${fmtDate(l.latest_at)}</p><div class="location-actions"><button class="mini-button" data-action="edit-location" data-id="${l.id}">${tr('edit')}</button><button class="mini-button" data-action="delete-location" data-id="${l.id}">${tr('delete')}</button></div></article>`).join('');
    wrap.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',async()=>{const id=Number(button.dataset.id);if(button.dataset.action==='edit-location')editLocation(id);if(button.dataset.action==='delete-location'){if(!confirm(tr('confirm_delete_site')))return;try{await api(`api/locations/${id}`,{method:'DELETE'});toast(tr('deleted'));await reloadCatalog();}catch(err){toast(err.message,true);}}}));
  }

  function editLocation(id) {const l=catalog.locations.find(x=>Number(x.id)===Number(id));if(!l)return;$('locationId').value=l.id;$('locationName').value=l.name||'';$('locationBuilding').value=l.building||'';$('locationFloor').value=l.floor||'';$('locationRoomType').value=l.room_type||'';$('locationHeight').value=l.measurement_height_m??'';$('locationNotes').value=l.notes||'';$('locationName').focus();}

  function renderEvents() {$('eventCount').textContent=catalog.events.length;const wrap=$('eventList');if(!catalog.events.length){wrap.innerHTML=`<div class="empty">${tr('no_events')}</div>`;return;}wrap.innerHTML=catalog.events.slice(0,100).map(e=>`<div class="event-item"><small>${fmtDate(e.occurred_at)}</small><strong>${escapeHtml(tr(`event_${e.event_type}`)||e.event_type)}</strong><div><strong>${escapeHtml(e.title)}</strong><small>${escapeHtml([e.location_name,e.notes].filter(Boolean).join(' · '))}</small></div><button class="mini-button" data-delete-event="${e.id}">${tr('delete')}</button></div>`).join('');wrap.querySelectorAll('[data-delete-event]').forEach(btn=>btn.addEventListener('click',async()=>{if(!confirm(tr('confirm_delete_event')))return;try{await api(`api/events/${btn.dataset.deleteEvent}`,{method:'DELETE'});toast(tr('deleted'));await reloadCatalog();}catch(err){toast(err.message,true);}}));}

  function renderReports() {$('reportCount').textContent=catalog.reports.length;const wrap=$('reportList');if(!catalog.reports.length){wrap.innerHTML=`<div class="empty">${tr('no_reports')}</div>`;return;}wrap.innerHTML=catalog.reports.map(r=>`<div class="report-item"><small>${fmtDate(r.created_at)}</small><div><strong>${escapeHtml(r.title)}</strong><small>${escapeHtml(r.location_name||tr('all_sites'))} · ${escapeHtml(r.device_model||r.device_id||tr('not_available'))} · ${escapeHtml(r.profile)}</small></div><div><strong>${r.mean_bq_m3===null||r.mean_bq_m3===undefined?'–':radon(r.mean_bq_m3)}</strong><small>${fmtInteger(r.samples)} ${tr('samples')} · ${fmtNumber(r.coverage_percent,0)} %</small></div><div class="report-actions"><a class="mini-button" href="reports/${encodeURIComponent(r.report_id)}" target="_blank">PDF</a><button class="mini-button" data-delete-report="${escapeHtml(r.report_id)}">${tr('delete')}</button></div></div>`).join('');wrap.querySelectorAll('[data-delete-report]').forEach(btn=>btn.addEventListener('click',async()=>{if(!confirm(tr('confirm_delete_report')))return;try{await api(`api/reports/${encodeURIComponent(btn.dataset.deleteReport)}`,{method:'DELETE'});toast(tr('deleted'));await reloadCatalog();}catch(err){toast(err.message,true);}}));}

  function historyQuery() {const params=new URLSearchParams({limit:'10000'});const start=toIso($('historyStart').value),end=toIso($('historyEnd').value);if(start)params.set('start',start);if(end)params.set('end',end);if($('historyDevice').value)params.set('device_id',$('historyDevice').value);if($('historyLocation').value)params.set('location_id',$('historyLocation').value);if($('historyCampaign').value)params.set('campaign_id',$('historyCampaign').value);return params;}
  async function loadHistoryFiltered() {try{const payload=await api(`api/history?${historyQuery()}`);records=payload.items||[];renderHistory();renderOverviewChart();const exportParams=historyQuery();exportParams.delete('limit');$('historyCsv').href=`export/history.csv?${exportParams}`;}catch(err){toast(err.message,true);}}
  function renderHistory() {const body=$('historyBody');$('historySummary').textContent=`${fmtInteger(records.length)} ${tr('samples')}`;if(!records.length){body.innerHTML=`<tr><td colspan="7" class="empty-cell">${tr('history_empty')}</td></tr>`;return;}body.innerHTML=records.slice(0,1000).map(row=>`<tr><td>${fmtDate(row.completed_at)}</td><td>${radon(row.bq_m3)}</td><td>${row.raw_cph}</td><td>${escapeHtml([row.model,row.serial_number||row.device_id].filter(Boolean).join(' · '))}</td><td>${escapeHtml(row.location_name||tr('not_assigned'))}</td><td>#${row.campaign_id}</td><td>${tr('source_spir')}</td></tr>`).join('');}

  async function loadDataSummary() {try{dataSummary=await api('api/data/summary');renderDataSummary();}catch(err){toast(err.message,true);}}
  function renderDataSummary() {if(!dataSummary)return;$('dataMeasurements').textContent=fmtInteger(dataSummary.measurements);$('dataRange').textContent=`${fmtDate(dataSummary.first_measurement)} – ${fmtDate(dataSummary.last_measurement)}`;$('dataDbSize').textContent=fmtBytes(dataSummary.database_size_bytes);$('dataIntegrity').textContent=`${tr('integrity')}: ${dataSummary.integrity}`;$('dataFiles').textContent=fmtInteger(dataSummary.reports);$('dataFileSize').textContent=fmtBytes(Number(dataSummary.report_size_bytes||0));$('dataSchema').textContent=`v${dataSummary.schema_version}`;}

  function deletePayload(preview=false, confirmation='') {return {action:$('deleteAction').value,preview,start:toIso($('deleteStart').value),end:toIso($('deleteEnd').value),device_id:$('deleteDevice').value||null,location_id:$('deleteLocation').value||null,campaign_id:$('deleteCampaign').value||null,confirmation:preview?'':confirmation,confirmation_text:preview?'':confirmation,confirmed:!preview};}
  async function previewDeletion() {try{const result=await api('api/data/delete',{method:'POST',body:deletePayload(true)});const p=result.preview;const box=$('deletePreviewResult');box.className=`notice ${Number(p.count||p.measurements||0)>0?'warning':''}`;box.textContent=`${tr('affected_records')}: ${fmtInteger(p.count??p.measurements??0)}${p.first_at?` · ${fmtDate(p.first_at)} – ${fmtDate(p.last_at)}`:''}`;}catch(err){toast(err.message,true);}}
  async function deleteData(event) {event.preventDefault();const confirmation=($('deleteConfirmation').value||'').trim().toUpperCase().replace(/\s+/g,'');if(!['LÖSCHEN','LOESCHEN','DELETE','PURGE','PRURGE','PRUGE'].includes(confirmation)){toast(tr('confirmation_invalid'),true);$('deleteConfirmation').focus();return;}if(!confirm(tr('confirm_destructive_action')))return;try{const result=await api('api/data/delete',{method:'POST',body:deletePayload(false,confirmation),confirmation});toast(`${tr('deleted')}: ${fmtInteger(result.deleted||0)} · ${tr('backup')}: ${result.backup}`);$('deleteConfirmation').value='';await loadAll();loadDataSummary();loadAudit();}catch(err){toast(err.message,true);}}

  async function loadAudit() {try{const payload=await api('api/audit?limit=200');const body=$('auditBody'),items=payload.items||[];body.innerHTML=items.length?items.map(item=>`<tr><td>${fmtDate(item.created_at)}</td><td>${escapeHtml(item.action)}</td><td>${escapeHtml(item.target||'–')}</td><td>${escapeHtml(item.user_name||'–')}</td><td><code>${escapeHtml(JSON.stringify(item.details||{}))}</code></td></tr>`).join(''):`<tr><td colspan="5" class="empty-cell">${tr('no_data')}</td></tr>`;}catch(err){toast(err.message,true);}}

  async function loadHaEntities() {const button=$('loadHaEntities');button.disabled=true;try{const payload=await api('api/homeassistant/entities');const items=payload.items||[];$('haEntityList').innerHTML=items.length?items.map(item=>`<label class="checkbox-item"><input type="checkbox" value="${escapeHtml(item.entity_id)}" ${item.recommended?'checked':''}><span>${escapeHtml(item.friendly_name)}<small>${escapeHtml(item.entity_id)} · ${escapeHtml(item.state??'–')} ${escapeHtml(item.unit||'')}</small></span></label>`).join(''):`<div class="notice">${tr('no_ha_entities')}</div>`;$('haStatus').textContent=`${items.length} ${tr('entities_detected')}`;}catch(err){$('haStatus').textContent=err.message;toast(err.message,true);}finally{button.disabled=false;}}
  async function purgeHa() {const ids=$$('#haEntityList input:checked').map(x=>x.value);if(!ids.length){toast(tr('select_entities'),true);return;}const confirmation=($('haConfirmation').value||'').trim().toUpperCase().replace(/\s+/g,'');if(!['PURGE','LÖSCHEN','LOESCHEN','DELETE','PRURGE','PRUGE'].includes(confirmation)){toast(tr('confirmation_invalid'),true);$('haConfirmation').focus();return;}if(!confirm(tr('confirm_ha_purge')))return;try{const result=await api('api/homeassistant/purge',{method:'POST',body:{entity_ids:ids,keep_days:Number($('haKeepDays').value||0),confirmation,confirmation_text:confirmation,confirmed:true},confirmation});toast(`${tr('purge_requested')}: ${result.entity_ids.length}`);$('haConfirmation').value='';loadAudit();}catch(err){toast(err.message,true);}}

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
  async function loadAll() {
    $('refreshButton').disabled=true;
    try {
      const [s,c]=await Promise.all([api('api/state'),api('api/catalog')]);state=s;catalog=c;renderState();renderCatalog();
      const h=await api(`api/history?${historyQuery()}`);records=h.items||[];renderHistory();renderOverviewChart();
      const exportParams=historyQuery();exportParams.delete('limit');$('historyCsv').href=`export/history.csv?${exportParams}`;
      const ha=state.homeassistant||{};$('haStatus').textContent=ha.connected?`${tr('connected')} · ${ha.location_name||''} · ${ha.version||''}`:(ha.error||tr('offline'));
      if(!analysisData) await loadAnalysis();
    } catch(err) {setConnection(false);toast(err.message,true);console.error(err);} finally {$('refreshButton').disabled=false;}
  }

  function bindEvents() {
    $$('.nav-item').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
    $('menuButton').addEventListener('click',()=>setSidebar(!$('sidebar').classList.contains('open')));
    $('sidebarBackdrop').addEventListener('click',closeSidebar);
    document.addEventListener('keydown',event=>{if(event.key==='Escape')closeSidebar();});
    $('refreshButton').addEventListener('click',loadAll);
    $('languageSelect').addEventListener('change',event=>{const url=new URL(location.href);url.searchParams.set('lang',event.target.value);location.href=url.toString();});
    $$('#rangeSwitch button').forEach(button=>button.addEventListener('click',()=>{chartDays=Number(button.dataset.days);$$('#rangeSwitch button').forEach(x=>x.classList.toggle('active',x===button));renderOverviewChart();}));
    $('analysisApply').addEventListener('click',loadAnalysis);$('analysisPreset').addEventListener('change',()=>{const custom=$('analysisPreset').value==='custom';$('analysisStart').disabled=!custom;$('analysisEnd').disabled=!custom;});
    $('analysisCsvButton').addEventListener('click',()=>{const params=analysisQuery();location.href=`export/history.csv?${params}`;});
    $('copyHashes').addEventListener('click',async()=>{await navigator.clipboard.writeText($('hashes').textContent);toast(tr('copied'));});
    $('locationForm').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget;const payload={id:$('locationId').value||null,name:$('locationName').value,building:$('locationBuilding').value,floor:$('locationFloor').value,room_type:$('locationRoomType').value,map_id:null,x_percent:null,y_percent:null,measurement_height_m:$('locationHeight').value||null,notes:$('locationNotes').value,active:true};try{await api('api/locations',{method:'POST',body:payload});toast(tr('saved'));form.reset();$('locationId').value='';await reloadCatalog();}catch(err){toast(err.message,true);}});
    $('assignForm').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget;try{const result=await api('api/locations/assign',{method:'POST',body:{device_id:$('assignDevice').value,location_id:$('assignLocation').value,title:$('assignTitle').value,start:toIso($('assignStart').value),end:toIso($('assignEnd').value),purpose:$('assignPurpose').value,notes:$('assignNotes').value}});toast(`${tr('assigned')}: ${result.assigned}`);form.reset();await loadAll();}catch(err){toast(err.message,true);}});
    $('eventForm').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget;try{await api('api/events',{method:'POST',body:{event_type:$('eventType').value,occurred_at:toIso($('eventTime').value),location_id:$('eventLocation').value||null,title:$('eventTitle').value,notes:$('eventNotes').value}});toast(tr('saved'));form.reset();$('eventTime').value=toInput(new Date());await reloadCatalog();}catch(err){toast(err.message,true);}});
    $('gmcmapUploadButton').addEventListener('click',uploadGmcmap);$('gmcmapRetryButton').addEventListener('click',retryGmcmap);$('refreshGmcmap').addEventListener('click',loadGmcmap);
    $('historyApply').addEventListener('click',loadHistoryFiltered);
    $('reportForm').addEventListener('submit',async event=>{event.preventDefault();const button=$('createReportButton');button.disabled=true;button.textContent=tr('generating');try{const result=await api('api/reports',{method:'POST',body:{title:$('reportTitle').value,profile:$('reportProfile').value,locale:$('reportLocale').value,device_id:$('reportDevice').value,location_id:$('reportLocation').value||null,days:Number($('reportDays').value),start:toIso($('reportStart').value),end:toIso($('reportEnd').value)}});toast(tr('report_created'));await reloadCatalog();window.open(`reports/${encodeURIComponent(result.item.report_id)}`,'_blank');}catch(err){toast(err.message,true);}finally{button.disabled=false;button.textContent=tr('generate_pdf');}});
    $('deletePreview').addEventListener('click',previewDeletion);$('deleteDataForm').addEventListener('submit',deleteData);
    $('restoreForm').addEventListener('submit',async event=>{event.preventDefault();if(!confirm(tr('confirm_restore')))return;const formElement=event.currentTarget;const form=new FormData(formElement);form.set('file',$('restoreFile').files[0]);form.set('confirmation',$('restoreConfirmation').value);try{await api('api/data/restore',{method:'POST',body:form});toast(tr('restored'));formElement.reset();await loadAll();}catch(err){toast(err.message,true);}});
    $('loadHaEntities').addEventListener('click',loadHaEntities);$('purgeHaHistory').addEventListener('click',purgeHa);$('refreshAudit').addEventListener('click',loadAudit);
    $('modalClose').addEventListener('click',()=> $('modal').classList.add('hidden'));
  }

  function initializeDefaults() {
    $('analysisStart').disabled=true;$('analysisEnd').disabled=true;$('eventTime').value=toInput(new Date());
    const latest=state?.measurement?.completed_at||new Date();$('assignStart').value=toInput(latest);$('reportLocale').value=locale()==='de'?'de':'en';
  }

  applyTranslations();bindEvents();initializeDefaults();
  const requested=(location.hash||'').slice(1)||localStorage.getItem('radonMonitoringView')||'overview';setView($(`view-${requested}`)?requested:'overview');
  loadAll().then(initializeDefaults);
  setInterval(()=>{if(!document.hidden)loadAll();},60000);
})();
