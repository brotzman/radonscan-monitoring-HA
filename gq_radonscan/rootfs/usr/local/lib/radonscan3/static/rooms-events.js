(() => {
  'use strict';

  function create(deps) {
    const {$,tr,escapeHtml,fmtNumber,fmtInteger,fmtDate,toIso,toInput,api,toast} = deps;
    let preferredRoomId = null;

    const catalog = () => deps.getCatalog() || {locations:[],sessions:[],devices:[],events:[]};
    const state = () => deps.getState() || {};
    const roomLabel = item => String(item?.room || item?.name || tr('not_available'));
    const options = (items, valueKey, labelFn, allLabel) => `${allLabel !== undefined ? `<option value="">${escapeHtml(allLabel)}</option>` : ''}${items.map(item => `<option value="${escapeHtml(item[valueKey])}">${escapeHtml(labelFn(item))}</option>`).join('')}`;

    function setFieldError(inputId, errorId, message='') {
      const input=$(inputId), error=$(errorId);
      if(input) {
        input.setCustomValidity(message);
        input.setAttribute('aria-invalid',message?'true':'false');
      }
      if(error) {
        error.textContent=message;
        error.hidden=!message;
      }
    }

    function setFormStatus(id, message='', kind='') {
      const element=$(id);
      if(!element) return;
      element.textContent=message;
      element.hidden=!message;
      element.className=`form-status${kind?` ${kind}`:''}`;
    }

    function clearRoomErrors() {
      setFieldError('locationRoom','locationRoomError');
      setFieldError('locationHeight','locationHeightError');
      setFormStatus('locationFormStatus');
    }

    function clearAssignmentErrors() {
      setFieldError('assignLocation','assignLocationError');
      setFieldError('assignTitle','assignTitleError');
      setFieldError('assignStart','assignStartError');
      setFieldError('assignEnd','assignEndError');
      setFormStatus('assignFormStatus');
    }

    function backendMessage(error) {
      const message=String(error?.message||error||'');
      const known={
        'A room name is required':'room_name_required',
        'Room names may contain at most 120 characters':'room_name_too_long',
        'Room names must not contain control characters':'room_name_invalid',
        'Measurement height must be a number':'measurement_height_number',
        'Measurement height must be between 0 and 10 metres':'measurement_height_range',
        'A room with this name already exists':'room_already_exists',
        'The selected room does not exist':'selected_room_missing',
        'A valid session start is required':'assignment_start_required',
        'Session end must be after start':'assignment_end_after_start',
      };
      return tr(known[message]||message);
    }

    function updateSelect(id, html, preferred=null) {
      const element=$(id);
      if(!element) return;
      const previous=element.value;
      element.innerHTML=html;
      const has=value=>value!==null&&value!==undefined&&Array.from(element.options).some(option=>option.value===String(value));
      if(has(preferred)) element.value=String(preferred);
      else if(has(previous)) element.value=previous;
    }

    function renderSelectors() {
      const locations=catalog().locations||[];
      const preferred=preferredRoomId ?? state()?.measurement?.location_id ?? null;
      updateSelect('assignLocation',options(locations,'id',roomLabel),preferred);
      updateSelect('eventLocation',options(locations,'id',roomLabel,tr('all_sites')),preferred);
      setAssignmentEnabled(locations.length>0);
    }

    function setAssignmentEnabled(enabled) {
      const fieldset=$('assignFieldset'), panel=$('assignmentPanel'), notice=$('assignEmptyNotice');
      if(fieldset) fieldset.disabled=!enabled;
      if(panel) panel.classList.toggle('workflow-disabled',!enabled);
      if(notice) notice.hidden=enabled;
      const button=$('assignButton');
      if(button) button.disabled=!enabled;
    }

    function renderLocations() {
      const locations=catalog().locations||[];
      const count=$('locationCount'), wrap=$('locationCards');
      if(count) count.textContent=locations.length;
      if(!wrap) return;
      if(!locations.length) {
        wrap.innerHTML=`<div class="empty">${escapeHtml(tr('no_sites_next_step'))}</div>`;
        return;
      }
      const ha=state()?.homeassistant||catalog().homeassistant_location||{};
      const building=ha.building_name||ha.location_name||'';
      const place=ha.place_address||ha.address||'';
      const inherited=[building,place].filter((value,index,items)=>value&&items.indexOf(value)===index).join(' · ')||tr('ha_location_unavailable');
      wrap.innerHTML=locations.map(location=>{
        const height=location.measurement_height_m===null||location.measurement_height_m===undefined?tr('not_set'):`${fmtNumber(Number(location.measurement_height_m),1)} m`;
        return `<article class="location-card"><h4>${escapeHtml(roomLabel(location))}</h4><p>${escapeHtml(inherited)}</p><p><strong>${escapeHtml(tr('measurement_height'))}:</strong> ${escapeHtml(height)}</p><div class="location-value">${location.latest_bq_m3===null||location.latest_bq_m3===undefined?'–':deps.radon(location.latest_bq_m3)}</div><p>${fmtInteger(location.sample_count||0)} ${escapeHtml(tr('samples'))} · ${fmtDate(location.latest_at)}</p><div class="location-actions"><button class="mini-button" type="button" data-action="edit-location" data-id="${location.id}">${escapeHtml(tr('edit'))}</button><button class="mini-button" type="button" data-action="delete-location" data-id="${location.id}">${escapeHtml(tr('delete'))}</button></div></article>`;
      }).join('');
      wrap.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',async()=>{
        const id=Number(button.dataset.id);
        if(button.dataset.action==='edit-location') editLocation(id);
        if(button.dataset.action==='delete-location') {
          if(!confirm(tr('confirm_delete_site'))) return;
          try {
            await api(`api/locations/${id}`,{method:'DELETE'});
            toast(tr('deleted'));
            if(preferredRoomId===id) preferredRoomId=null;
            await deps.reloadCatalog();
            await deps.loadOverviewSelection(false);
          } catch(error) { toast(backendMessage(error),true); }
        }
      }));
    }

    function renderSessions() {
      const sessions=catalog().sessions||[];
      const count=$('assignmentCount'), wrap=$('assignmentList');
      if(count) count.textContent=sessions.length;
      if(!wrap) return;
      if(!sessions.length) {
        wrap.innerHTML=`<div class="empty">${escapeHtml(tr('no_assignments'))}</div>`;
        return;
      }
      const deviceName=deviceId=>{
        const device=(catalog().devices||[]).find(item=>String(item.device_id)===String(deviceId));
        return [device?.model,device?.serial_number||deviceId].filter(Boolean).join(' · ')||tr('not_available');
      };
      wrap.innerHTML=sessions.slice(0,100).map(session=>{
        const period=[fmtDate(session.started_at),session.ended_at?fmtDate(session.ended_at):tr('ongoing')].join(' – ');
        const meta=[session.location_name||tr('not_assigned'),deviceName(session.device_id),`${fmtInteger(session.sample_count||0)} ${tr('samples')}`].join(' · ');
        return `<article class="assignment-item"><small>${escapeHtml(period)}</small><div><strong>${escapeHtml(session.title||tr('measurement_session'))}</strong><small>${escapeHtml(meta)}</small>${session.purpose?`<small>${escapeHtml(session.purpose)}</small>`:''}</div></article>`;
      }).join('');
    }

    function renderEvents() {
      const events=catalog().events||[];
      const count=$('eventCount'), wrap=$('eventList');
      if(count) count.textContent=events.length;
      if(!wrap) return;
      if(!events.length) {
        wrap.innerHTML=`<div class="empty">${escapeHtml(tr('no_events'))}</div>`;
        return;
      }
      wrap.innerHTML=events.slice(0,100).map(event=>`<div class="event-item"><small>${fmtDate(event.occurred_at)}</small><div><strong>${escapeHtml(tr(`event_${event.event_type}`)||event.event_type)} · ${escapeHtml(event.title)}</strong><small>${escapeHtml([event.location_name,event.notes].filter(Boolean).join(' · '))}</small></div><button class="mini-button" type="button" data-delete-event="${event.id}">${escapeHtml(tr('delete'))}</button></div>`).join('');
      wrap.querySelectorAll('[data-delete-event]').forEach(button=>button.addEventListener('click',async()=>{
        if(!confirm(tr('confirm_delete_event'))) return;
        try {
          await api(`api/events/${button.dataset.deleteEvent}`,{method:'DELETE'});
          toast(tr('deleted'));
          await deps.reloadCatalog();
        } catch(error) { toast(backendMessage(error),true); }
      }));
    }

    function render() {
      renderSelectors();
      renderLocations();
      renderSessions();
      renderEvents();
    }

    function editLocation(id) {
      const location=(catalog().locations||[]).find(item=>Number(item.id)===Number(id));
      if(!location) return;
      clearRoomErrors();
      $('locationId').value=location.id;
      $('locationRoom').value=roomLabel(location);
      $('locationHeight').value=location.measurement_height_m??'';
      $('cancelRoomEdit').hidden=false;
      $('saveRoomButton').textContent=tr('update_room');
      $('locationRoom').focus();
    }

    function resetRoomForm() {
      const form=$('locationForm');
      if(form) form.reset();
      if($('locationId')) $('locationId').value='';
      if($('cancelRoomEdit')) $('cancelRoomEdit').hidden=true;
      if($('saveRoomButton')) $('saveRoomButton').textContent=tr('save_site');
      clearRoomErrors();
    }

    async function saveRoom(event) {
      event.preventDefault();
      clearRoomErrors();
      const roomInput=$('locationRoom'), heightInput=$('locationHeight'), idInput=$('locationId');
      const room=String(roomInput?.value??'').replace(/\s+/g,' ').trim();
      if(!room) {
        const message=tr('room_name_required');
        setFieldError('locationRoom','locationRoomError',message);
        roomInput?.focus();
        return;
      }
      if(room.length>120) {
        const message=tr('room_name_too_long');
        setFieldError('locationRoom','locationRoomError',message);
        roomInput?.focus();
        return;
      }
      const rawHeight=String(heightInput?.value??'').trim();
      const height=rawHeight===''?null:Number(rawHeight.replace(',','.'));
      if(height!==null && (!Number.isFinite(height)||height<0||height>10)) {
        const message=tr('measurement_height_range');
        setFieldError('locationHeight','locationHeightError',message);
        heightInput?.focus();
        return;
      }
      const id=String(idInput?.value??'').trim()||null;
      const payload={id,room,name:room,measurement_height_m:height};
      const fallback=new URLSearchParams({room});
      if(rawHeight) fallback.set('measurement_height_m',rawHeight.replace(',','.'));
      if(id) fallback.set('id',id);
      const button=$('saveRoomButton');
      if(button) {button.disabled=true;button.textContent=tr('saving_room');}
      setFormStatus('locationFormStatus',tr('saving_room'),'pending');
      try {
        const result=await api(`api/locations?${fallback.toString()}`,{
          method:'POST',
          headers:{
            'X-Radon-Room':encodeURIComponent(room),
            'X-Radon-Measurement-Height':rawHeight.replace(',','.'),
            ...(id?{'X-Radon-Location-Id':id}:{})
          },
          body:payload,
        });
        if(!result?.item?.id) throw new Error(tr('room_save_not_confirmed'));
        preferredRoomId=Number(result.item.id);
        const current=catalog();
        const index=(current.locations||[]).findIndex(item=>Number(item.id)===preferredRoomId);
        if(index>=0) current.locations[index]=result.item; else current.locations.push(result.item);
        toast(tr('room_saved'));
        resetRoomForm();
        setFormStatus('locationFormStatus',tr('room_saved'),'success');
        await deps.reloadCatalog();
        renderSelectors();
        if($('assignLocation')) $('assignLocation').value=String(preferredRoomId);
        $('assignTitle')?.focus();
        await deps.loadOverviewSelection(false);
      } catch(error) {
        const message=backendMessage(error);
        if(/room|raum/i.test(message)) setFieldError('locationRoom','locationRoomError',message);
        else if(/height|höhe|metre|meter/i.test(message)) setFieldError('locationHeight','locationHeightError',message);
        setFormStatus('locationFormStatus',message,'error');
        toast(message,true);
      } finally {
        if(button) {button.disabled=false;button.textContent=$('locationId')?.value?tr('update_room'):tr('save_site');}
      }
    }

    async function assignMeasurements(event) {
      event.preventDefault();
      clearAssignmentErrors();
      const location=$('assignLocation')?.value||'';
      const title=String($('assignTitle')?.value||'').trim();
      const startValue=$('assignStart')?.value||'';
      const endValue=$('assignEnd')?.value||'';
      if(!location) {setFieldError('assignLocation','assignLocationError',tr('assignment_room_required'));$('assignLocation')?.focus();return;}
      if(!title) {setFieldError('assignTitle','assignTitleError',tr('assignment_title_required'));$('assignTitle')?.focus();return;}
      if(!startValue) {setFieldError('assignStart','assignStartError',tr('assignment_start_required'));$('assignStart')?.focus();return;}
      if(endValue && new Date(endValue)<new Date(startValue)) {setFieldError('assignEnd','assignEndError',tr('assignment_end_after_start'));$('assignEnd')?.focus();return;}
      const button=$('assignButton');
      if(button) button.disabled=true;
      setFormStatus('assignFormStatus',tr('assigning_measurements'),'pending');
      try {
        const result=await api('api/locations/assign',{method:'POST',body:{
          device_id:$('assignDevice').value,
          location_id:location,
          title,
          start:toIso(startValue),
          end:toIso(endValue),
          purpose:$('assignPurpose').value,
          notes:$('assignNotes').value,
        }});
        preferredRoomId=Number(location);
        setFormStatus('assignFormStatus',`${tr('assigned')}: ${fmtInteger(result.assigned||0)}`,'success');
        toast(`${tr('assigned')}: ${fmtInteger(result.assigned||0)}`);
        event.currentTarget.reset();
        initializeDefaults();
        await deps.reloadCatalog();
        renderSelectors();
        if($('assignLocation')) $('assignLocation').value=String(preferredRoomId);
        await deps.loadAll();
      } catch(error) {
        const message=backendMessage(error);
        setFormStatus('assignFormStatus',message,'error');
        toast(message,true);
      } finally {
        if(button) button.disabled=(catalog().locations||[]).length===0;
      }
    }

    async function saveEvent(event) {
      event.preventDefault();
      const title=String($('eventTitle')?.value||'').trim();
      const occurred=$('eventTime')?.value||'';
      setFieldError('eventTitle','eventTitleError');
      setFieldError('eventTime','eventTimeError');
      setFormStatus('eventFormStatus');
      if(!occurred) {setFieldError('eventTime','eventTimeError',tr('event_time_required'));$('eventTime')?.focus();return;}
      if(!title) {setFieldError('eventTitle','eventTitleError',tr('event_title_required'));$('eventTitle')?.focus();return;}
      try {
        await api('api/events',{method:'POST',body:{event_type:$('eventType').value,occurred_at:toIso(occurred),location_id:$('eventLocation').value||null,title,notes:$('eventNotes').value}});
        setFormStatus('eventFormStatus',tr('saved'),'success');
        toast(tr('saved'));
        event.currentTarget.reset();
        $('eventTime').value=toInput(new Date());
        await deps.reloadCatalog();
      } catch(error) {
        const message=backendMessage(error);
        setFormStatus('eventFormStatus',message,'error');
        toast(message,true);
      }
    }

    function bind() {
      $('locationRoom')?.addEventListener('input',()=>setFieldError('locationRoom','locationRoomError'));
      $('locationHeight')?.addEventListener('input',()=>setFieldError('locationHeight','locationHeightError'));
      $('locationForm')?.addEventListener('submit',saveRoom);
      $('cancelRoomEdit')?.addEventListener('click',resetRoomForm);
      $('assignForm')?.addEventListener('submit',assignMeasurements);
      ['assignLocation','assignTitle','assignStart','assignEnd'].forEach(id=>$(id)?.addEventListener('input',()=>setFieldError(id,`${id}Error`)));
      $('eventForm')?.addEventListener('submit',saveEvent);
      $('eventTitle')?.addEventListener('input',()=>setFieldError('eventTitle','eventTitleError'));
      $('eventTime')?.addEventListener('input',()=>setFieldError('eventTime','eventTimeError'));
    }

    function initializeDefaults() {
      if($('eventTime')&&!$('eventTime').value) $('eventTime').value=toInput(new Date());
      if($('assignStart')&&!$('assignStart').value) $('assignStart').value=toInput(state()?.measurement?.completed_at||new Date());
      renderSelectors();
    }

    return {bind,render,initializeDefaults,resetRoomForm};
  }

  window.RMRoomsEvents={create};
})();
