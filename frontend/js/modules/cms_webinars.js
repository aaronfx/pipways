// CMS Module: WEBINARS
// Extracted from cms.js for maintainability

Object.assign(CMSPage, {
    async _webinars(){
    const pane=document.getElementById('cms-pane-webinars'); if(!pane) return;
    let ws=[]; try{ws=await API.cms.listWebinars();}catch(e){this._toast('Failed to load webinars: '+e.message,'error');}
    const regCounts={};
    await Promise.all(ws.map(async w=>{
        try{const r=await API.cms.getRegistrants(w.id);regCounts[w.id]=r.count||0;}catch(_){regCounts[w.id]=0;}
    }));
    pane.innerHTML=`
    <div class="chdr">
        <h3 class="text-white font-semibold flex items-center gap-2"><i class="fas fa-video text-pink-400"></i> Webinars <span class="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">${ws.length}</span></h3>
        <button class="cb cb-p" onclick="CMSPage._webinarForm()"><i class="fas fa-plus"></i> New Webinar</button>
    </div>
    <div id="cms-web-form" style="display:none;" class="ccard mb-4"></div>
    <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <div class="overflow-x-auto"><table class="cms-tbl">
            <thead><tr><th>ID</th><th>Title</th><th>Presenter</th><th>Date</th><th>Duration</th><th>Status</th><th>Registered</th><th>Capacity</th><th class="text-right">Actions</th></tr></thead>
            <tbody>${ws.length?ws.map(w=>`<tr>
                <td><span style="background:rgba(124,58,237,.15);color:#a78bfa;border:1px solid rgba(124,58,237,.3);padding:.15rem .5rem;border-radius:.35rem;font-size:.7rem;font-weight:700;font-family:monospace;">#${w.id}</span></td>
                <td><div class="text-white font-medium text-sm">${this._e(w.title)}</div>
                    ${w.meeting_link?`<a href="${this._e(w.meeting_link)}" target="_blank" class="text-purple-400 text-xs hover:underline">🔗 Join</a>`:''}</td>
                <td class="text-gray-400">${this._e(w.presenter||'—')}</td>
                <td class="text-gray-300">${this._d(w.scheduled_at)}</td>
                <td class="text-gray-400">${w.duration_minutes||60}m</td>
                <td>${this._pub(w.is_published)}</td>
                <td><button class="cb cb-g" style="font-size:.72rem;padding:.25rem .65rem;" onclick="CMSPage._webinarRegistrants(${w.id},this.dataset.title)" data-title="${this._e(w.title)}">
                    <i class="fas fa-users mr-1"></i>${regCounts[w.id]||0}
                </button></td>
                <td class="text-gray-400">${w.max_attendees||100}</td>
                <td class="text-right"><div style="display:flex;gap:.3rem;justify-content:flex-end;">
                    <button class="cb cb-g" onclick="CMSPage._webinarForm(${JSON.stringify(w).replace(/"/g,'&quot;')})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="cb ${w.is_published?'cb-g':'cb-gr'}" onclick="CMSPage._toggleWebinar(${w.id})">${w.is_published?'Unpublish':'Publish'}</button>
                    <button class="cb cb-r" onclick="CMSPage._deleteWebinar(${w.id})"><i class="fas fa-trash"></i></button>
                </div></td>
            </tr>`).join(''):`<tr><td colspan="9" class="text-center py-8 text-gray-500 text-sm">No webinars yet</td></tr>`}
            </tbody>
        </table></div>
    </div>`;
},_webinarForm(d=null){
    const isEdit=d&&d.id; this._editingId=isEdit?d.id:null;
    d=d||{title:'',description:'',presenter:'',speaker_bio:'',scheduled_at:'',
           duration_minutes:60,meeting_link:'',youtube_url:'',embed_url:'',
           recording_url:'',max_attendees:100,tags:'',is_published:false};
    const f=document.getElementById('cms-web-form'); if(!f) return;
    f.style.display='block';
    f.innerHTML=`
    <div class="chdr">
        <h4 class="text-white font-semibold">${isEdit?'Edit Webinar':'New Webinar'}</h4>
        <button class="cb cb-g" onclick="CMSPage._closeWebinarForm()"><i class="fas fa-times"></i></button>
    </div>
    <div class="crow crow2">
        <div><label class="cl">Title *</label><input class="ci" id="wf-title" value="${this._e(d.title)}" placeholder="Webinar title"></div>
        <div><label class="cl">Presenter</label><input class="ci" id="wf-presenter" value="${this._e(d.presenter)}" placeholder="Host name"></div>
    </div>
    <div class="crow crow2">
        <div><label class="cl">Scheduled Date &amp; Time *</label><input type="datetime-local" class="ci" id="wf-date" value="${this._dt(d.scheduled_at)}"></div>
        <div><label class="cl">Duration (minutes)</label><input type="number" class="ci" id="wf-dur" value="${d.duration_minutes||60}" min="15" max="480"></div>
    </div>
    <div class="crow"><div><label class="cl">Description</label><textarea class="cta" id="wf-desc" style="min-height:70px;">${this._e(d.description)}</textarea></div></div>
    <div class="crow"><div><label class="cl">Speaker Bio</label><textarea class="cta" id="wf-bio" style="min-height:55px;">${this._e(d.speaker_bio)}</textarea></div></div>
    <div class="crow crow2">
        <div><label class="cl">Zoom / Meeting Link</label><input class="ci" id="wf-link" value="${this._e(d.meeting_link)}" placeholder="https://zoom.us/j/..."></div>
        <div><label class="cl">Max Attendees</label><input type="number" class="ci" id="wf-max" value="${d.max_attendees||100}" min="1"></div>
    </div>
    <div class="crow crow2">
        <div><label class="cl">YouTube URL (live stream)</label><input class="ci" id="wf-yt" value="${this._e(d.youtube_url)}" placeholder="https://youtube.com/watch?v=..."></div>
        <div><label class="cl">Embed URL</label><input class="ci" id="wf-embed" value="${this._e(d.embed_url)}" placeholder="https://..."></div>
    </div>
    <div class="crow crow2">
        <div><label class="cl">Recording URL (post-event)</label><input class="ci" id="wf-rec" value="${this._e(d.recording_url)}" placeholder="YouTube or video URL"></div>
        <div><label class="cl">Tags (comma-separated)</label><input class="ci" id="wf-tags" value="${this._e(Array.isArray(d.tags)?d.tags.join(', '):d.tags||'')}" placeholder="SMC, forex, live"></div>
    </div>
    <div style="display:flex;align-items:center;gap:1.5rem;margin-top:.5rem;flex-wrap:wrap;">
        <label class="ctog" onclick="CMSPage._togCheck('wf-pub')">
            <div class="ttrack${d.is_published?' on':''}"><div class="tthumb"></div></div>
            <span class="text-sm text-gray-300">Published</span>
            <input type="hidden" id="wf-pub" value="${d.is_published?'1':'0'}">
        </label>
        <button class="cb cb-p" onclick="CMSPage._saveWebinar()"><i class="fas fa-save"></i> ${isEdit?'Update':'Create'} Webinar</button>
        <button class="cb cb-g" onclick="CMSPage._closeWebinarForm()">Cancel</button>
    </div>`;
    f.scrollIntoView({behavior:'smooth',block:'start'});
},
_closeWebinarForm(){
    const f=document.getElementById('cms-web-form');
    if(f){f.style.display='none';f.innerHTML='';} this._editingId=null;
},
async _saveWebinar(){
    const title=document.getElementById('wf-title')?.value.trim();
    const date=document.getElementById('wf-date')?.value;
    if(!title||!date){this._toast('Title and date required','error');return;}
    const tagsRaw=document.getElementById('wf-tags')?.value||'';
    const p={
        title,
        description:      document.getElementById('wf-desc')?.value||'',
        presenter:        document.getElementById('wf-presenter')?.value||'',
        speaker_bio:      document.getElementById('wf-bio')?.value||'',
        scheduled_at:     date,
        duration_minutes: parseInt(document.getElementById('wf-dur')?.value)||60,
        meeting_link:     document.getElementById('wf-link')?.value||'',
        youtube_url:      document.getElementById('wf-yt')?.value||'',
        embed_url:        document.getElementById('wf-embed')?.value||'',
        recording_url:    document.getElementById('wf-rec')?.value||'',
        max_attendees:    parseInt(document.getElementById('wf-max')?.value)||100,
        tags:             tagsRaw.split(',').map(t=>t.trim()).filter(Boolean).join(','),
        is_published:     document.getElementById('wf-pub')?.value==='1',
    };
    try{
        if(this._editingId){await API.cms.updateWebinar(this._editingId,p);this._toast('Webinar updated');}
        else{await API.cms.createWebinar(p);this._toast('Webinar created');}
        this._closeWebinarForm(); await this._webinars();
    }catch(e){this._toast(e.message,'error');}
},async _toggleWebinar(id){ try{const r=await API.cms.toggleWebinar(id);this._toast(r.message);await this._webinars();}catch(e){this._toast(e.message,'error');} },async _deleteWebinar(id){ if(!confirm('Delete webinar?'))return; try{await API.cms.deleteWebinar(id);this._toast('Deleted');await this._webinars();}catch(e){this._toast(e.message,'error');} },
async _webinarRegistrants(id,title){
    const existing=document.getElementById('cms-reg-modal'); if(existing) existing.remove();
    const modal=document.createElement('div');
    modal.id='cms-reg-modal';
    modal.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;display:flex;align-items:center;justify-content:center;padding:1rem;';
    modal.innerHTML=`
    <div style="background:#1f2937;border:1px solid #374151;border-radius:.75rem;width:min(640px,96vw);max-height:85vh;display:flex;flex-direction:column;overflow:hidden;">
        <div class="chdr" style="padding:1rem 1.25rem;flex-shrink:0;">
            <div><h4 class="text-white font-semibold flex items-center gap-2"><i class="fas fa-users text-purple-400"></i> Registrants</h4>
            <p class="text-xs text-gray-500 mt-0.5">${this._e(title||'')}</p></div>
            <button class="cb cb-g" onclick="CMSPage._closeRegModal()"><i class="fas fa-times"></i></button>
        </div>
        <div id="cms-reg-body" style="overflow-y:auto;padding:1rem 1.25rem;flex:1;">
            <div class="text-gray-400 text-sm text-center py-8"><i class="fas fa-spinner fa-spin mr-2"></i>Loading registrants…</div>
        </div>
    </div>`;
    document.body.appendChild(modal);
    modal.addEventListener('click',e=>{if(e.target===modal) CMSPage._closeRegModal();});
    try{
        const r=await API.cms.getRegistrants(id);
        const body=document.getElementById('cms-reg-body'); if(!body) return;
        if(!r.count){body.innerHTML=`<div class="text-center py-10 text-gray-500"><i class="fas fa-user-slash text-2xl block mb-2 opacity-30"></i>No registrants yet</div>`;return;}
        body.innerHTML=`
        <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-semibold text-white">${r.count} registrant${r.count!==1?'s':''}</span>
        </div>
        <div class="bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
            <table class="cms-tbl">
                <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Registered At</th></tr></thead>
                <tbody>${r.registrants.map((reg,i)=>`<tr>
                    <td class="text-gray-600 text-xs">${i+1}</td>
                    <td class="text-white text-sm">${this._e(reg.full_name||'—')}</td>
                    <td class="text-gray-400 text-xs font-mono">${this._e(reg.email)}</td>
                    <td class="text-gray-500 text-xs">${this._d(reg.registered_at)}</td>
                </tr>`).join('')}</tbody>
            </table>
        </div>`;
    }catch(e){
        const body=document.getElementById('cms-reg-body');
        if(body) body.innerHTML=`<div class="text-red-400 text-sm text-center py-8">${this._e(e.message)}</div>`;
    }
},
_closeRegModal(){ const m=document.getElementById('cms-reg-modal'); if(m) m.remove(); },
});
