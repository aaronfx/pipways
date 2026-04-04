/**
 * cms.js v2 — Core CMS Module (shell)
 * Tabs: Blog · LMS · Signals · Webinars · Users · Media · Limits · Settings
 *
 * Feature-specific methods are in separate modules:
 *   - cms_blog.js
 *   - cms_lms.js
 *   - cms_signals.js
 *   - cms_webinars.js
 *   - cms_users.js
 *   - cms_media.js
 *   - cms_settings.js
 */

// ── Standalone fetch helper ───────────────────────────────────────────────────
function _cmsReq(endpoint, opts) {
    opts = opts || {};
    var token = localStorage.getItem('pipways_token');
    var headers = Object.assign({'Content-Type': 'application/json'}, opts.headers || {});
    if (token) headers['Authorization'] = 'Bearer ' + token;
    if (opts.body instanceof FormData) delete headers['Content-Type'];
    return fetch(window.location.origin + endpoint, Object.assign({}, opts, {headers: headers}))
        .then(function(res) {
            if (res.status === 401) { localStorage.removeItem('pipways_token'); location.reload(); throw new Error('Session expired'); }
            return res.json().then(function(body) {
                if (!res.ok) throw new Error(body.detail || body.message || 'HTTP ' + res.status);
                return body;
            });
        });
}

// ── API extension ─────────────────────────────────────────────────────────────
API.cms = {
    uploadMedia:     (fd)        => { const t=localStorage.getItem('pipways_token'); return fetch(`${location.origin}/cms/media/upload`,{method:'POST',headers:{Authorization:`Bearer ${t}`},body:fd}).then(r=>r.ok?r.json():r.json().then(e=>{throw new Error(e.detail||'Upload failed')})); },
    listMedia:       (folder)    => _cmsReq(`/cms/media${folder?`?folder=${folder}`:''}`),
    deleteMedia:     (fn)        => _cmsReq(`/cms/media?filename=${encodeURIComponent(fn)}`,{method:'DELETE'}),
    listPosts:       ()          => _cmsReq('/cms/blog'),
    getPost:         (id)        => _cmsReq(`/cms/blog/${id}`),
    createPost:      (d)         => _cmsReq('/cms/blog',{method:'POST',body:JSON.stringify(d)}),
    updatePost:      (id,d)      => _cmsReq(`/cms/blog/${id}`,{method:'PUT',body:JSON.stringify(d)}),
    deletePost:      (id)        => _cmsReq(`/cms/blog/${id}`,{method:'DELETE'}),
    togglePost:      (id)        => _cmsReq(`/cms/blog/${id}/toggle-publish`,{method:'POST'}),
    seoScore:        (d)         => _cmsReq('/cms/blog/seo-score',{method:'POST',body:JSON.stringify(d)}),
    listCourses:     ()          => _cmsReq('/cms/courses'),
    createCourse:    (d)         => _cmsReq('/cms/courses',{method:'POST',body:JSON.stringify(d)}),
    updateCourse:    (id,d)      => _cmsReq(`/cms/courses/${id}`,{method:'PUT',body:JSON.stringify(d)}),
    deleteCourse:    (id)        => _cmsReq(`/cms/courses/${id}`,{method:'DELETE'}),
    toggleCourse:    (id)        => _cmsReq(`/cms/courses/${id}/toggle-publish`,{method:'POST'}),
    listModules:     (cid)       => _cmsReq(`/cms/courses/${cid}/modules`),
    createModule:    (d)         => _cmsReq('/cms/modules',{method:'POST',body:JSON.stringify(d)}),
    updateModule:    (id,d)      => _cmsReq(`/cms/modules/${id}`,{method:'PUT',body:JSON.stringify(d)}),
    deleteModule:    (id)        => _cmsReq(`/cms/modules/${id}`,{method:'DELETE'}),
    listLessons:     (mid)       => _cmsReq(`/cms/modules/${mid}/lessons`),
    createLesson:    (d)         => _cmsReq('/cms/lessons',{method:'POST',body:JSON.stringify(d)}),
    updateLesson:    (id,d)      => _cmsReq(`/cms/lessons/${id}`,{method:'PUT',body:JSON.stringify(d)}),
    deleteLesson:    (id)        => _cmsReq(`/cms/lessons/${id}`,{method:'DELETE'}),
    getQuiz:         (mid)       => _cmsReq(`/cms/modules/${mid}/quiz`),
    createQuiz:      (d)         => _cmsReq('/cms/quizzes',{method:'POST',body:JSON.stringify(d)}),
    updateQuiz:      (id,d)      => _cmsReq(`/cms/quizzes/${id}`,{method:'PUT',body:JSON.stringify(d)}),
    deleteQuiz:      (id)        => _cmsReq(`/cms/quizzes/${id}`,{method:'DELETE'}),
    createQuestion:  (d)         => _cmsReq('/cms/quiz-questions',{method:'POST',body:JSON.stringify(d)}),
    updateQuestion:  (id,d)      => _cmsReq(`/cms/quiz-questions/${id}`,{method:'PUT',body:JSON.stringify(d)}),
    deleteQuestion:  (id)        => _cmsReq(`/cms/quiz-questions/${id}`,{method:'DELETE'}),
    listSignals:     ()          => _cmsReq('/cms/signals'),
    createSignal:    (d)         => _cmsReq('/cms/signals',{method:'POST',body:JSON.stringify(d)}),
    updateSignal:    (id,d)      => _cmsReq(`/cms/signals/${id}`,{method:'PUT',body:JSON.stringify(d)}),
    deleteSignal:    (id)        => _cmsReq(`/cms/signals/${id}`,{method:'DELETE'}),
    closeSignal:     (id,o)      => _cmsReq(`/cms/signals/${id}/close?outcome=${o}`,{method:'POST'}),
    listWebinars:    ()          => _cmsReq('/cms/webinars'),
    createWebinar:   (d)         => _cmsReq('/cms/webinars',{method:'POST',body:JSON.stringify(d)}),
    updateWebinar:   (id,d)      => _cmsReq(`/cms/webinars/${id}`,{method:'PUT',body:JSON.stringify(d)}),
    deleteWebinar:   (id)        => _cmsReq(`/cms/webinars/${id}`,{method:'DELETE'}),
    toggleWebinar:   (id)        => _cmsReq(`/cms/webinars/${id}/toggle-publish`,{method:'POST'}),
    getRegistrants:  (id)        => _cmsReq(`/webinars/${id}/registrants`),
    listUsers:       (p,s,r,t)   => _cmsReq(`/cms/users?page=${p||1}&per_page=25${s?`&search=${encodeURIComponent(s)}`:''}`),
    setUserRole:     (id,role)   => _cmsReq(`/cms/users/${id}/role`,{method:'POST',body:JSON.stringify({role})}),
    setUserSub:      (id,tier)   => _cmsReq(`/cms/users/${id}/subscription`,{method:'POST',body:JSON.stringify({subscription_tier:tier})}),
    toggleUser:      (id)        => _cmsReq(`/cms/users/${id}/toggle-active`,{method:'POST'}),
    getUserActivity: (id)        => _cmsReq(`/cms/users/${id}/activity`),
    listAnnouncements:  ()       => _cmsReq('/cms/announcements'),
    createAnnouncement: (d)      => _cmsReq('/cms/announcements',{method:'POST',body:JSON.stringify(d)}),
    deleteAnnouncement: (id)     => _cmsReq(`/cms/announcements/${id}`,{method:'DELETE'}),
    toggleAnnouncement: (id)     => _cmsReq(`/cms/announcements/${id}/toggle`,{method:'POST'}),
    listCoupons:     ()          => _cmsReq('/cms/coupons'),
    createCoupon:    (d)         => _cmsReq('/cms/coupons',{method:'POST',body:JSON.stringify(d)}),
    deleteCoupon:    (id)        => _cmsReq(`/cms/coupons/${id}`,{method:'DELETE'}),
    toggleCoupon:    (id)        => _cmsReq(`/cms/coupons/${id}/toggle`,{method:'POST'}),
    getSettings:     ()          => _cmsReq('/cms/settings'),
    saveSettings:    (d)         => _cmsReq('/cms/settings',{method:'PUT',body:JSON.stringify(d)}),
};

// ── CMSPage ───────────────────────────────────────────────────────────────────
const CMSPage = {
    _container: null,
    _activeTab: 'blog',
    _editingId: null,
    _lmsState: { courseId:null, moduleId:null, quizId:null },
    _quill: null,
    _usersPage: 1,
    _usersSearch: '',
    _mediaCallback: null,

    // ────────────────────────────────────────────────────────────────────────
    // HELPER METHODS
    // ────────────────────────────────────────────────────────────────────────

    _e(s){ return s==null?'':String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); },
    _d(s){ if(!s)return'—'; try{return new Date(s).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});}catch(_){return s;} },
    _dt(s){ if(!s)return''; try{return new Date(s).toISOString().slice(0,16);}catch(_){return'';} },
    _pub(on,a='Published',b='Draft'){ const c=on?'rgba(16,185,129,.15)':'rgba(107,114,128,.15)',t=on?'#34d399':'#9ca3af',br=on?'rgba(16,185,129,.3)':'rgba(107,114,128,.3)'; return `<span style="background:${c};color:${t};border:1px solid ${br};padding:.15rem .55rem;border-radius:9999px;font-size:.7rem;font-weight:700;">${on?a:b}</span>`; },
    _role(r){ const m={'admin':'rgba(239,68,68,.15)','moderator':'rgba(245,158,11,.15)','user':'rgba(107,114,128,.15)'}; const t={'admin':'#f87171','moderator':'#fbbf24','user':'#9ca3af'}; const k=r||'user'; return `<span style="background:${m[k]||m.user};color:${t[k]||t.user};border:1px solid ${t[k]||t.user}44;padding:.15rem .55rem;border-radius:9999px;font-size:.7rem;font-weight:700;">${k}</span>`; },
    _tier(s){ const m={'pro':'rgba(124,58,237,.15)','enterprise':'rgba(245,158,11,.15)','free':'rgba(107,114,128,.15)'}; const t={'pro':'#a78bfa','enterprise':'#fbbf24','free':'#9ca3af'}; const k=s||'free'; return `<span style="background:${m[k]||m.free};color:${t[k]||t.free};border:1px solid ${t[k]||t.free}55;padding:.15rem .55rem;border-radius:9999px;font-size:.7rem;font-weight:700;">${k}</span>`; },
    _dir(d){ const u=(d||'').toUpperCase()==='BUY'; return `<span style="background:${u?'rgba(16,185,129,.15)':'rgba(239,68,68,.15)'};color:${u?'#34d399':'#f87171'};border:1px solid ${u?'rgba(16,185,129,.3)':'rgba(239,68,68,.3)'};padding:.15rem .55rem;border-radius:9999px;font-size:.7rem;font-weight:700;">${d||'—'}</span>`; },

    _toast(msg,type='success'){
        const d=document.createElement('div');
        d.style.cssText=`position:fixed;bottom:1.5rem;right:1.5rem;z-index:99999;padding:.75rem 1.25rem;border-radius:.75rem;font-size:.85rem;font-weight:600;color:white;max-width:340px;background:${type==='success'?'rgba(16,185,129,.95)':type==='error'?'rgba(239,68,68,.95)':type==='warning'?'rgba(245,158,11,.95)':'rgba(59,130,246,.95)'};box-shadow:0 8px 24px rgba(0,0,0,.4);`;
        d.textContent=msg; document.body.appendChild(d); setTimeout(()=>d.remove(),3500);
    },

    // ────────────────────────────────────────────────────────────────────────
    // CORE RENDERER
    // ────────────────────────────────────────────────────────────────────────

    async render(container){
        if(!container) return;
        this._container=container;
        container.innerHTML=this._shell();
        this._setupTabs();
        this._injectStyles();
        await this._loadTab(this._activeTab);
    },

    _injectStyles(){
        if(document.getElementById('cms-styles')) return;
        const s=document.createElement('style');
        s.id='cms-styles';
        s.textContent=`
        .cms-tab{padding:.45rem 1rem;border-radius:.6rem;font-size:.82rem;font-weight:600;border:none;cursor:pointer;color:#9ca3af;background:transparent;transition:all .18s;white-space:nowrap;}
        .cms-tab.active{background:linear-gradient(135deg,#7c3aed,#6d28d9);color:white;box-shadow:0 4px 12px rgba(124,58,237,.35);}
        .cms-tab:not(.active):hover{background:#374151;color:white;}
        .cms-pane{display:none;}.cms-pane.visible{display:block;}
        .cms-tbl{width:100%;border-collapse:collapse;}
        .cms-tbl th{padding:.6rem .85rem;text-align:left;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#6b7280;background:#111827;}
        .cms-tbl td{padding:.6rem .85rem;font-size:.82rem;border-bottom:1px solid #1f2937;vertical-align:middle;}
        .cms-tbl tr:hover td{background:rgba(124,58,237,.04);}
        .cb{display:inline-flex;align-items:center;gap:.35rem;padding:.35rem .85rem;border-radius:.5rem;font-size:.78rem;font-weight:600;border:none;cursor:pointer;transition:all .18s;}
        .cb-p{background:linear-gradient(135deg,#7c3aed,#6d28d9);color:white;} .cb-p:hover{opacity:.9;transform:translateY(-1px);}
        .cb-g{background:#374151;color:#d1d5db;border:1px solid #4b5563;} .cb-g:hover{background:#4b5563;color:white;}
        .cb-r{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3);} .cb-r:hover{background:rgba(239,68,68,.3);}
        .cb-gr{background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.3);} .cb-gr:hover{background:rgba(16,185,129,.3);}
        .cb-y{background:rgba(245,158,11,.15);color:#fbbf24;border:1px solid rgba(245,158,11,.3);} .cb-y:hover{background:rgba(245,158,11,.3);}
        .ci{width:100%;background:#111827;border:1px solid #374151;border-radius:.5rem;padding:.5rem .75rem;color:white;font-size:.875rem;box-sizing:border-box;}
        .ci:focus{outline:none;border-color:#7c3aed;}
        .cta{width:100%;background:#111827;border:1px solid #374151;border-radius:.5rem;padding:.5rem .75rem;color:white;font-size:.875rem;box-sizing:border-box;resize:vertical;min-height:120px;}
        .cta:focus{outline:none;border-color:#7c3aed;}
        .cs{width:100%;background:#111827;border:1px solid #374151;border-radius:.5rem;padding:.5rem .75rem;color:white;font-size:.875rem;box-sizing:border-box;}
        .cs:focus{outline:none;border-color:#7c3aed;}
        .cl{display:block;font-size:.78rem;color:#9ca3af;margin-bottom:.35rem;font-weight:500;}
        .ccard{background:#1f2937;border:1px solid #374151;border-radius:.75rem;padding:1.25rem;margin-bottom:1rem;}
        .chdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;padding-bottom:.75rem;border-bottom:1px solid #374151;}
        .crow{display:grid;gap:.75rem;margin-bottom:.75rem;}
        .crow2{grid-template-columns:1fr 1fr;}
        .crow3{grid-template-columns:1fr 1fr 1fr;}
        .ctog{display:flex;align-items:center;gap:.5rem;cursor:pointer;}
        .ttrack{width:40px;height:22px;border-radius:11px;background:#374151;position:relative;transition:background .2s;}
        .ttrack.on{background:#7c3aed;}
        .tthumb{width:16px;height:16px;border-radius:50%;background:white;position:absolute;top:3px;left:3px;transition:left .2s;}
        .ttrack.on .tthumb{left:21px;}
        .seo-ring{width:80px;height:80px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:800;flex-shrink:0;}
        .seo-check{display:flex;align-items:center;gap:.5rem;padding:.4rem .6rem;border-radius:.4rem;font-size:.8rem;margin-bottom:.35rem;}
        .media-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:.75rem;margin-top:.75rem;}
        .media-item{background:#111827;border:2px solid #374151;border-radius:.5rem;overflow:hidden;cursor:pointer;transition:border-color .15s;}
        .media-item:hover,.media-item.selected{border-color:#7c3aed;}
        .media-thumb{width:100%;height:90px;object-fit:cover;display:block;background:#1f2937;}
        .media-name{font-size:.68rem;color:#9ca3af;padding:.3rem .4rem;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;}
        .upload-zone{border:2px dashed #374151;border-radius:.75rem;padding:2rem;text-align:center;cursor:pointer;transition:all .2s;}
        .upload-zone.drag-over,.upload-zone:hover{border-color:#7c3aed;background:rgba(124,58,237,.05);}
        .lms-module{background:#1a2235;border:1px solid #2a3550;border-radius:.65rem;margin-bottom:.75rem;overflow:hidden;}
        .lms-module-header{display:flex;align-items:center;gap:.75rem;padding:.75rem 1rem;cursor:pointer;background:#1f2937;}
        .lms-module-header:hover{background:#263347;}
        .lms-lesson{display:flex;align-items:center;gap:.75rem;padding:.6rem 1rem .6rem 2.5rem;border-top:1px solid #1a2235;font-size:.82rem;}
        .lms-lesson:hover{background:rgba(124,58,237,.04);}
        .quiz-q{background:#111827;border:1px solid #2a3550;border-radius:.5rem;padding:.85rem;margin-bottom:.65rem;}
        .sg{background:#1f2937;border:1px solid #374151;border-radius:.75rem;overflow:hidden;margin-bottom:1rem;}
        .sg-hdr{padding:.75rem 1rem;background:#111827;font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#6b7280;}
        .sg-row{display:flex;align-items:center;justify-content:space-between;padding:.75rem 1rem;border-bottom:1px solid #1f2937;gap:1rem;}
        .sg-row:last-child{border-bottom:none;}
        .sg-lbl{font-size:.85rem;color:#e5e7eb;font-weight:500;min-width:180px;}
        .sg-desc{font-size:.75rem;color:#6b7280;margin-top:.1rem;}
        `;
        document.head.appendChild(s);
    },

    _shell(){
        const tabs=[
            {id:'blog',    icon:'fa-newspaper',    label:'Blog'},
            {id:'lms',     icon:'fa-graduation-cap',label:'LMS'},
            {id:'signals', icon:'fa-satellite-dish',label:'Signals'},
            {id:'webinars',icon:'fa-video',         label:'Webinars'},
            {id:'users',   icon:'fa-users',         label:'Users'},
            {id:'media',   icon:'fa-photo-video',   label:'Media'},
            {id:'limits',  icon:'fa-sliders-h',     label:'Feature Limits'},
            {id:'settings',icon:'fa-cog',           label:'Settings'},
        ];
        return `
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-5">
            <div>
                <h2 class="text-2xl font-bold text-white flex items-center gap-2">
                    <i class="fas fa-layer-group text-purple-400"></i> Content Management
                </h2>
                <p class="text-sm text-gray-500 mt-0.5">Blog · LMS · Signals · Webinars · Users · Media · Limits · Settings</p>
            </div>
        </div>
        <div class="flex gap-1 mb-5 p-1 rounded-xl bg-gray-800/60 border border-gray-700 flex-wrap">
            ${tabs.map(t=>`<button class="cms-tab${t.id===this._activeTab?' active':''}" data-tab="${t.id}">
                <i class="fas ${t.icon} mr-1.5"></i>${t.label}
            </button>`).join('')}
        </div>
        ${tabs.map(t=>`<div id="cms-pane-${t.id}" class="cms-pane${t.id===this._activeTab?' visible':''}"></div>`).join('')}`;
    },

    _setupTabs(){
        document.querySelectorAll('.cms-tab').forEach(b=>{
            b.addEventListener('click', async ()=>{
                document.querySelectorAll('.cms-tab').forEach(x=>x.classList.remove('active'));
                document.querySelectorAll('.cms-pane').forEach(x=>x.classList.remove('visible'));
                b.classList.add('active');
                this._activeTab=b.dataset.tab;
                document.getElementById(`cms-pane-${b.dataset.tab}`)?.classList.add('visible');
                await this._loadTab(b.dataset.tab);
            });
        });
    },

    async _loadTab(tab){
        const map={blog:()=>this._blog(),lms:()=>this._lms(),signals:()=>this._signals(),
                   webinars:()=>this._webinars(),users:()=>this._users(),
                   media:()=>this._media(),limits:()=>this._limits(),settings:()=>this._settings()};
        if(map[tab]) await map[tab]();
    },
};
