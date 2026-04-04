/**
 * cms.js v2 — Full CMS Module
 * Tabs: Blog · LMS · Signals · Webinars · Users · Media · Settings
 *
 * FIXES APPLIED:
 *   1. window.quill exposed after Quill init (enables HTML paste patch)
 *   2. _webinarForm() + _closeWebinarForm() + _saveWebinar() added (were missing — broke New/Edit Webinar)
 *   3. _restoreDraft() added (was missing — broke autosave draft restore banner)
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

    // ═══════════════════════════════════════════════════════════════════════
    // BLOG
    // ═══════════════════════════════════════════════════════════════════════
    async _blog(){
        const pane=document.getElementById('cms-pane-blog'); if(!pane) return;
        let posts=[]; try{posts=await API.cms.listPosts();}catch(e){this._toast('Failed to load posts: '+e.message,'error');}
        pane.innerHTML=`
        <div class="chdr">
            <h3 class="text-white font-semibold flex items-center gap-2">
                <i class="fas fa-newspaper text-blue-400"></i> Blog Posts
                <span class="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">${posts.length}</span>
            </h3>
            <button class="cb cb-p" onclick="CMSPage._blogForm()"><i class="fas fa-plus"></i> New Post</button>
        </div>
        <div id="cms-blog-form" style="display:none;" class="ccard mb-4"></div>
        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="cms-tbl">
                    <thead><tr><th>Title</th><th>Category</th><th>SEO</th><th>Status</th><th>Views</th><th>Created</th><th class="text-right">Actions</th></tr></thead>
                    <tbody>
                        ${posts.length?posts.map(p=>`<tr>
                            <td><div class="text-white font-medium text-sm">${this._e(p.title)}</div>
                                <div class="text-gray-600 text-xs font-mono">/${this._e(p.slug)}</div></td>
                            <td class="text-gray-400">${this._e(p.category||'General')}</td>
                            <td>${p.focus_keyword?`<span class="text-xs text-green-400"><i class="fas fa-check-circle mr-1"></i>Set</span>`:`<span class="text-xs text-gray-600">—</span>`}</td>
                            <td>${this._pub(p.is_published)}</td>
                            <td class="text-gray-400">${p.views||0}</td>
                            <td class="text-gray-500">${this._d(p.created_at)}</td>
                            <td class="text-right">
                                <div style="display:flex;gap:.3rem;justify-content:flex-end;">
                                    <button class="cb cb-g" onclick="CMSPage._blogForm(${p.id})"><i class="fas fa-edit"></i></button>
                                    <button class="cb ${p.is_published?'cb-g':'cb-gr'}" onclick="CMSPage._togglePost(${p.id})">${p.is_published?'Unpublish':'Publish'}</button>
                                    <button class="cb cb-r" onclick="CMSPage._deletePost(${p.id})"><i class="fas fa-trash"></i></button>
                                </div>
                            </td>
                        </tr>`).join('')
                        :`<tr><td colspan="7" class="text-center py-10 text-gray-500 text-sm"><i class="fas fa-newspaper text-2xl block mb-2 opacity-30"></i>No posts yet</td></tr>`}
                    </tbody>
                </table>
            </div>
        </div>`;
    },

    async _blogForm(id=null){
        this._editingId=id;
        let d={title:'',slug:'',excerpt:'',content:'',category:'General',tags:'',featured_image:'',seo_title:'',seo_description:'',focus_keyword:'',is_published:false};
        if(id){ try{d=await API.cms.getPost(id); d.tags=(d.tags||[]).join(', ');}catch(_){} }
        const f=document.getElementById('cms-blog-form'); if(!f) return;
        f.style.display='block';
        f.innerHTML=`
        <div class="chdr">
            <h4 class="text-white font-semibold">${id?'Edit Post':'New Post'}</h4>
            <div class="flex gap-2">
                <button class="cb cb-y" onclick="CMSPage._runSEO()"><i class="fas fa-chart-line"></i> SEO Score</button>
                <button class="cb cb-g" onclick="CMSPage._closeBlogForm()"><i class="fas fa-times"></i></button>
            </div>
        </div>
        <div class="crow crow2">
            <div><label class="cl">Title *</label><input class="ci" id="bf-title" value="${this._e(d.title)}" placeholder="Post title…"></div>
            <div><label class="cl">Slug *</label><input class="ci" id="bf-slug" value="${this._e(d.slug)}" placeholder="url-slug"></div>
        </div>
        <div class="crow crow2">
            <div><label class="cl">Category</label>
                <select class="cs" id="bf-cat">${['General','Strategy','Analysis','Psychology','Risk Management','SMC','Forex','Crypto','Indices'].map(c=>`<option value="${c}"${d.category===c?' selected':''}>${c}</option>`).join('')}</select></div>
            <div><label class="cl">Tags (comma-separated)</label><input class="ci" id="bf-tags" value="${this._e(Array.isArray(d.tags)?d.tags.join(', '):d.tags)}" placeholder="forex, smc, strategy"></div>
        </div>
        <div class="crow">
            <div><label class="cl">Excerpt / Meta Description</label>
                <textarea class="cta" id="bf-excerpt" style="min-height:60px;">${this._e(d.excerpt)}</textarea>
                <span id="bf-excerpt-count" class="text-xs text-gray-600"></span>
            </div>
        </div>
        <div class="crow crow2">
            <div>
                <label class="cl">Featured Image URL</label>
                <div style="display:flex;gap:.5rem;">
                    <input class="ci" id="bf-img" value="${this._e(d.featured_image)}" placeholder="https:// or pick from media…">
                    <button class="cb cb-g" style="white-space:nowrap;" onclick="CMSPage._pickMedia('bf-img')"><i class="fas fa-images"></i></button>
                </div>
                <div id="bf-img-preview" style="margin-top:.5rem;${d.featured_image?'':'display:none;'}">
                    <img src="${this._e(d.featured_image)}" style="max-height:200px;width:100%;object-fit:cover;border-radius:.5rem;border:1px solid #374151;">
                </div>
            </div>
            <div><label class="cl">Focus Keyword</label>
                <input class="ci" id="bf-kw" value="${this._e(d.focus_keyword)}" placeholder="e.g. forex trading strategy"></div>
        </div>
        <div class="crow crow2" style="background:#0d1117;border:1px solid #1f2937;border-radius:.5rem;padding:.75rem;">
            <div><label class="cl" style="color:#a78bfa;"><i class="fas fa-search mr-1"></i>SEO Title</label>
                <input class="ci" id="bf-stitle" value="${this._e(d.seo_title)}" placeholder="Overrides title in search results">
                <span id="bf-stitle-count" class="text-xs text-gray-600"></span>
            </div>
            <div><label class="cl" style="color:#a78bfa;"><i class="fas fa-search mr-1"></i>SEO Description</label>
                <input class="ci" id="bf-sdesc" value="${this._e(d.seo_description)}" placeholder="160 char search snippet">
                <span id="bf-sdesc-count" class="text-xs text-gray-600"></span>
            </div>
        </div>
        <div class="crow">
            <div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.35rem;">
                    <label class="cl" style="margin:0;">Content *</label>
                    <span class="flex items-center gap-2">
                        <span id="bf-wc" class="text-xs text-gray-600"></span>
                        <span style="color:#374151;">·</span>
                        <span id="bf-cc" class="text-xs text-gray-600"></span>
                    </span>
                </div>
                <div id="bf-editor-wrap" style="border:1px solid #374151;border-radius:.5rem;overflow:hidden;background:#111827;">
                    <div id="bf-editor" style="min-height:320px;font-size:.9rem;"></div>
                </div>
                <input type="hidden" id="bf-content">
            </div>
        </div>
        <div id="cms-seo-panel" style="display:none;" class="ccard"></div>
        <div style="display:flex;align-items:center;gap:1.5rem;margin-top:.5rem;flex-wrap:wrap;">
            <div>
                <label class="cl">Status</label>
                <div style="display:flex;border:1px solid #374151;border-radius:.5rem;overflow:hidden;">
                    <button type="button" id="bf-status-draft"
                            onclick="CMSPage._setPostStatus('draft')"
                            style="padding:.4rem 1.1rem;font-size:.8rem;font-weight:600;cursor:pointer;border:none;transition:all .15s;
                                   background:${!d.is_published?'#4b5563':'#1f2937'};
                                   color:${!d.is_published?'white':'#9ca3af'};">
                        📄 Draft
                    </button>
                    <button type="button" id="bf-status-published"
                            onclick="CMSPage._setPostStatus('published')"
                            style="padding:.4rem 1.1rem;font-size:.8rem;font-weight:600;cursor:pointer;border:none;border-left:1px solid #374151;transition:all .15s;
                                   background:${d.is_published?'#7c3aed':'#1f2937'};
                                   color:${d.is_published?'white':'#9ca3af'};">
                        🌐 Published
                    </button>
                </div>
                <input type="hidden" id="bf-pub" value="${d.is_published?'1':'0'}">
            </div>
            <button class="cb cb-p" onclick="CMSPage._savePost()" style="align-self:flex-end;margin-bottom:.1rem;">
                <i class="fas fa-save"></i> ${id?'Update Post':'Save Post'}
            </button>
        </div>`;

        f.scrollIntoView({behavior:'smooth',block:'start'});

        // ── Initialise Quill ──────────────────────────────────────────────
        this._quill = null;

        if (typeof Quill === 'undefined') {
            const wrap = document.getElementById('bf-editor-wrap');
            if (wrap) {
                wrap.innerHTML = '<textarea class="cta" id="bf-editor-fallback" style="border-radius:0;border:none;min-height:320px;width:100%;padding:.75rem;background:#111827;color:white;">'
                    + (d.content || '') + '</textarea>';
                const fb = document.getElementById('bf-editor-fallback');
                if (fb) {
                    const sync = () => { const hi = document.getElementById('bf-content'); if (hi) hi.value = fb.value; };
                    fb.addEventListener('input', sync); sync();
                }
            }
        } else {
            if (!document.getElementById('quill-dark-style')) {
                const st = document.createElement('style');
                st.id = 'quill-dark-style';
                st.textContent = `
                    #bf-editor-wrap .ql-toolbar.ql-snow {
                        background:#1f2937; border:none; border-bottom:1px solid #374151;
                        padding:.4rem .6rem; flex-wrap:wrap; border-radius:.5rem .5rem 0 0;
                    }
                    #bf-editor-wrap .ql-container.ql-snow,
                    #bf-editor-wrap .ql-editor { border-radius:0 0 .5rem .5rem; }
                    #bf-editor-wrap .ql-toolbar.ql-snow .ql-stroke { stroke:#9ca3af; }
                    #bf-editor-wrap .ql-toolbar.ql-snow .ql-fill   { fill:#9ca3af; }
                    #bf-editor-wrap .ql-toolbar.ql-snow button:hover .ql-stroke { stroke:#a78bfa; }
                    #bf-editor-wrap .ql-toolbar.ql-snow button.ql-active .ql-stroke { stroke:#a78bfa; }
                    #bf-editor-wrap .ql-toolbar.ql-snow .ql-picker { color:#9ca3af; }
                    #bf-editor-wrap .ql-toolbar.ql-snow .ql-picker-options {
                        background:#1f2937; border:1px solid #374151; border-radius:.4rem;
                    }
                    #bf-editor-wrap .ql-toolbar.ql-snow .ql-picker-item { color:#d1d5db; }
                    #bf-editor-wrap .ql-container.ql-snow {
                        border:none; background:#111827; color:#e5e7eb; font-family:inherit;
                    }
                    #bf-editor-wrap .ql-editor { min-height:320px; font-size:.9rem; line-height:1.7; padding:.85rem 1rem; }
                    #bf-editor-wrap .ql-editor.ql-blank::before { color:#6b7280; font-style:normal; }
                    #bf-editor-wrap .ql-editor h1,
                    #bf-editor-wrap .ql-editor h2,
                    #bf-editor-wrap .ql-editor h3 { color:#f3f4f6; margin:.6rem 0 .3rem; }
                    #bf-editor-wrap .ql-editor a { color:#a78bfa; }
                    #bf-editor-wrap .ql-editor blockquote {
                        border-left:3px solid #7c3aed; margin-left:0; padding-left:.85rem; color:#9ca3af;
                    }
                    #bf-editor-wrap .ql-editor pre {
                        background:#0d1117; border:1px solid #374151; border-radius:.4rem;
                        padding:.75rem 1rem; color:#34d399;
                    }
                    #bf-editor-wrap .ql-editor ol,
                    #bf-editor-wrap .ql-editor ul { padding-left:1.5rem; }
                `;
                document.head.appendChild(st);
            }

            this._quill = new Quill('#bf-editor', {
                theme: 'snow',
                placeholder: 'Write your blog post here…',
                modules: {
                    toolbar: [
                        ['bold', 'italic', 'underline'],
                        [{ header: [1, 2, 3, false] }],
                        [{ list: 'ordered' }, { list: 'bullet' }],
                        ['link', 'blockquote', 'code-block'],
                        ['clean']
                    ]
                }
            });

            // ── FIX 1: Expose window.quill so paste patch + console commands work ──
            window.quill = this._quill;

            if (d.content) {
                this._quill.root.innerHTML = d.content;
            }

            const syncContent = () => {
                const hi = document.getElementById('bf-content');
                const plainText = this._quill.getText();
                if (hi) hi.value = this._quill.root.innerHTML;
                const wcEl = document.getElementById('bf-wc');
                if (wcEl) wcEl.textContent = plainText.trim().split(/\s+/).filter(Boolean).length + ' words';
                const ccEl = document.getElementById('bf-cc');
                if (ccEl) ccEl.textContent = plainText.replace(/\n$/, '').length + ' chars';
            };
            this._quill.on('text-change', syncContent);
            syncContent();

            const draftKey = 'pw_blog_draft_' + (id || 'new');
            const autosaveDraft = () => {
                try {
                    localStorage.setItem(draftKey, JSON.stringify({
                        content:   this._quill.root.innerHTML,
                        title:     document.getElementById('bf-title')?.value || '',
                        excerpt:   document.getElementById('bf-excerpt')?.value || '',
                        savedAt:   new Date().toISOString(),
                    }));
                } catch (_) {}
            };
            if (this._autosaveTimer) clearInterval(this._autosaveTimer);
            this._autosaveTimer = setInterval(autosaveDraft, 30000);

            if (!id) {
                try {
                    const saved = JSON.parse(localStorage.getItem(draftKey) || 'null');
                    if (saved && saved.content && saved.content !== '<p><br></p>') {
                        const mins = Math.round((Date.now() - new Date(saved.savedAt)) / 60000);
                        const timeAgo = mins < 2 ? 'just now' : mins + 'm ago';
                        const wrap = document.getElementById('bf-editor-wrap');
                        if (wrap) {
                            const banner = document.createElement('div');
                            banner.style.cssText = 'background:#1e293b;border-bottom:1px solid #374151;padding:.5rem 1rem;display:flex;align-items:center;justify-content:space-between;font-size:.78rem;';
                            banner.innerHTML = '<span style="color:#94a3b8;"><i class="fas fa-history mr-1.5" style="color:#a78bfa;"></i>Unsaved draft from ' + timeAgo + '</span>'
                                + '<div style="display:flex;gap:.5rem;">'
                                + '<button onclick="this.parentElement.parentElement.remove()" style="color:#6b7280;background:none;border:none;cursor:pointer;font-size:.75rem;padding:.2rem .5rem;">Dismiss</button>'
                                + '<button style="background:#7c3aed;color:white;border:none;border-radius:.3rem;cursor:pointer;font-size:.75rem;padding:.2rem .6rem;" '
                                + 'onclick="CMSPage._restoreDraft(this);" data-key="' + draftKey + '">Restore</button>'
                                + '</div>';
                            wrap.parentNode.insertBefore(banner, wrap);
                        }
                    }
                } catch (_) {}
            }
        }

        const ec=()=>{ const t=document.getElementById('bf-excerpt')?.value||''; const el=document.getElementById('bf-excerpt-count'); if(el){el.textContent=`${t.length}/160`;el.style.color=t.length>160?'#f87171':'#6b7280';} };
        const sc=()=>{ const t=document.getElementById('bf-stitle')?.value||''; const el=document.getElementById('bf-stitle-count'); if(el)el.textContent=`${t.length}/60`; };
        const dc=()=>{ const t=document.getElementById('bf-sdesc')?.value||''; const el=document.getElementById('bf-sdesc-count'); if(el)el.textContent=`${t.length}/160`; };
        document.getElementById('bf-excerpt')?.addEventListener('input',ec); ec();
        document.getElementById('bf-stitle')?.addEventListener('input',sc); sc();
        document.getElementById('bf-sdesc')?.addEventListener('input',dc); dc();

        document.getElementById('bf-title')?.addEventListener('input',e=>{
            if(!id) document.getElementById('bf-slug').value=e.target.value.toLowerCase().trim().replace(/[^a-z0-9\s-]/g,'').replace(/\s+/g,'-').replace(/-+/g,'-');
        });

        document.getElementById('bf-img')?.addEventListener('input',e=>{
            const pv=document.getElementById('bf-img-preview');
            if(pv){ const img=pv.querySelector('img'); if(img)img.src=e.target.value; pv.style.display=e.target.value?'block':'none'; }
        });
    },

    _closeBlogForm(){
        const f=document.getElementById('cms-blog-form');
        if(f){f.style.display='none';f.innerHTML='';}
        this._editingId=null;
        this._quill=null;
        // Clear window.quill when editor is closed
        window.quill = null;
        if(this._autosaveTimer){ clearInterval(this._autosaveTimer); this._autosaveTimer=null; }
    },

    // ── FIX 3: Restore autosaved draft ───────────────────────────────────
    _restoreDraft(btn){
        const key = btn?.dataset?.key;
        if(!key) return;
        try{
            const saved = JSON.parse(localStorage.getItem(key)||'null');
            if(!saved) return;
            if(this._quill && saved.content){
                this._quill.root.innerHTML = saved.content;
                // Sync hidden input
                const hi = document.getElementById('bf-content');
                if(hi) hi.value = saved.content;
            }
            if(saved.title){ const t=document.getElementById('bf-title'); if(t) t.value=saved.title; }
            if(saved.excerpt){ const e=document.getElementById('bf-excerpt'); if(e) e.value=saved.excerpt; }
            btn?.closest('div')?.remove();
            this._toast('Draft restored','success');
        }catch(e){
            this._toast('Failed to restore draft','error');
        }
    },

    _setPostStatus(status){
        const isPub=status==='published';
        const hi=document.getElementById('bf-pub');
        const draftBtn=document.getElementById('bf-status-draft');
        const pubBtn=document.getElementById('bf-status-published');
        if(hi) hi.value=isPub?'1':'0';
        if(draftBtn){draftBtn.style.background=isPub?'#1f2937':'#4b5563';draftBtn.style.color=isPub?'#9ca3af':'white';}
        if(pubBtn){pubBtn.style.background=isPub?'#7c3aed':'#1f2937';pubBtn.style.color=isPub?'white':'#9ca3af';}
    },

    async _runSEO(){
        const payload={
            title:    document.getElementById('bf-title')?.value||'',
            content:  document.getElementById('bf-content')?.value||'',
            excerpt:  document.getElementById('bf-excerpt')?.value||'',
            focus_keyword: document.getElementById('bf-kw')?.value||'',
            slug:     document.getElementById('bf-slug')?.value||'',
        };
        const panel=document.getElementById('cms-seo-panel'); if(!panel) return;
        panel.style.display='block';
        panel.innerHTML=`<div class="text-gray-400 text-sm"><i class="fas fa-spinner fa-spin mr-2"></i>Analysing SEO…</div>`;
        try{
            const r=await API.cms.seoScore(payload);
            const gc=r.score>=80?'#34d399':r.score>=65?'#fbbf24':r.score>=50?'#f97316':'#f87171';
            const bg=r.score>=80?'rgba(16,185,129,.12)':r.score>=65?'rgba(245,158,11,.12)':'rgba(239,68,68,.12)';
            panel.innerHTML=`
            <div style="display:flex;gap:1.5rem;align-items:flex-start;flex-wrap:wrap;">
                <div class="seo-ring" style="background:${bg};border:3px solid ${gc};color:${gc};">
                    ${r.score}<span style="font-size:.55rem;font-weight:600;">/100</span>
                </div>
                <div style="flex:1;">
                    <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.75rem;">
                        <span style="font-size:1.1rem;font-weight:700;color:${gc};">Grade ${r.grade}</span>
                        <span class="text-xs text-gray-500">${r.word_count} words</span>
                        ${r.ai_powered?'<span style="background:rgba(124,58,237,.15);color:#a78bfa;border:1px solid rgba(124,58,237,.3);padding:.1rem .5rem;border-radius:9999px;font-size:.7rem;">AI Enhanced</span>':''}
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:.35rem;margin-bottom:.75rem;">
                        ${r.checks.map(c=>`
                        <div class="seo-check" style="background:${c.passed?'rgba(16,185,129,.08)':'rgba(239,68,68,.08)'};border:1px solid ${c.passed?'rgba(16,185,129,.2)':'rgba(239,68,68,.2)'};">
                            <i class="fas ${c.passed?'fa-check-circle':'fa-times-circle'}" style="color:${c.passed?'#34d399':'#f87171'};font-size:.8rem;flex-shrink:0;"></i>
                            <span style="color:${c.passed?'#d1d5db':'#9ca3af'};font-size:.77rem;">${this._e(c.label)}</span>
                            <span style="color:${c.passed?'#34d399':'#f87171'};font-size:.7rem;margin-left:auto;font-weight:700;">+${c.points}</span>
                        </div>`).join('')}
                    </div>
                    ${r.ai_suggestions?.length?`
                    <div style="background:#111827;border:1px solid #1f2937;border-radius:.5rem;padding:.75rem;">
                        <div style="font-size:.75rem;font-weight:700;color:#a78bfa;margin-bottom:.5rem;"><i class="fas fa-robot mr-1"></i>AI Recommendations</div>
                        ${r.ai_suggestions.map((s,i)=>`<div style="font-size:.78rem;color:#9ca3af;margin-bottom:.3rem;">
                            <span style="color:#7c3aed;font-weight:700;margin-right:.4rem;">${i+1}.</span>${this._e(s)}</div>`).join('')}
                    </div>`:''}
                </div>
            </div>`;
        }catch(e){ panel.innerHTML=`<div class="text-red-400 text-sm">${this._e(e.message)}</div>`; }
    },

    async _savePost(){
        const title=document.getElementById('bf-title')?.value.trim();
        const slug=document.getElementById('bf-slug')?.value.trim();
        const content = this._quill
            ? this._quill.root.innerHTML.trim()
            : (document.getElementById('bf-content')?.value||'').trim();
        const contentIsEmpty = this._quill
            ? this._quill.getText().trim().length === 0
            : !content;
        if(!title||!slug||contentIsEmpty){this._toast('Title, slug and content required','error');return;}
        const p={title,slug,excerpt:document.getElementById('bf-excerpt')?.value||'',content,
            category:document.getElementById('bf-cat')?.value||'General',
            tags:(document.getElementById('bf-tags')?.value||'').split(',').map(t=>t.trim()).filter(Boolean),
            featured_image:document.getElementById('bf-img')?.value||'',
            seo_title:document.getElementById('bf-stitle')?.value||'',
            seo_description:document.getElementById('bf-sdesc')?.value||'',
            focus_keyword:document.getElementById('bf-kw')?.value||'',
            is_published:document.getElementById('bf-pub')?.value==='1'};
        try{
            if(this._editingId){await API.cms.updatePost(this._editingId,p);this._toast('Post updated');}
            else{
                await API.cms.createPost(p);
                this._toast('Post created');
                try{ localStorage.removeItem('pw_blog_draft_new'); }catch(_){}
            }
            this._closeBlogForm(); await this._blog();
        }catch(e){this._toast(e.message,'error');}
    },

    async _togglePost(id){ try{const r=await API.cms.togglePost(id);this._toast(r.message);await this._blog();}catch(e){this._toast(e.message,'error');} },
    async _deletePost(id){ if(!confirm('Delete this post permanently?'))return; try{await API.cms.deletePost(id);this._toast('Post deleted');await this._blog();}catch(e){this._toast(e.message,'error');} },

    // ═══════════════════════════════════════════════════════════════════════
    // LMS
    // ═══════════════════════════════════════════════════════════════════════
    async _lms() {
        const pane = document.getElementById('cms-pane-lms');
        if (!pane) return;
        if (!document.getElementById('lms-tree')) {
            pane.innerHTML = `
            <div id="lms-header" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
                <h3 class="text-white font-semibold flex items-center gap-2">
                    <i class="fas fa-graduation-cap text-purple-400"></i>
                    Courses <span id="lms-count" class="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">0</span>
                </h3>
                <button class="cb cb-p" onclick="CMSPage._lmsShowCourseForm()"><i class="fas fa-plus"></i> New Course</button>
            </div>
            <div id="lms-overlay" style="display:none;" class="ccard mb-4"></div>
            <div id="lms-tree"></div>`;
        }
        await this._lmsRefreshTree();
    },

    async _lmsRefreshTree() {
        const tree = document.getElementById('lms-tree');
        if (!tree) return;
        tree.innerHTML = `<div class="text-gray-500 text-sm text-center py-4"><i class="fas fa-spinner fa-spin mr-2"></i>Loading courses…</div>`;
        let courses = [];
        try { courses = await API.cms.listCourses(); } catch (e) {
            tree.innerHTML = `<div class="text-center py-8 text-red-400 text-sm">${e.message}</div>`; return;
        }
        const countEl = document.getElementById('lms-count');
        if (countEl) countEl.textContent = courses.length;
        if (!courses.length) {
            tree.innerHTML = `<div class="text-center py-12 text-gray-500 text-sm"><i class="fas fa-graduation-cap text-3xl block mb-3 opacity-20"></i>No courses yet — click <strong class="text-purple-400">New Course</strong> to get started.</div>`;
            return;
        }
        tree.innerHTML = courses.map(c => `
        <div class="lms-module" id="lms-course-${c.id}">
            <div class="lms-module-header" onclick="CMSPage._lmsToggle(${c.id})">
                <i class="fas fa-chevron-right text-gray-600 text-xs" id="lms-arr-${c.id}" style="transition:transform .2s;flex-shrink:0;"></i>
                <div style="flex:1;min-width:0;">
                    <div class="text-white font-semibold text-sm truncate">${this._e(c.title)}</div>
                    <div class="text-gray-500 text-xs">${this._e(c.level||'Beginner')} &bull; ${c.module_count||0} modules &bull; ${c.lesson_count||0} lessons &bull; ${c.price>0?'$'+Number(c.price).toFixed(2):'Free'}</div>
                </div>
                ${this._pub(c.is_published)}
                <div style="display:flex;gap:.3rem;flex-shrink:0;" onclick="event.stopPropagation()">
                    <button class="cb cb-g" style="font-size:.7rem;padding:.25rem .6rem;" onclick="CMSPage._lmsShowCourseForm(${c.id})"><i class="fas fa-edit"></i></button>
                    <button class="cb ${c.is_published?'cb-y':'cb-gr'}" style="font-size:.7rem;padding:.25rem .6rem;" onclick="CMSPage._lmsTogglePub(${c.id})">${c.is_published?'Unpublish':'Publish'}</button>
                    <button class="cb cb-r" style="font-size:.7rem;padding:.25rem .6rem;" onclick="CMSPage._lmsDeleteCourse(${c.id})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
            <div id="lms-body-${c.id}" style="display:none;">
                <div style="padding:.65rem 1rem;background:#0d1117;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #1f2937;">
                    <span class="text-xs text-gray-500 uppercase tracking-wider font-semibold">Modules</span>
                    <button class="cb cb-p" style="font-size:.7rem;padding:.25rem .75rem;" onclick="CMSPage._lmsShowModuleForm(${c.id})"><i class="fas fa-plus"></i> Add Module</button>
                </div>
                <div id="lms-modules-${c.id}"><div class="text-gray-600 text-xs text-center py-3"><i class="fas fa-spinner fa-spin mr-1"></i>Loading…</div></div>
            </div>
        </div>`).join('');
        if (courses.length) await this._lmsExpand(courses[0].id);
    },

    async _lmsToggle(cid) {
        const body=document.getElementById(`lms-body-${cid}`);
        const arr=document.getElementById(`lms-arr-${cid}`);
        if(!body) return;
        const opening=body.style.display==='none'||body.style.display==='';
        body.style.display=opening?'block':'none';
        if(arr) arr.style.transform=opening?'rotate(90deg)':'';
        if(opening) await this._lmsLoadModules(cid);
    },

    async _lmsExpand(cid) {
        const body=document.getElementById(`lms-body-${cid}`);
        const arr=document.getElementById(`lms-arr-${cid}`);
        if(!body) return;
        body.style.display='block';
        if(arr) arr.style.transform='rotate(90deg)';
        await this._lmsLoadModules(cid);
    },

    _lmsOverlay(html) {
        const ov=document.getElementById('lms-overlay'); if(!ov) return;
        ov.style.display='block'; ov.innerHTML=html;
        ov.scrollIntoView({behavior:'smooth',block:'start'});
    },

    _lmsCloseOverlay() {
        const ov=document.getElementById('lms-overlay');
        if(ov){ov.style.display='none';ov.innerHTML='';}
        this._editingId=null;
    },

    async _lmsShowCourseForm(id) {
        id=parseInt(id)||null;
        let d={title:'',description:'',level:'Beginner',price:0,thumbnail:'',preview_video:'',is_published:false,certificate_enabled:false,pass_percentage:70};
        if(id){ try{const list=await API.cms.listCourses(); d=list.find(c=>c.id===id)||d;}catch(_){} }
        this._editingId=id;
        this._lmsOverlay(`
        <div class="chdr"><h4 class="text-white font-semibold">${id?'Edit Course':'New Course'}</h4>
            <button class="cb cb-g" onclick="CMSPage._lmsCloseOverlay()"><i class="fas fa-times"></i></button></div>
        <div class="crow crow2">
            <div><label class="cl">Title *</label><input class="ci" id="cf-title" value="${this._e(d.title)}" placeholder="Course title"></div>
            <div><label class="cl">Level</label><select class="cs" id="cf-level">${['Beginner','Intermediate','Advanced'].map(l=>`<option${d.level===l?' selected':''}>${l}</option>`).join('')}</select></div>
        </div>
        <div class="crow"><div><label class="cl">Description</label><textarea class="cta" id="cf-desc" style="min-height:70px;">${this._e(d.description)}</textarea></div></div>
        <div class="crow crow2">
            <div><label class="cl">Price (0 = Free)</label><input type="number" class="ci" id="cf-price" step="0.01" min="0" value="${d.price||0}"></div>
            <div><label class="cl">Pass % for Certificate</label><input type="number" class="ci" id="cf-pass" min="0" max="100" value="${d.pass_percentage||70}"></div>
        </div>
        <div class="crow crow2">
            <div><label class="cl">Thumbnail URL</label>
                <div style="display:flex;gap:.5rem;"><input class="ci" id="cf-thumb" value="${this._e(d.thumbnail)}" placeholder="https://…">
                <button class="cb cb-g" onclick="CMSPage._pickMedia('cf-thumb')"><i class="fas fa-images"></i></button></div></div>
            <div><label class="cl">Preview Video URL</label><input class="ci" id="cf-preview" value="${this._e(d.preview_video)}" placeholder="YouTube/Vimeo URL"></div>
        </div>
        <div style="display:flex;gap:1.5rem;margin-top:.5rem;align-items:center;flex-wrap:wrap;">
            <label class="ctog" onclick="CMSPage._togCheck('cf-pub')">
                <div class="ttrack${d.is_published?' on':''}"><div class="tthumb"></div></div>
                <span class="text-sm text-gray-300">Published</span>
                <input type="hidden" id="cf-pub" value="${d.is_published?'1':'0'}">
            </label>
            <label class="ctog" onclick="CMSPage._togCheck('cf-cert')">
                <div class="ttrack${d.certificate_enabled?' on':''}"><div class="tthumb"></div></div>
                <span class="text-sm text-gray-300">Certificate Enabled</span>
                <input type="hidden" id="cf-cert" value="${d.certificate_enabled?'1':'0'}">
            </label>
            <button class="cb cb-p" onclick="CMSPage._lmsSaveCourse()"><i class="fas fa-save"></i> ${id?'Update':'Create'} Course</button>
        </div>`);
    },

    async _lmsSaveCourse() {
        const title=document.getElementById('cf-title')?.value.trim();
        if(!title){this._toast('Title required','error');return;}
        const p={title,description:document.getElementById('cf-desc')?.value||'',level:document.getElementById('cf-level')?.value||'Beginner',
            price:parseFloat(document.getElementById('cf-price')?.value)||0,thumbnail:document.getElementById('cf-thumb')?.value||'',
            preview_video:document.getElementById('cf-preview')?.value||'',is_published:document.getElementById('cf-pub')?.value==='1',
            certificate_enabled:document.getElementById('cf-cert')?.value==='1',pass_percentage:parseInt(document.getElementById('cf-pass')?.value)||70};
        try{
            if(this._editingId){await API.cms.updateCourse(this._editingId,p);this._toast('Course updated');}
            else{await API.cms.createCourse(p);this._toast('Course created');}
            this._lmsCloseOverlay(); await this._lmsRefreshTree();
        }catch(e){this._toast(e.message,'error');}
    },

    async _lmsTogglePub(id){ try{const r=await API.cms.toggleCourse(id);this._toast(r.message);await this._lmsRefreshTree();}catch(e){this._toast(e.message,'error');} },
    async _lmsDeleteCourse(id){ if(!confirm('Delete course and ALL its modules, lessons and quizzes?'))return; try{await API.cms.deleteCourse(id);this._toast('Course deleted');this._lmsCloseOverlay();await this._lmsRefreshTree();}catch(e){this._toast(e.message,'error');} },

    async _lmsLoadModules(cid) {
        const el=document.getElementById(`lms-modules-${cid}`); if(!el) return;
        let mods=[]; try{mods=await API.cms.listModules(cid);}catch(e){el.innerHTML=`<div class="text-red-400 text-xs text-center py-3">${e.message}</div>`;return;}
        if(!mods.length){el.innerHTML=`<div style="padding:1rem 1.5rem;text-align:center;"><p class="text-gray-500 text-xs mb-2">No modules yet.</p><button class="cb cb-p" style="font-size:.72rem;" onclick="CMSPage._lmsShowModuleForm(${cid})"><i class="fas fa-plus"></i> Add First Module</button></div>`;return;}
        el.innerHTML=mods.map(m=>`
        <div style="border-top:1px solid #1a2235;" id="lms-mod-${m.id}">
            <div style="display:flex;align-items:center;gap:.75rem;padding:.6rem 1rem .6rem 2rem;background:#161f2e;">
                <i class="fas fa-layer-group text-purple-500 text-xs"></i>
                <div style="flex:1;min-width:0;">
                    <span class="text-gray-200 text-sm font-medium">${this._e(m.title)}</span>
                    <span class="text-gray-600 text-xs ml-2">${m.lesson_count||0} lessons &bull; ${m.quiz_count?'Has quiz':'No quiz'}</span>
                </div>
                <div style="display:flex;gap:.3rem;flex-shrink:0;">
                    <button class="cb cb-g" style="font-size:.7rem;padding:.25rem .6rem;" onclick="CMSPage._lmsShowModuleForm(${cid},${m.id},'${this._e(m.title).replace(/'/g,"\\'")}','${this._e(m.description||'').replace(/'/g,"\\'")}',${m.order_index||0})"><i class="fas fa-edit"></i></button>
                    <button class="cb cb-p" style="font-size:.7rem;padding:.25rem .6rem;" onclick="CMSPage._lmsShowLessonForm(${cid},${m.id})"><i class="fas fa-plus"></i> Lesson</button>
                    <button class="cb cb-y" style="font-size:.7rem;padding:.25rem .6rem;" onclick="CMSPage._lmsShowQuizPanel(${m.id})"><i class="fas fa-question-circle"></i> Quiz</button>
                    <button class="cb cb-r" style="font-size:.7rem;padding:.25rem .6rem;" onclick="CMSPage._lmsDeleteModule(${m.id},${cid})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
            <div id="lms-lessons-${m.id}"><div class="text-gray-700 text-xs text-center py-2"><i class="fas fa-spinner fa-spin mr-1"></i></div></div>
        </div>`).join('');
        await Promise.all(mods.map(m=>this._lmsLoadLessons(m.id)));
    },

    _lmsShowModuleForm(cid,mid,title,desc,order){
        mid=parseInt(mid)||null; title=title||''; desc=desc||''; order=parseInt(order)||0;
        this._lmsOverlay(`
        <div class="chdr"><h4 class="text-white font-semibold"><i class="fas fa-layer-group text-purple-400 mr-2"></i>${mid?'Edit Module':'Add Module'}</h4>
            <button class="cb cb-g" onclick="CMSPage._lmsCloseOverlay()"><i class="fas fa-times"></i></button></div>
        <div class="crow crow2">
            <div><label class="cl">Module Title *</label><input class="ci" id="mf-title" value="${this._e(title)}" placeholder="e.g. Introduction to Forex"></div>
            <div><label class="cl">Order Index</label><input type="number" class="ci" id="mf-order" value="${order}" min="0"></div>
        </div>
        <div class="crow"><div><label class="cl">Description (optional)</label><textarea class="cta" id="mf-desc" style="min-height:60px;">${this._e(desc)}</textarea></div></div>
        <div style="display:flex;gap:.75rem;margin-top:.25rem;">
            <button class="cb cb-p" onclick="CMSPage._lmsSaveModule(${cid},${mid||'null'})"><i class="fas fa-save"></i> ${mid?'Update':'Add'} Module</button>
            <button class="cb cb-g" onclick="CMSPage._lmsCloseOverlay()">Cancel</button>
        </div>`);
    },

    async _lmsSaveModule(cid,mid){
        const title=document.getElementById('mf-title')?.value.trim();
        if(!title){this._toast('Module title required','error');return;}
        const p={course_id:cid,title,description:document.getElementById('mf-desc')?.value||'',order_index:parseInt(document.getElementById('mf-order')?.value)||0};
        try{
            if(mid){await API.cms.updateModule(mid,p);this._toast('Module updated');}
            else{await API.cms.createModule(p);this._toast('Module added');}
            this._lmsCloseOverlay(); await this._lmsLoadModules(cid);
        }catch(e){this._toast(e.message,'error');}
    },

    async _lmsDeleteModule(mid,cid){ if(!confirm('Delete module and all its lessons and quiz?'))return; try{await API.cms.deleteModule(mid);this._toast('Module deleted');this._lmsCloseOverlay();await this._lmsLoadModules(cid);}catch(e){this._toast(e.message,'error');} },

    async _lmsLoadLessons(mid){
        const el=document.getElementById(`lms-lessons-${mid}`); if(!el) return;
        let lessons=[]; try{lessons=await API.cms.listLessons(mid);}catch(_){}
        if(!lessons.length){el.innerHTML=`<div class="text-gray-700 text-xs text-center py-2">No lessons yet</div>`;return;}
        el.innerHTML=lessons.map(l=>`
        <div class="lms-lesson">
            <i class="fas ${l.video_url?'fa-play-circle text-purple-400':'fa-file-alt text-gray-600'} text-xs"></i>
            <span class="text-gray-300 text-xs flex-1">${String(l.order_index||0).padStart(2,'0')}. ${this._e(l.title)}</span>
            <span class="text-gray-600 text-xs">${l.duration_minutes||0}m</span>
            ${l.is_free_preview?'<span class="text-xs text-green-500 px-1">Free</span>':''}
            <div style="display:flex;gap:.25rem;">
                <button class="cb cb-g" style="font-size:.68rem;padding:.2rem .5rem;" onclick='CMSPage._lmsShowLessonForm(null,${mid},${JSON.stringify(l).replace(/"/g,"&quot;")})'>
                    <i class="fas fa-edit"></i>
                </button>
                <button class="cb cb-r" style="font-size:.68rem;padding:.2rem .5rem;" onclick="CMSPage._lmsDeleteLesson(${l.id},${mid})"><i class="fas fa-trash"></i></button>
            </div>
        </div>`).join('');
    },

    _lmsShowLessonForm(cid,mid,lesson){
        const isEdit=lesson&&lesson.id; this._editingId=isEdit?lesson.id:null;
        const d=lesson||{title:'',content:'',video_url:'',attachment_url:'',duration_minutes:0,order_index:0,is_free_preview:false,course_id:cid};
        this._lmsOverlay(`
        <div class="chdr"><h4 class="text-white font-semibold"><i class="fas fa-book-open text-blue-400 mr-2"></i>${isEdit?'Edit Lesson':'Add Lesson'}</h4>
            <button class="cb cb-g" onclick="CMSPage._lmsCloseOverlay()"><i class="fas fa-times"></i></button></div>
        <div class="crow crow2">
            <div><label class="cl">Title *</label><input class="ci" id="lf-title" value="${this._e(d.title)}" placeholder="Lesson title"></div>
            <div><label class="cl">Video URL</label>
                <div style="display:flex;gap:.4rem;"><input class="ci" id="lf-video" value="${this._e(d.video_url)}" placeholder="YouTube/Vimeo…">
                <button class="cb cb-g" onclick="CMSPage._pickMedia('lf-video','video')"><i class="fas fa-film"></i></button></div></div>
        </div>
        <div class="crow crow2">
            <div><label class="cl">Attachment URL</label>
                <div style="display:flex;gap:.4rem;"><input class="ci" id="lf-attach" value="${this._e(d.attachment_url)}" placeholder="PDF, slides…">
                <button class="cb cb-g" onclick="CMSPage._pickMedia('lf-attach','docs')"><i class="fas fa-paperclip"></i></button></div></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem;">
                <div><label class="cl">Duration (min)</label><input type="number" class="ci" id="lf-dur" value="${d.duration_minutes||0}" min="0"></div>
                <div><label class="cl">Order</label><input type="number" class="ci" id="lf-ord" value="${d.order_index||0}" min="0"></div>
            </div>
        </div>
        <div class="crow"><div><label class="cl">Content / Notes</label><textarea class="cta" id="lf-content" style="min-height:100px;">${this._e(d.content)}</textarea></div></div>
        <div style="display:flex;gap:1.5rem;align-items:center;margin-top:.5rem;flex-wrap:wrap;">
            <label class="ctog" onclick="CMSPage._togCheck('lf-preview')">
                <div class="ttrack${d.is_free_preview?' on':''}"><div class="tthumb"></div></div>
                <span class="text-sm text-gray-300">Free Preview</span>
                <input type="hidden" id="lf-preview" value="${d.is_free_preview?'1':'0'}">
            </label>
            <button class="cb cb-p" onclick="CMSPage._lmsSaveLesson(${mid},${cid||d.course_id||0})"><i class="fas fa-save"></i> ${isEdit?'Update':'Add'} Lesson</button>
            <button class="cb cb-g" onclick="CMSPage._lmsCloseOverlay()">Cancel</button>
        </div>`);
    },

    async _lmsSaveLesson(mid,cid){
        const title=document.getElementById('lf-title')?.value.trim();
        if(!title){this._toast('Title required','error');return;}
        const p={module_id:mid,course_id:cid,title,content:document.getElementById('lf-content')?.value||'',
            video_url:document.getElementById('lf-video')?.value||'',attachment_url:document.getElementById('lf-attach')?.value||'',
            duration_minutes:parseInt(document.getElementById('lf-dur')?.value)||0,order_index:parseInt(document.getElementById('lf-ord')?.value)||0,
            is_free_preview:document.getElementById('lf-preview')?.value==='1'};
        try{
            if(this._editingId){await API.cms.updateLesson(this._editingId,p);this._toast('Lesson updated');}
            else{await API.cms.createLesson(p);this._toast('Lesson added');}
            this._lmsCloseOverlay(); await this._lmsLoadLessons(mid);
        }catch(e){this._toast(e.message,'error');}
    },

    async _lmsDeleteLesson(id,mid){ if(!confirm('Delete this lesson?'))return; try{await API.cms.deleteLesson(id);this._toast('Lesson deleted');await this._lmsLoadLessons(mid);}catch(e){this._toast(e.message,'error');} },

    async _lmsShowQuizPanel(mid){
        this._lmsOverlay(`<div class="text-gray-400 text-sm"><i class="fas fa-spinner fa-spin mr-2"></i>Loading quiz…</div>`);
        let quiz=null; try{quiz=await API.cms.getQuiz(mid);}catch(_){}
        this._lmsRenderQuizEditor(mid,quiz);
    },

    _lmsRenderQuizEditor(mid,quiz){
        const ov=document.getElementById('lms-overlay'); if(!ov) return;
        ov.innerHTML=`
        <div class="chdr"><h4 class="text-white font-semibold"><i class="fas fa-question-circle text-yellow-400 mr-2"></i>Quiz — Module ${mid}</h4>
            <button class="cb cb-g" onclick="CMSPage._lmsCloseOverlay()"><i class="fas fa-times"></i></button></div>
        ${!quiz?`
        <div class="crow crow2">
            <div><label class="cl">Quiz Title *</label><input class="ci" id="qz-title" placeholder="Module Quiz"></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem;">
                <div><label class="cl">Pass %</label><input type="number" class="ci" id="qz-pass" value="70" min="0" max="100"></div>
                <div><label class="cl">Max Attempts</label><input type="number" class="ci" id="qz-attempts" value="3" min="1"></div>
            </div>
        </div>
        <div style="display:flex;gap:.75rem;">
            <button class="cb cb-p" onclick="CMSPage._lmsCreateQuiz(${mid})"><i class="fas fa-plus"></i> Create Quiz</button>
            <button class="cb cb-g" onclick="CMSPage._lmsCloseOverlay()">Cancel</button>
        </div>`:`
        <div class="crow crow2">
            <div><label class="cl">Quiz Title</label><input class="ci" id="qz-title" value="${this._e(quiz.title)}"></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem;">
                <div><label class="cl">Pass %</label><input type="number" class="ci" id="qz-pass" value="${quiz.pass_percentage||70}" min="0" max="100"></div>
                <div><label class="cl">Max Attempts</label><input type="number" class="ci" id="qz-attempts" value="${quiz.max_attempts||3}" min="1"></div>
            </div>
        </div>
        <div style="display:flex;gap:.5rem;margin-bottom:1rem;flex-wrap:wrap;">
            <button class="cb cb-p" onclick="CMSPage._lmsUpdateQuiz(${quiz.id},${mid})"><i class="fas fa-save"></i> Save Settings</button>
            <button class="cb cb-r" onclick="CMSPage._lmsDeleteQuiz(${quiz.id},${mid})"><i class="fas fa-trash"></i> Delete Quiz</button>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.75rem;">
            <span class="text-white font-semibold text-sm">Questions (${(quiz.questions||[]).length})</span>
            <button class="cb cb-p" style="font-size:.75rem;" onclick="CMSPage._lmsShowQuestionForm(${quiz.id},${mid})"><i class="fas fa-plus"></i> Add Question</button>
        </div>
        <div id="quiz-questions-list">${(quiz.questions||[]).map((q,i)=>this._lmsQuestionHtml(q,i,mid)).join('')}</div>`}`;
    },

    _lmsQuestionHtml(q,i,mid){
        const opts=['a','b','c','d'];
        return `<div class="quiz-q">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:.5rem;margin-bottom:.5rem;">
                <span class="text-gray-300 text-sm font-medium">${i+1}. ${this._e(q.question)}</span>
                <div style="display:flex;gap:.3rem;flex-shrink:0;">
                    <button class="cb cb-g" style="font-size:.68rem;padding:.2rem .5rem;" onclick='CMSPage._lmsShowQuestionForm(${q.quiz_id||0},${mid},${JSON.stringify(q).replace(/"/g,"&quot;")})'>
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="cb cb-r" style="font-size:.68rem;padding:.2rem .5rem;" onclick="CMSPage._lmsDeleteQuestion(${q.id},${mid})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:.3rem;">
                ${opts.filter(o=>q[`option_${o}`]).map(o=>`
                <div style="background:${q.correct_option===o?'rgba(16,185,129,.15)':'rgba(31,41,55,.8)'};border:1px solid ${q.correct_option===o?'rgba(16,185,129,.4)':'#374151'};border-radius:.4rem;padding:.35rem .6rem;font-size:.78rem;color:${q.correct_option===o?'#34d399':'#9ca3af'};">
                    <span style="font-weight:700;margin-right:.35rem;">${o.toUpperCase()}.</span>${this._e(q[`option_${o}`])}${q.correct_option===o?'<i class="fas fa-check ml-1"></i>':''}
                </div>`).join('')}
            </div>
            ${q.explanation?`<div style="margin-top:.4rem;font-size:.75rem;color:#6b7280;"><i class="fas fa-info-circle mr-1"></i>${this._e(q.explanation)}</div>`:''}
        </div>`;
    },

    async _lmsCreateQuiz(mid){ const t=document.getElementById('qz-title')?.value.trim(); if(!t){this._toast('Quiz title required','error');return;} try{await API.cms.createQuiz({module_id:mid,title:t,pass_percentage:parseInt(document.getElementById('qz-pass')?.value)||70,max_attempts:parseInt(document.getElementById('qz-attempts')?.value)||3});this._toast('Quiz created');await this._lmsShowQuizPanel(mid);}catch(e){this._toast(e.message,'error');} },
    async _lmsUpdateQuiz(qid,mid){ const t=document.getElementById('qz-title')?.value.trim(); try{await API.cms.updateQuiz(qid,{module_id:mid,title:t,pass_percentage:parseInt(document.getElementById('qz-pass')?.value)||70,max_attempts:parseInt(document.getElementById('qz-attempts')?.value)||3});this._toast('Quiz settings saved');}catch(e){this._toast(e.message,'error');} },
    async _lmsDeleteQuiz(qid,mid){ if(!confirm('Delete quiz and all questions?'))return; try{await API.cms.deleteQuiz(qid);this._toast('Quiz deleted');await this._lmsShowQuizPanel(mid);}catch(e){this._toast(e.message,'error');} },

    _lmsShowQuestionForm(quizId,mid,q){
        const isEdit=q&&q.id;
        const d=q||{question:'',option_a:'',option_b:'',option_c:'',option_d:'',correct_option:'a',explanation:'',order_index:0};
        document.getElementById('qform-overlay')?.remove();
        const overlay=document.createElement('div');
        overlay.id='qform-overlay';
        overlay.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9998;display:flex;align-items:center;justify-content:center;padding:1rem;';
        overlay.innerHTML=`
        <div style="background:#1f2937;border:1px solid #374151;border-radius:.75rem;padding:1.5rem;width:min(620px,95vw);max-height:90vh;overflow-y:auto;">
            <div class="chdr"><h4 class="text-white font-semibold">${isEdit?'Edit Question':'Add Question'}</h4>
                <button class="cb cb-g" onclick="document.getElementById('qform-overlay').remove()"><i class="fas fa-times"></i></button></div>
            <div class="crow"><div><label class="cl">Question *</label><textarea class="cta" id="qf-q" style="min-height:60px;">${this._e(d.question)}</textarea></div></div>
            <div class="crow crow2">
                <div><label class="cl">Option A *</label><input class="ci" id="qf-a" value="${this._e(d.option_a)}"></div>
                <div><label class="cl">Option B *</label><input class="ci" id="qf-b" value="${this._e(d.option_b)}"></div>
                <div><label class="cl">Option C</label><input class="ci" id="qf-c" value="${this._e(d.option_c||'')}"></div>
                <div><label class="cl">Option D</label><input class="ci" id="qf-d" value="${this._e(d.option_d||'')}"></div>
            </div>
            <div class="crow crow2">
                <div><label class="cl">Correct Answer *</label>
                    <select class="cs" id="qf-correct">${['a','b','c','d'].map(o=>`<option value="${o}"${d.correct_option===o?' selected':''}>${o.toUpperCase()}</option>`).join('')}</select></div>
                <div><label class="cl">Order</label><input type="number" class="ci" id="qf-ord" value="${d.order_index||0}"></div>
            </div>
            <div class="crow"><div><label class="cl">Explanation</label><input class="ci" id="qf-expl" value="${this._e(d.explanation||'')}"></div></div>
            <div style="display:flex;gap:.75rem;margin-top:.5rem;">
                <button class="cb cb-p" onclick="CMSPage._lmsSaveQuestion(${quizId},${mid},${isEdit?d.id:'null'})"><i class="fas fa-save"></i> ${isEdit?'Update':'Add'} Question</button>
                <button class="cb cb-g" onclick="document.getElementById('qform-overlay').remove()">Cancel</button>
            </div>
        </div>`;
        document.body.appendChild(overlay);
    },

    async _lmsSaveQuestion(quizId,mid,qid){
        const question=document.getElementById('qf-q')?.value.trim();
        const a=document.getElementById('qf-a')?.value.trim();
        const b=document.getElementById('qf-b')?.value.trim();
        if(!question||!a||!b){this._toast('Question and options A & B are required','error');return;}
        const p={quiz_id:quizId,question,option_a:a,option_b:b,option_c:document.getElementById('qf-c')?.value||'',option_d:document.getElementById('qf-d')?.value||'',
            correct_option:document.getElementById('qf-correct')?.value||'a',explanation:document.getElementById('qf-expl')?.value||'',order_index:parseInt(document.getElementById('qf-ord')?.value)||0};
        try{
            if(qid){await API.cms.updateQuestion(qid,p);this._toast('Question updated');}
            else{await API.cms.createQuestion(p);this._toast('Question added');}
            document.getElementById('qform-overlay')?.remove(); await this._lmsShowQuizPanel(mid);
        }catch(e){this._toast(e.message,'error');}
    },

    async _lmsDeleteQuestion(id,mid){ if(!confirm('Delete this question?'))return; try{await API.cms.deleteQuestion(id);this._toast('Question deleted');await this._lmsShowQuizPanel(mid);}catch(e){this._toast(e.message,'error');} },

    // ═══════════════════════════════════════════════════════════════════════
    // SIGNALS
    // ═══════════════════════════════════════════════════════════════════════
    async _signals(){
        const pane=document.getElementById('cms-pane-signals'); if(!pane) return;
        let sigs=[]; try{sigs=await API.cms.listSignals();}catch(e){this._toast('Failed to load signals: '+e.message,'error');}
        pane.innerHTML=`
        <div class="chdr">
            <h3 class="text-white font-semibold flex items-center gap-2"><i class="fas fa-satellite-dish text-purple-400"></i> Signals <span class="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">${sigs.length}</span></h3>
            <button class="cb cb-p" onclick="CMSPage._sigForm()"><i class="fas fa-plus"></i> New Signal</button>
        </div>
        <div id="cms-sig-form" style="display:none;" class="ccard mb-4"></div>
        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div class="overflow-x-auto"><table class="cms-tbl">
                <thead><tr><th>Symbol</th><th>Dir</th><th>Entry</th><th>SL</th><th>TP</th><th>TF</th><th>Status</th><th>Created</th><th class="text-right">Actions</th></tr></thead>
                <tbody>${sigs.length?sigs.map(s=>`<tr>
                    <td class="font-bold text-white">${this._e(s.symbol||'—')}</td>
                    <td>${this._dir(s.direction)}</td>
                    <td class="font-mono text-gray-300">${s.entry_price}</td>
                    <td class="font-mono text-red-400">${s.stop_loss}</td>
                    <td class="font-mono text-green-400">${s.take_profit}</td>
                    <td class="text-gray-500">${s.timeframe||'—'}</td>
                    <td>${this._pub(s.status==='active','Active','Closed')}</td>
                    <td class="text-gray-500">${this._d(s.created_at)}</td>
                    <td class="text-right"><div style="display:flex;gap:.3rem;justify-content:flex-end;">
                        <button class="cb cb-g" onclick='CMSPage._sigForm(${JSON.stringify(s).replace(/"/g,"&quot;")})'>
                            <i class="fas fa-edit"></i>
                        </button>
                        ${s.status==='active'?`<button class="cb cb-y" onclick="CMSPage._closeSignal(${s.id})">Close</button>`:''}
                        <button class="cb cb-r" onclick="CMSPage._deleteSignal(${s.id})"><i class="fas fa-trash"></i></button>
                    </div></td>
                </tr>`).join(''):`<tr><td colspan="9" class="text-center py-8 text-gray-500 text-sm">No signals yet</td></tr>`}
                </tbody>
            </table></div>
        </div>`;
    },

    _sigForm(d=null){
        const isEdit=d&&d.id; this._editingId=isEdit?d.id:null;
        d=d||{symbol:'',direction:'BUY',entry_price:'',stop_loss:'',take_profit:'',timeframe:'1H',analysis:'',ai_confidence:'',status:'active'};
        const f=document.getElementById('cms-sig-form'); if(!f) return;
        f.style.display='block';
        f.innerHTML=`
        <div class="chdr"><h4 class="text-white font-semibold">${isEdit?'Edit Signal':'New Signal'}</h4>
            <button class="cb cb-g" onclick="CMSPage._closeSigForm()"><i class="fas fa-times"></i></button></div>
        <div class="crow crow3">
            <div><label class="cl">Symbol *</label><input class="ci" id="sf-sym" value="${this._e(d.symbol)}" placeholder="EURUSD"></div>
            <div><label class="cl">Direction</label><select class="cs" id="sf-dir"><option${d.direction==='BUY'?' selected':''}>BUY</option><option${d.direction==='SELL'?' selected':''}>SELL</option></select></div>
            <div><label class="cl">Timeframe</label><select class="cs" id="sf-tf">${['1M','5M','15M','1H','4H','1D','1W'].map(t=>`<option${d.timeframe===t?' selected':''}>${t}</option>`).join('')}</select></div>
        </div>
        <div class="crow crow3">
            <div><label class="cl">Entry *</label><input type="number" step="0.00001" class="ci" id="sf-entry" value="${d.entry_price}"></div>
            <div><label class="cl">Stop Loss *</label><input type="number" step="0.00001" class="ci" id="sf-sl" value="${d.stop_loss}"></div>
            <div><label class="cl">Take Profit *</label><input type="number" step="0.00001" class="ci" id="sf-tp" value="${d.take_profit}"></div>
        </div>
        <div class="crow crow2">
            <div><label class="cl">AI Confidence (0–1)</label><input type="number" step="0.01" min="0" max="1" class="ci" id="sf-conf" value="${d.ai_confidence||''}"></div>
            <div><label class="cl">Status</label><select class="cs" id="sf-status">${['active','closed','cancelled'].map(s=>`<option${d.status===s?' selected':''}>${s}</option>`).join('')}</select></div>
        </div>
        <div class="crow"><div><label class="cl">Analysis Notes</label><textarea class="cta" id="sf-anal" style="min-height:70px;">${this._e(d.analysis||'')}</textarea></div></div>
        <button class="cb cb-p" onclick="CMSPage._saveSig()"><i class="fas fa-save"></i> ${isEdit?'Update':'Create'} Signal</button>`;
    },
    _closeSigForm(){ const f=document.getElementById('cms-sig-form'); if(f){f.style.display='none';f.innerHTML='';} this._editingId=null; },
    async _saveSig(){
        const sym=document.getElementById('sf-sym')?.value.trim().toUpperCase();
        const entry=parseFloat(document.getElementById('sf-entry')?.value),sl=parseFloat(document.getElementById('sf-sl')?.value),tp=parseFloat(document.getElementById('sf-tp')?.value);
        if(!sym||isNaN(entry)||isNaN(sl)||isNaN(tp)){this._toast('Symbol, Entry, SL, TP required','error');return;}
        const p={symbol:sym,direction:document.getElementById('sf-dir')?.value||'BUY',entry_price:entry,stop_loss:sl,take_profit:tp,
            timeframe:document.getElementById('sf-tf')?.value||'1H',analysis:document.getElementById('sf-anal')?.value||'',
            ai_confidence:document.getElementById('sf-conf')?.value?parseFloat(document.getElementById('sf-conf').value):null,
            status:document.getElementById('sf-status')?.value||'active'};
        try{
            if(this._editingId){await API.cms.updateSignal(this._editingId,p);this._toast('Signal updated');}
            else{await API.cms.createSignal(p);this._toast('Signal created');}
            this._closeSigForm(); await this._signals();
        }catch(e){this._toast(e.message,'error');}
    },
    async _closeSignal(id){ const o=prompt('Outcome (win/loss/breakeven):','win'); if(!o)return; try{await API.cms.closeSignal(id,o);this._toast('Signal closed');await this._signals();}catch(e){this._toast(e.message,'error');} },
    async _deleteSignal(id){ if(!confirm('Delete signal?'))return; try{await API.cms.deleteSignal(id);this._toast('Deleted');await this._signals();}catch(e){this._toast(e.message,'error');} },

    // ═══════════════════════════════════════════════════════════════════════
    // WEBINARS
    // ═══════════════════════════════════════════════════════════════════════
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
                    <td><button class="cb cb-g" style="font-size:.72rem;padding:.25rem .65rem;" onclick="CMSPage._webinarRegistrants(${w.id},'${this._e(w.title).replace(/'/g,"\\'")}')">
                        <i class="fas fa-users mr-1"></i>${regCounts[w.id]||0}
                    </button></td>
                    <td class="text-gray-400">${w.max_attendees||100}</td>
                    <td class="text-right"><div style="display:flex;gap:.3rem;justify-content:flex-end;">
                        <button class="cb cb-g" onclick='CMSPage._webinarForm(${JSON.stringify(w).replace(/"/g,"&quot;")})'>
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="cb ${w.is_published?'cb-g':'cb-gr'}" onclick="CMSPage._toggleWebinar(${w.id})">${w.is_published?'Unpublish':'Publish'}</button>
                        <button class="cb cb-r" onclick="CMSPage._deleteWebinar(${w.id})"><i class="fas fa-trash"></i></button>
                    </div></td>
                </tr>`).join(''):`<tr><td colspan="9" class="text-center py-8 text-gray-500 text-sm">No webinars yet</td></tr>`}
                </tbody>
            </table></div>
        </div>`;
    },

    // ── FIX 2: _webinarForm — was missing entirely ────────────────────────
    _webinarForm(d=null){
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
    },

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
    async _toggleWebinar(id){ try{const r=await API.cms.toggleWebinar(id);this._toast(r.message);await this._webinars();}catch(e){this._toast(e.message,'error');} },
    async _deleteWebinar(id){ if(!confirm('Delete webinar?'))return; try{await API.cms.deleteWebinar(id);this._toast('Deleted');await this._webinars();}catch(e){this._toast(e.message,'error');} },

    // ═══════════════════════════════════════════════════════════════════════
    // USERS
    // ═══════════════════════════════════════════════════════════════════════
    async _users(){
        const pane=document.getElementById('cms-pane-users'); if(!pane) return;
        pane.innerHTML=`
        <div class="chdr">
            <h3 class="text-white font-semibold flex items-center gap-2"><i class="fas fa-users text-blue-400"></i> User Management</h3>
            <div style="position:relative;">
                <i class="fas fa-search" style="position:absolute;left:.6rem;top:50%;transform:translateY(-50%);color:#6b7280;font-size:.75rem;"></i>
                <input type="text" id="usr-search" placeholder="Search by email or name…" style="padding:.4rem .75rem .4rem 2rem;background:#111827;border:1px solid #374151;border-radius:.5rem;color:white;font-size:.82rem;width:200px;" oninput="CMSPage._usrSearch(this.value)">
            </div>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
            <div class="ccard">
                <div class="chdr" style="margin-bottom:.75rem;padding-bottom:.5rem;">
                    <span class="text-white font-semibold text-sm"><i class="fas fa-bullhorn text-yellow-400 mr-2"></i>Announcements</span>
                    <button class="cb cb-p" style="font-size:.72rem;padding:.25rem .75rem;" onclick="CMSPage._addAnnouncement()"><i class="fas fa-plus"></i> New</button>
                </div>
                <div id="ann-list"><div class="text-gray-600 text-xs">Loading…</div></div>
            </div>
            <div class="ccard">
                <div class="chdr" style="margin-bottom:.75rem;padding-bottom:.5rem;">
                    <span class="text-white font-semibold text-sm"><i class="fas fa-tag text-green-400 mr-2"></i>Coupons</span>
                    <button class="cb cb-p" style="font-size:.72rem;padding:.25rem .75rem;" onclick="CMSPage._addCoupon()"><i class="fas fa-plus"></i> New</button>
                </div>
                <div id="coup-list"><div class="text-gray-600 text-xs">Loading…</div></div>
            </div>
        </div>
        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div id="usr-table-wrap" class="overflow-x-auto"></div>
            <div id="usr-pager" class="px-5 py-4 border-t border-gray-700 flex items-center justify-between"></div>
        </div>`;
        await Promise.all([this._loadUsersTable(1,''),this._loadAnnouncements(),this._loadCoupons()]);
    },

    _usrSearch: (()=>{ let t; return (v)=>{ clearTimeout(t); t=setTimeout(()=>CMSPage._loadUsersTable(1,v),350); }; })(),

    async _loadUsersTable(page,search){
        this._usersPage=page; this._usersSearch=search;
        const wrap=document.getElementById('usr-table-wrap'); const pager=document.getElementById('usr-pager');
        if(!wrap) return;
        wrap.innerHTML=`<div class="py-8 text-center text-gray-500 text-sm"><i class="fas fa-spinner fa-spin mr-2"></i>Loading…</div>`;
        try{
            const data=await API.cms.listUsers(page,search);
            const users=data.users||[]; const total=data.total||0; const pages=data.pages||1;
            wrap.innerHTML=`<table class="cms-tbl">
                <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Subscription</th><th>Status</th><th>Joined</th><th class="text-right">Actions</th></tr></thead>
                <tbody>${users.length?users.map(u=>`<tr>
                    <td class="text-white font-medium">${this._e(u.full_name||'—')}</td>
                    <td class="text-gray-400">${this._e(u.email)}</td>
                    <td>${this._role(u.display_role||u.role)}</td>
                    <td>${this._tier(u.subscription_tier)}</td>
                    <td>${this._pub(u.is_active,'Active','Banned')}</td>
                    <td class="text-gray-500">${this._d(u.created_at)}</td>
                    <td class="text-right">
                        <div style="display:flex;gap:.3rem;justify-content:flex-end;flex-wrap:wrap;">
                            <select class="cs" style="font-size:.72rem;padding:.2rem .4rem;width:100px;" onchange="CMSPage._setRole(${u.id},this.value)">
                                ${['user','moderator','admin'].map(r=>`<option value="${r}"${(u.display_role||u.role||'user')===r?' selected':''}>${r}</option>`).join('')}
                            </select>
                            <select class="cs" style="font-size:.72rem;padding:.2rem .4rem;width:100px;" onchange="CMSPage._setSub(${u.id},this.value)">
                                ${['free','pro','enterprise'].map(t=>`<option value="${t}"${(u.subscription_tier||'free')===t?' selected':''}>${t}</option>`).join('')}
                            </select>
                            <button class="cb ${u.is_active?'cb-r':'cb-gr'}" style="font-size:.7rem;padding:.22rem .6rem;" onclick="CMSPage._toggleUserStatus(${u.id})">${u.is_active?'Ban':'Unban'}</button>
                            <button class="cb cb-g" style="font-size:.7rem;padding:.22rem .6rem;" onclick="CMSPage._viewActivity(${u.id},'${this._e(u.email).replace(/'/g,"\\'")}')"><i class="fas fa-chart-bar"></i></button>
                        </div>
                    </td>
                </tr>`).join(''):`<tr><td colspan="7" class="text-center py-8 text-gray-500 text-sm">No users found</td></tr>`}
                </tbody>
            </table>`;
            if(pager) pager.innerHTML=`
                <span class="text-xs text-gray-500">${((page-1)*25)+1}–${Math.min(page*25,total)} of ${total}</span>
                <div class="flex gap-1">
                    <button onclick="CMSPage._loadUsersTable(${page-1},'${this._e(this._usersSearch)}')" ${page<=1?'disabled':''} class="cb cb-g" style="font-size:.72rem;padding:.2rem .6rem;">← Prev</button>
                    <span class="text-xs text-gray-500 px-2">${page}/${pages}</span>
                    <button onclick="CMSPage._loadUsersTable(${page+1},'${this._e(this._usersSearch)}')" ${page>=pages?'disabled':''} class="cb cb-g" style="font-size:.72rem;padding:.2rem .6rem;">Next →</button>
                </div>`;
        }catch(e){ wrap.innerHTML=`<div class="py-8 text-center text-red-400 text-sm">${this._e(e.message)}</div>`; }
    },

    async _setRole(id,role){ try{await API.cms.setUserRole(id,role);this._toast(`Role set to ${role}`);}catch(e){this._toast(e.message,'error');} },
    async _setSub(id,tier){ try{await API.cms.setUserSub(id,tier);this._toast(`Subscription set to ${tier}`);}catch(e){this._toast(e.message,'error');} },
    async _toggleUserStatus(id){ try{const r=await API.cms.toggleUser(id);this._toast(r.message);await this._loadUsersTable(this._usersPage,this._usersSearch);}catch(e){this._toast(e.message,'error');} },

    async _viewActivity(id,email){
        let a={}; try{a=await API.cms.getUserActivity(id);}catch(_){}
        const overlay=document.createElement('div');
        overlay.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9998;display:flex;align-items:center;justify-content:center;';
        overlay.innerHTML=`<div style="background:#1f2937;border:1px solid #374151;border-radius:.75rem;padding:1.5rem;width:min(480px,95vw);">
            <div class="chdr"><h4 class="text-white font-semibold">${this._e(email)}</h4>
            <button class="cb cb-g" onclick="this.closest('[style]').remove()"><i class="fas fa-times"></i></button></div>
            <div class="grid grid-cols-2 gap-3">
                ${[['fa-satellite-dish','Signals Created',a.signal_count||0],['fa-file-upload','Journal Uploads',a.journal_uploads||0],['fa-robot','AI Mentor Requests',a.mentor_requests||0],['fa-chart-bar','Charts Analyzed',a.charts_analyzed||0]].map(([ic,lb,v])=>`
                <div style="background:#111827;border:1px solid #374151;border-radius:.5rem;padding:.85rem;text-align:center;">
                    <i class="fas ${ic} text-purple-400 mb-1 block"></i>
                    <div class="text-2xl font-bold text-white">${v}</div>
                    <div class="text-xs text-gray-500">${lb}</div>
                </div>`).join('')}
            </div>
        </div>`;
        overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove();});
        document.body.appendChild(overlay);
    },

    async _loadAnnouncements(){
        const el=document.getElementById('ann-list'); if(!el) return;
        let anns=[]; try{anns=await API.cms.listAnnouncements();}catch(_){}
        const colors={info:'#60a5fa',warning:'#fbbf24',success:'#34d399',danger:'#f87171'};
        el.innerHTML=anns.length?anns.map(a=>`
        <div style="display:flex;align-items:center;gap:.5rem;padding:.4rem .5rem;border-radius:.4rem;background:#111827;margin-bottom:.35rem;border-left:3px solid ${colors[a.type]||colors.info};">
            <span class="text-xs text-gray-300 flex-1 truncate">${this._e(a.message)}</span>
            ${this._pub(a.is_active,'Live','Off')}
            <button class="cb cb-g" style="font-size:.68rem;padding:.15rem .45rem;" onclick="CMSPage._toggleAnn(${a.id})"><i class="fas fa-toggle-on"></i></button>
            <button class="cb cb-r" style="font-size:.68rem;padding:.15rem .45rem;" onclick="CMSPage._deleteAnn(${a.id})"><i class="fas fa-trash"></i></button>
        </div>`).join(''):`<div class="text-gray-600 text-xs">No announcements</div>`;
    },

    async _addAnnouncement(){
        const msg=prompt('Announcement message:',''); if(!msg) return;
        const type=prompt('Type (info/warning/success/danger):','info')||'info';
        try{await API.cms.createAnnouncement({message:msg,type,is_active:true});this._toast('Announcement created');await this._loadAnnouncements();}
        catch(e){this._toast(e.message,'error');}
    },
    async _toggleAnn(id){ try{await API.cms.toggleAnnouncement(id);await this._loadAnnouncements();}catch(e){this._toast(e.message,'error');} },
    async _deleteAnn(id){ if(!confirm('Delete?'))return; try{await API.cms.deleteAnnouncement(id);await this._loadAnnouncements();}catch(e){this._toast(e.message,'error');} },

    async _loadCoupons(){
        const el=document.getElementById('coup-list'); if(!el) return;
        let coupons=[]; try{coupons=await API.cms.listCoupons();}catch(_){}
        el.innerHTML=coupons.length?coupons.map(c=>`
        <div style="display:flex;align-items:center;gap:.5rem;padding:.4rem .5rem;border-radius:.4rem;background:#111827;margin-bottom:.35rem;">
            <span style="font-family:monospace;color:#a78bfa;font-size:.8rem;font-weight:700;">${this._e(c.code)}</span>
            <span class="text-gray-400 text-xs">${c.discount_type==='percent'?c.discount_value+'%':'$'+c.discount_value} off</span>
            <span class="text-gray-600 text-xs">${c.uses||0}/${c.max_uses} uses</span>
            ${this._pub(c.is_active,'Active','Off')}
            <button class="cb cb-g" style="font-size:.68rem;padding:.15rem .45rem;" onclick="CMSPage._toggleCoupon(${c.id})"><i class="fas fa-toggle-on"></i></button>
            <button class="cb cb-r" style="font-size:.68rem;padding:.15rem .45rem;" onclick="CMSPage._deleteCoupon(${c.id})"><i class="fas fa-trash"></i></button>
        </div>`).join(''):`<div class="text-gray-600 text-xs">No coupons</div>`;
    },

    async _addCoupon(){
        const code=prompt('Coupon code:','SUMMER25'); if(!code) return;
        const type=prompt('Type (percent/fixed):','percent')||'percent';
        const val=parseFloat(prompt('Discount value:','25')); if(isNaN(val)) return;
        try{await API.cms.createCoupon({code,discount_type:type,discount_value:val,max_uses:100,is_active:true});this._toast('Coupon created');await this._loadCoupons();}
        catch(e){this._toast(e.message,'error');}
    },
    async _toggleCoupon(id){ try{await API.cms.toggleCoupon(id);await this._loadCoupons();}catch(e){this._toast(e.message,'error');} },
    async _deleteCoupon(id){ if(!confirm('Delete coupon?'))return; try{await API.cms.deleteCoupon(id);await this._loadCoupons();}catch(e){this._toast(e.message,'error');} },

    // ═══════════════════════════════════════════════════════════════════════
    // MEDIA LIBRARY
    // ═══════════════════════════════════════════════════════════════════════
    async _media(callback=null){
        const pane=document.getElementById('cms-pane-media'); if(!pane&&!callback) return;
        let files=[]; try{files=await API.cms.listMedia();}catch(_){}
        const container=callback?document.createElement('div'):pane;
        container.innerHTML=`
        <div class="chdr">
            <h3 class="text-white font-semibold flex items-center gap-2"><i class="fas fa-photo-video text-green-400"></i> Media Library <span class="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">${files.length}</span></h3>
        </div>
        <div class="upload-zone" id="media-drop-zone" onclick="document.getElementById('media-file-input').click()">
            <input type="file" id="media-file-input" style="display:none;" multiple accept="image/*,video/mp4,application/pdf" onchange="CMSPage._uploadFiles(this.files)">
            <i class="fas fa-cloud-upload-alt text-3xl text-gray-600 mb-2"></i>
            <p class="text-gray-400 text-sm">Drop files here or click to upload</p>
            <p class="text-gray-600 text-xs mt-1">Images, Videos, PDFs — max 20 MB each</p>
        </div>
        <div id="media-upload-progress" style="display:none;" class="mt-2"></div>
        <div style="display:flex;gap:.5rem;margin:.75rem 0;flex-wrap:wrap;">
            ${['all','general','blog','courses','webinars'].map(f=>`<button class="cb cb-g" style="font-size:.72rem;" onclick="CMSPage._filterMedia('${f}')">${f}</button>`).join('')}
            ${callback?`<button class="cb cb-gr" style="margin-left:auto;" onclick="CMSPage._cancelMediaPick()">Cancel</button>`:''}
        </div>
        <div class="media-grid" id="media-grid">
            ${files.length?files.map(f=>this._mediaItem(f,callback)).join(''):`<div class="text-gray-600 text-sm col-span-full text-center py-6">No files yet — upload one above</div>`}
        </div>`;
        if(!callback) this._setupMediaDrop();
    },

    _mediaItem(f,callback=null){
        const isImg=/\.(jpg|jpeg|png|webp|gif|svg)/i.test(f.url);
        const isPdf=/\.pdf$/i.test(f.url);
        const isVid=/\.(mp4|webm)/i.test(f.url);
        const thumb=isImg?`<img src="${this._e(f.url)}" class="media-thumb" loading="lazy">`
            :`<div class="media-thumb" style="display:flex;align-items:center;justify-content:center;"><i class="fas ${isPdf?'fa-file-pdf text-red-400':isVid?'fa-film text-purple-400':'fa-file text-gray-500'} text-2xl"></i></div>`;
        const clickFn=callback
            ?`CMSPage._selectMedia('${this._e(f.url)}','${this._e(f.filename)}')`
            :`window.open('${this._e(f.url)}','_blank')`;
        return `<div class="media-item" onclick="${clickFn}" title="${this._e(f.original_name||f.filename)}">
            ${thumb}
            <div class="media-name">${this._e((f.original_name||f.filename||'').split('/').pop())}</div>
            ${!callback?`<div style="display:flex;justify-content:space-between;padding:.2rem .4rem;">
                <button class="cb cb-r" style="font-size:.65rem;padding:.1rem .4rem;" onclick="event.stopPropagation();CMSPage._deleteMedia('${this._e(f.filename)}')"><i class="fas fa-trash"></i></button>
                <button class="cb cb-g" style="font-size:.65rem;padding:.1rem .4rem;" onclick="event.stopPropagation();navigator.clipboard.writeText('${this._e(f.url)}');CMSPage._toast('URL copied')"><i class="fas fa-copy"></i></button>
            </div>`:''}
        </div>`;
    },

    _setupMediaDrop(){
        const zone=document.getElementById('media-drop-zone'); if(!zone) return;
        zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('drag-over');});
        zone.addEventListener('dragleave',()=>zone.classList.remove('drag-over'));
        zone.addEventListener('drop',e=>{e.preventDefault();zone.classList.remove('drag-over');this._uploadFiles(e.dataTransfer.files);});
    },

    async _uploadFiles(files){
        const prog=document.getElementById('media-upload-progress'); if(prog){prog.style.display='block';prog.innerHTML='';}
        const folder=this._activeTab==='blog'?'blog':this._activeTab==='lms'?'courses':this._activeTab==='webinars'?'webinars':'general';
        for(const file of files){
            const row=document.createElement('div');
            row.style.cssText='font-size:.78rem;color:#9ca3af;margin-bottom:.25rem;';
            row.innerHTML=`<i class="fas fa-spinner fa-spin mr-1"></i> Uploading ${this._e(file.name)}…`;
            if(prog) prog.appendChild(row);
            try{
                const fd=new FormData(); fd.append('file',file); fd.append('folder',folder);
                const r=await API.cms.uploadMedia(fd);
                row.innerHTML=`<i class="fas fa-check-circle text-green-400 mr-1"></i> ${this._e(file.name)} → <a href="${r.url}" target="_blank" class="text-purple-400">${r.url}</a>`;
            }catch(e){
                row.innerHTML=`<i class="fas fa-times-circle text-red-400 mr-1"></i> ${this._e(file.name)}: ${this._e(e.message)}`;
            }
        }
        await this._media();
    },

    async _filterMedia(folder){
        const grid=document.getElementById('media-grid'); if(!grid) return;
        grid.innerHTML='<div class="col-span-full text-gray-600 text-xs text-center py-4"><i class="fas fa-spinner fa-spin mr-1"></i>Loading…</div>';
        let files=[]; try{files=await API.cms.listMedia(folder==='all'?null:folder);}catch(_){}
        grid.innerHTML=files.length?files.map(f=>this._mediaItem(f)).join(''):'<div class="text-gray-600 text-sm col-span-full text-center py-6">No files in this folder</div>';
    },

    async _deleteMedia(fn){ if(!confirm('Delete this file permanently?'))return; try{await API.cms.deleteMedia(fn);this._toast('File deleted');await this._media();}catch(e){this._toast(e.message,'error');} },

    _pickMedia(targetInputId,folder=''){
        this._mediaCallback=targetInputId;
        const overlay=document.createElement('div');
        overlay.id='media-picker-overlay';
        overlay.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:9999;display:flex;align-items:flex-start;justify-content:center;padding:2rem;overflow-y:auto;';
        const inner=document.createElement('div');
        inner.style.cssText='background:#1f2937;border:1px solid #374151;border-radius:.75rem;padding:1.5rem;width:min(900px,95vw);';
        overlay.appendChild(inner);
        document.body.appendChild(overlay);
        overlay.addEventListener('click',e=>{if(e.target===overlay){overlay.remove();this._mediaCallback=null;}});
        this._renderMediaPicker(inner,folder);
    },

    async _renderMediaPicker(container,folder){
        let files=[]; try{files=await API.cms.listMedia(folder||null);}catch(_){}
        container.innerHTML=`
        <div class="chdr"><h4 class="text-white font-semibold"><i class="fas fa-images text-green-400 mr-2"></i>Select Media</h4>
            <button class="cb cb-g" onclick="document.getElementById('media-picker-overlay').remove();CMSPage._mediaCallback=null;"><i class="fas fa-times"></i></button></div>
        <div style="margin-bottom:.75rem;">
            <input type="file" id="picker-upload" style="display:none;" multiple accept="image/*,video/mp4,application/pdf" onchange="CMSPage._pickerUpload(this.files)">
            <button class="cb cb-p" onclick="document.getElementById('picker-upload').click()"><i class="fas fa-upload"></i> Upload New</button>
        </div>
        <div class="media-grid">${files.length?files.map(f=>this._mediaItem(f,'picker')).join(''):`<div class="text-gray-600 text-sm col-span-full text-center py-6">No files yet</div>`}</div>`;
    },

    async _pickerUpload(files){
        const folder='general'; const container=document.querySelector('#media-picker-overlay > div');
        for(const file of files){ try{const fd=new FormData();fd.append('file',file);fd.append('folder',folder);await API.cms.uploadMedia(fd);}catch(e){this._toast(e.message,'error');} }
        if(container) this._renderMediaPicker(container,folder);
    },

    _selectMedia(url,fn){
        const input=document.getElementById(this._mediaCallback);
        if(input){ input.value=url; input.dispatchEvent(new Event('input')); }
        document.getElementById('media-picker-overlay')?.remove();
        this._mediaCallback=null;
    },
    _cancelMediaPick(){ document.getElementById('media-picker-overlay')?.remove(); this._mediaCallback=null; },

    // ═══════════════════════════════════════════════════════════════════════
    // FEATURE LIMITS
    // ═══════════════════════════════════════════════════════════════════════
    async _limits(){
        const pane=document.getElementById('cms-pane-limits'); if(!pane) return;
        pane.innerHTML=`<div class="text-gray-400 text-sm text-center py-6"><i class="fas fa-spinner fa-spin mr-2"></i>Loading…</div>`;
        let s={}; try{s=await API.cms.getSettings();}catch(_){}
        const g=(k,fb='')=>this._e(s[k]!=null?s[k]:fb);
        const features=[
            {key:'chart_analysis',label:'Chart Analysis',icon:'fa-chart-bar',color:'#60a5fa',desc:'AI chart analyses per day',fields:[{k:'chart_free_daily',label:'Free tier — per day',type:'number',default:'2'},{k:'chart_pro_daily',label:'Pro tier — per day',type:'number',default:'50'}]},
            {key:'performance',label:'Performance Analytics',icon:'fa-chart-line',color:'#f59e0b',desc:'Trade journal uploads per month',fields:[{k:'journal_free_imports',label:'Free tier — per month',type:'number',default:'1'},{k:'journal_pro_imports',label:'Pro tier — per month',type:'number',default:'999'}]},
            {key:'ai_mentor',label:'AI Mentor',icon:'fa-robot',color:'#f472b6',desc:'Questions per day',fields:[{k:'mentor_free_daily',label:'Free tier — per day',type:'number',default:'5'},{k:'mentor_pro_daily',label:'Pro tier — per day',type:'number',default:'200'}]},
            {key:'ai_stock',label:'AI Stock Research',icon:'fa-chart-pie',color:'#34d399',desc:'Stock queries per day',fields:[{k:'stock_free_daily',label:'Free tier — per day',type:'number',default:'3'},{k:'stock_pro_daily',label:'Pro tier — per day',type:'number',default:'100'}]},
            {key:'signals',label:'Trading Signals',icon:'fa-satellite-dish',color:'#a78bfa',desc:'Max visible signals per tier',fields:[{k:'signals_free_limit',label:'Free tier — max signals',type:'number',default:'3'},{k:'signals_pro_limit',label:'Pro tier — max signals',type:'number',default:'999'}]},
            {key:'webinars',label:'Webinars',icon:'fa-video',color:'#fb923c',desc:'Registrations per month',fields:[{k:'webinar_free_limit',label:'Free tier — per month',type:'number',default:'1'},{k:'webinar_pro_limit',label:'Pro tier — per month',type:'number',default:'999'}]},
            {key:'blog',label:'Blog',icon:'fa-newspaper',color:'#2dd4bf',desc:'Articles visible to free tier',fields:[{k:'blog_free_limit',label:'Free tier — articles visible',type:'number',default:'10'}]},
        ];
        pane.innerHTML=`
        <div class="chdr">
            <h3 class="text-white font-semibold flex items-center gap-2"><i class="fas fa-sliders-h text-purple-400"></i> Feature Limits by Tier</h3>
            <button class="cb cb-p" onclick="CMSPage._saveLimits()"><i class="fas fa-save"></i> Save All Limits</button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${features.map(f=>`
            <div class="ccard" style="border-color:${f.color}33;">
                <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem;">
                    <div style="width:38px;height:38px;border-radius:.5rem;background:${f.color}20;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <i class="fas ${f.icon}" style="color:${f.color};font-size:.95rem;"></i>
                    </div>
                    <div><div class="text-white font-semibold text-sm">${f.label}</div><div class="text-gray-500 text-xs">${f.desc}</div></div>
                </div>
                ${f.fields.map(fd=>`
                <div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-bottom:.6rem;">
                    <label class="text-xs text-gray-400" style="flex:1;">${fd.label}</label>
                    <input type="${fd.type||'number'}" class="ci" id="lim-${fd.k}" value="${g(fd.k,fd.default)}" style="max-width:90px;text-align:right;padding:.35rem .6rem;" min="0">
                </div>`).join('')}
                <div style="margin-top:.75rem;padding-top:.65rem;border-top:1px solid #374151;display:flex;align-items:center;gap:.5rem;">
                    <label class="ctog" onclick="CMSPage._togCheck('lim-${f.key}_enabled')">
                        <div class="ttrack${s[f.key+'_enabled']==='false'?'':' on'}"><div class="tthumb"></div></div>
                        <input type="hidden" id="lim-${f.key}_enabled" value="${s[f.key+'_enabled']==='false'?'0':'1'}">
                    </label>
                    <span class="text-xs text-gray-500">Feature enabled for all tiers</span>
                </div>
            </div>`).join('')}
        </div>`;
    },

    async _saveLimits(){
        const updates={};
        document.querySelectorAll('[id^="lim-"]').forEach(el=>{ updates[el.id.slice(4)]=el.value; });
        try{await API.cms.saveSettings(updates);this._toast('Feature limits saved');}
        catch(e){this._toast(e.message,'error');}
    },

    // ═══════════════════════════════════════════════════════════════════════
    // SETTINGS
    // ═══════════════════════════════════════════════════════════════════════
    async _settings(){
        const pane=document.getElementById('cms-pane-settings'); if(!pane) return;
        pane.innerHTML=`<div class="text-gray-400 text-sm text-center py-8"><i class="fas fa-spinner fa-spin mr-2"></i>Loading settings…</div>`;
        let s={}; try{s=await API.cms.getSettings();}catch(_){}
        const g=(k,fb='')=>this._e(s[k]!=null?s[k]:fb);
        pane.innerHTML=`
        <div class="chdr">
            <h3 class="text-white font-semibold flex items-center gap-2"><i class="fas fa-cog text-yellow-400"></i> Site Settings</h3>
            <button class="cb cb-p" onclick="CMSPage._saveSettings()"><i class="fas fa-save"></i> Save All</button>
        </div>
        <div class="sg"><div class="sg-hdr"><i class="fas fa-globe mr-2"></i>General</div>
            <div class="sg-row"><div><div class="sg-lbl">Site Name</div></div><input class="ci" style="max-width:260px;" id="s-site_name" value="${g('site_name','Gopipways')}"></div>
            <div class="sg-row"><div><div class="sg-lbl">Tagline</div></div><input class="ci" style="max-width:320px;" id="s-site_tagline" value="${g('site_tagline')}"></div>
            <div class="sg-row"><div><div class="sg-lbl">Footer Text</div></div><input class="ci" style="max-width:360px;" id="s-footer_text" value="${g('footer_text')}"></div>
            <div class="sg-row"><div><div class="sg-lbl">Currency</div></div><select class="cs" style="max-width:100px;" id="s-currency">${['USD','EUR','GBP','NGN','ZAR','AED'].map(c=>`<option${s.currency===c?' selected':''}>${c}</option>`).join('')}</select></div>
            <div class="sg-row"><div><div class="sg-lbl">Timezone</div></div><select class="cs" style="max-width:220px;" id="s-timezone">${['UTC','America/New_York','America/Los_Angeles','Europe/London','Europe/Berlin','Asia/Dubai','Africa/Lagos'].map(t=>`<option value="${t}"${s.timezone===t?' selected':''}>${t}</option>`).join('')}</select></div>
        </div>
        <div class="sg"><div class="sg-hdr"><i class="fas fa-envelope mr-2"></i>Contact &amp; Email</div>
            <div class="sg-row"><div><div class="sg-lbl">Contact Email</div></div><input class="ci" style="max-width:280px;" id="s-contact_email" value="${g('contact_email')}"></div>
            <div class="sg-row"><div><div class="sg-lbl">Support Email</div></div><input class="ci" style="max-width:280px;" id="s-support_email" value="${g('support_email')}"></div>
        </div>
        <div class="sg"><div class="sg-hdr"><i class="fas fa-palette mr-2"></i>Branding</div>
            <div class="sg-row"><div><div class="sg-lbl">Logo URL</div></div>
                <div style="display:flex;gap:.4rem;"><input class="ci" style="max-width:300px;" id="s-logo_url" value="${g('logo_url')}"><button class="cb cb-g" onclick="CMSPage._pickMedia('s-logo_url')"><i class="fas fa-images"></i></button></div></div>
            <div class="sg-row"><div><div class="sg-lbl">Favicon URL</div></div>
                <div style="display:flex;gap:.4rem;"><input class="ci" style="max-width:300px;" id="s-favicon_url" value="${g('favicon_url')}"><button class="cb cb-g" onclick="CMSPage._pickMedia('s-favicon_url')"><i class="fas fa-images"></i></button></div></div>
            <div class="sg-row"><div><div class="sg-lbl">Analytics ID</div><div class="sg-desc">Google Analytics GA4</div></div><input class="ci" style="max-width:180px;" id="s-analytics_id" value="${g('analytics_id')}" placeholder="G-XXXXXXXXXX"></div>
        </div>
        <div class="sg"><div class="sg-hdr"><i class="fas fa-share-alt mr-2"></i>Social Media</div>
            ${[['twitter_url','fab fa-twitter','Twitter / X'],['instagram_url','fab fa-instagram','Instagram'],['telegram_url','fab fa-telegram','Telegram'],['youtube_url','fab fa-youtube','YouTube'],['discord_url','fab fa-discord','Discord']].map(([k,ic,lb])=>`
            <div class="sg-row"><div><div class="sg-lbl"><i class="${ic} mr-1"></i>${lb}</div></div><input class="ci" style="max-width:300px;" id="s-${k}" value="${g(k)}" placeholder="https://…"></div>`).join('')}
        </div>
        <div class="sg"><div class="sg-hdr"><i class="fas fa-sliders-h mr-2"></i>Platform Controls</div>
            <div class="sg-row"><div><div class="sg-lbl">Maintenance Mode</div><div class="sg-desc">Redirects visitors to maintenance page</div></div>
                <label class="ctog" onclick="CMSPage._togCheck('s-maintenance_mode','true','false')">
                    <div class="ttrack${s.maintenance_mode==='true'?' on':''}"><div class="tthumb"></div></div>
                    <input type="hidden" id="s-maintenance_mode" value="${g('maintenance_mode','false')}">
                </label></div>
            <div class="sg-row"><div><div class="sg-lbl">Allow Registration</div></div>
                <label class="ctog" onclick="CMSPage._togCheck('s-allow_registration','true','false')">
                    <div class="ttrack${s.allow_registration!=='false'?' on':''}"><div class="tthumb"></div></div>
                    <input type="hidden" id="s-allow_registration" value="${g('allow_registration','true')}">
                </label></div>
            <div class="sg-row"><div><div class="sg-lbl">Free Signal Limit</div></div><input type="number" class="ci" style="max-width:80px;" id="s-free_signals_limit" value="${g('free_signals_limit','3')}" min="0"></div>
        </div>
        <div style="display:flex;justify-content:flex-end;margin-top:1rem;">
            <button class="cb cb-p" style="padding:.6rem 1.5rem;font-size:.9rem;" onclick="CMSPage._saveSettings()"><i class="fas fa-save mr-2"></i>Save All Changes</button>
        </div>`;
    },

    async _saveSettings(){
        const updates={};
        document.querySelectorAll('[id^="s-"]').forEach(el=>{ updates[el.id.slice(2)]=el.value; });
        try{await API.cms.saveSettings(updates);this._toast('Settings saved');}
        catch(e){this._toast(e.message,'error');}
    },

    // ── Universal toggle helper ───────────────────────────────────────────
    _togCheck(id, onVal='1', offVal='0'){
        const el=document.getElementById(id); if(!el) return;
        const isOn=el.value===onVal;
        el.value=isOn?offVal:onVal;
        const track=el.closest('label')?.querySelector('.ttrack')||el.closest('[class*="ctog"]')?.querySelector('.ttrack');
        if(track) track.classList.toggle('on',!isOn);
    },
};
