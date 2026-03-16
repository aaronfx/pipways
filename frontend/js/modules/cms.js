/**
 * cms.js — Content Management System Module
 * frontend/js/modules/cms.js  →  served at /js/modules/cms.js
 *
 * Five tabs: Blog · Courses/LMS · Signals · Webinars · Settings
 * Depends on: window.dashboard, window.API
 */

// ── CMS API methods ────────────────────────────────────────────────────────────
API.cms = {
    // Blog
    listPosts:      ()       => dashboard.apiRequest('/cms/blog'),
    getPost:        (id)     => dashboard.apiRequest(`/cms/blog/${id}`),
    createPost:     (data)   => dashboard.apiRequest('/cms/blog', { method:'POST', body:JSON.stringify(data) }),
    updatePost:     (id, d)  => dashboard.apiRequest(`/cms/blog/${id}`, { method:'PUT', body:JSON.stringify(d) }),
    deletePost:     (id)     => dashboard.apiRequest(`/cms/blog/${id}`, { method:'DELETE' }),
    togglePost:     (id)     => dashboard.apiRequest(`/cms/blog/${id}/toggle-publish`, { method:'POST' }),
    // Courses
    listCourses:    ()       => dashboard.apiRequest('/cms/courses'),
    listLessons:    (cid)    => dashboard.apiRequest(`/cms/courses/${cid}/lessons`),
    createCourse:   (data)   => dashboard.apiRequest('/cms/courses', { method:'POST', body:JSON.stringify(data) }),
    updateCourse:   (id, d)  => dashboard.apiRequest(`/cms/courses/${id}`, { method:'PUT', body:JSON.stringify(d) }),
    deleteCourse:   (id)     => dashboard.apiRequest(`/cms/courses/${id}`, { method:'DELETE' }),
    toggleCourse:   (id)     => dashboard.apiRequest(`/cms/courses/${id}/toggle-publish`, { method:'POST' }),
    createLesson:   (data)   => dashboard.apiRequest('/cms/lessons', { method:'POST', body:JSON.stringify(data) }),
    updateLesson:   (id, d)  => dashboard.apiRequest(`/cms/lessons/${id}`, { method:'PUT', body:JSON.stringify(d) }),
    deleteLesson:   (id)     => dashboard.apiRequest(`/cms/lessons/${id}`, { method:'DELETE' }),
    // Signals
    listSignals:    ()       => dashboard.apiRequest('/cms/signals'),
    createSignal:   (data)   => dashboard.apiRequest('/cms/signals', { method:'POST', body:JSON.stringify(data) }),
    updateSignal:   (id, d)  => dashboard.apiRequest(`/cms/signals/${id}`, { method:'PUT', body:JSON.stringify(d) }),
    deleteSignal:   (id)     => dashboard.apiRequest(`/cms/signals/${id}`, { method:'DELETE' }),
    closeSignal:    (id, o)  => dashboard.apiRequest(`/cms/signals/${id}/close?outcome=${o}`, { method:'POST' }),
    // Webinars
    listWebinars:   ()       => dashboard.apiRequest('/cms/webinars'),
    createWebinar:  (data)   => dashboard.apiRequest('/cms/webinars', { method:'POST', body:JSON.stringify(data) }),
    updateWebinar:  (id, d)  => dashboard.apiRequest(`/cms/webinars/${id}`, { method:'PUT', body:JSON.stringify(d) }),
    deleteWebinar:  (id)     => dashboard.apiRequest(`/cms/webinars/${id}`, { method:'DELETE' }),
    toggleWebinar:  (id)     => dashboard.apiRequest(`/cms/webinars/${id}/toggle-publish`, { method:'POST' }),
    // Settings
    getSettings:    ()       => dashboard.apiRequest('/cms/settings'),
    saveSettings:   (data)   => dashboard.apiRequest('/cms/settings', { method:'PUT', body:JSON.stringify(data) }),
};

// ── CMSPage module ─────────────────────────────────────────────────────────────
const CMSPage = {
    _container: null,
    _activeTab: 'blog',
    _editingId: null,         // id of row being edited (null = create mode)
    _lessonCourseId: null,    // course expanded for lesson editor

    // ── Helpers ──────────────────────────────────────────────────────────────
    _esc(s){ return s==null?'':String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); },
    _date(s){ if(!s) return '—'; try{ return new Date(s).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}); }catch(_){return s;} },
    _dt(s){ if(!s) return ''; try{ return new Date(s).toISOString().slice(0,16); }catch(_){return '';} },
    _badge(on, onLabel='Published', offLabel='Draft'){
        return on
            ? `<span style="background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.3);padding:.15rem .55rem;border-radius:9999px;font-size:.7rem;font-weight:700;">${onLabel}</span>`
            : `<span style="background:rgba(107,114,128,.15);color:#9ca3af;border:1px solid rgba(107,114,128,.3);padding:.15rem .55rem;border-radius:9999px;font-size:.7rem;font-weight:700;">${offLabel}</span>`;
    },
    _dirBadge(dir){
        const up = (dir||'').toUpperCase() === 'BUY';
        return `<span style="background:${up?'rgba(16,185,129,.15)':'rgba(239,68,68,.15)'};color:${up?'#34d399':'#f87171'};border:1px solid ${up?'rgba(16,185,129,.3)':'rgba(239,68,68,.3)'};padding:.15rem .55rem;border-radius:9999px;font-size:.7rem;font-weight:700;">${dir||'—'}</span>`;
    },
    _statusBadge(s){
        const colors = { active:'rgba(16,185,129,.15)', closed:'rgba(107,114,128,.15)', cancelled:'rgba(239,68,68,.15)' };
        const texts  = { active:'#34d399', closed:'#9ca3af', cancelled:'#f87171' };
        const borders= { active:'rgba(16,185,129,.3)', closed:'rgba(107,114,128,.3)', cancelled:'rgba(239,68,68,.3)' };
        const k = (s||'active').toLowerCase();
        return `<span style="background:${colors[k]||colors.active};color:${texts[k]||texts.active};border:1px solid ${borders[k]||borders.active};padding:.15rem .55rem;border-radius:9999px;font-size:.7rem;font-weight:700;">${k}</span>`;
    },

    _toast(msg, type='success'){
        const d = document.createElement('div');
        d.style.cssText=`position:fixed;bottom:1.5rem;right:1.5rem;z-index:99999;
            padding:.75rem 1.25rem;border-radius:.75rem;font-size:.85rem;font-weight:600;
            color:white;max-width:320px;
            background:${type==='success'?'rgba(16,185,129,.95)':type==='error'?'rgba(239,68,68,.95)':'rgba(59,130,246,.95)'};
            box-shadow:0 8px 24px rgba(0,0,0,.4);`;
        d.textContent=msg;
        document.body.appendChild(d);
        setTimeout(()=>d.remove(),3500);
    },

    _confirm(msg){ return confirm(msg); },

    // ── Entry point ───────────────────────────────────────────────────────────
    async render(container){
        if(!container) return;
        this._container = container;
        container.innerHTML = this._shell();
        this._setupTabs();
        await this._loadTab(this._activeTab);
    },

    _shell(){
        const tabs = [
            { id:'blog',     icon:'fa-newspaper',   label:'Blog Posts' },
            { id:'courses',  icon:'fa-graduation-cap', label:'Courses / LMS' },
            { id:'signals',  icon:'fa-satellite-dish', label:'Signals' },
            { id:'webinars', icon:'fa-video',        label:'Webinars' },
            { id:'settings', icon:'fa-cog',          label:'Site Settings' },
        ];
        return `
        <style>
            .cms-tab{padding:.45rem 1rem;border-radius:.6rem;font-size:.82rem;font-weight:600;
                border:none;cursor:pointer;color:#9ca3af;background:transparent;transition:all .18s;white-space:nowrap;}
            .cms-tab.active{background:linear-gradient(135deg,#7c3aed,#6d28d9);color:white;box-shadow:0 4px 12px rgba(124,58,237,.35);}
            .cms-tab:not(.active):hover{background:#374151;color:white;}
            .cms-pane{display:none;}.cms-pane.visible{display:block;}
            .cms-table{width:100%;border-collapse:collapse;}
            .cms-table th{padding:.6rem .85rem;text-align:left;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#6b7280;background:#111827;}
            .cms-table td{padding:.6rem .85rem;font-size:.82rem;border-bottom:1px solid #1f2937;vertical-align:middle;}
            .cms-table tr:hover td{background:rgba(124,58,237,.04);}
            .cms-btn{display:inline-flex;align-items:center;gap:.35rem;padding:.35rem .85rem;border-radius:.5rem;font-size:.78rem;font-weight:600;border:none;cursor:pointer;transition:all .18s;}
            .cms-btn-purple{background:linear-gradient(135deg,#7c3aed,#6d28d9);color:white;}
            .cms-btn-purple:hover{opacity:.9;transform:translateY(-1px);}
            .cms-btn-gray{background:#374151;color:#d1d5db;border:1px solid #4b5563;}
            .cms-btn-gray:hover{background:#4b5563;color:white;}
            .cms-btn-red{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3);}
            .cms-btn-red:hover{background:rgba(239,68,68,.3);}
            .cms-btn-green{background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.3);}
            .cms-btn-green:hover{background:rgba(16,185,129,.3);}
            .cms-form-row{display:grid;gap:.75rem;margin-bottom:.75rem;}
            .cms-form-row.cols-2{grid-template-columns:1fr 1fr;}
            .cms-form-row.cols-3{grid-template-columns:1fr 1fr 1fr;}
            .cms-input{width:100%;background:#111827;border:1px solid #374151;border-radius:.5rem;padding:.5rem .75rem;color:white;font-size:.875rem;box-sizing:border-box;}
            .cms-input:focus{outline:none;border-color:#7c3aed;}
            .cms-textarea{width:100%;background:#111827;border:1px solid #374151;border-radius:.5rem;padding:.5rem .75rem;color:white;font-size:.875rem;box-sizing:border-box;resize:vertical;min-height:160px;}
            .cms-textarea:focus{outline:none;border-color:#7c3aed;}
            .cms-select{width:100%;background:#111827;border:1px solid #374151;border-radius:.5rem;padding:.5rem .75rem;color:white;font-size:.875rem;box-sizing:border-box;}
            .cms-select:focus{outline:none;border-color:#7c3aed;}
            .cms-label{display:block;font-size:.78rem;color:#9ca3af;margin-bottom:.35rem;font-weight:500;}
            .cms-card{background:#1f2937;border:1px solid #374151;border-radius:.75rem;padding:1.25rem;margin-bottom:1rem;}
            .cms-section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;padding-bottom:.75rem;border-bottom:1px solid #374151;}
            .cms-toggle{display:flex;align-items:center;gap:.5rem;cursor:pointer;}
            .toggle-track{width:40px;height:22px;border-radius:11px;background:#374151;position:relative;transition:background .2s;}
            .toggle-track.on{background:#7c3aed;}
            .toggle-thumb{width:16px;height:16px;border-radius:50%;background:white;position:absolute;top:3px;left:3px;transition:left .2s;}
            .toggle-track.on .toggle-thumb{left:21px;}
            .settings-group{background:#1f2937;border:1px solid #374151;border-radius:.75rem;overflow:hidden;margin-bottom:1rem;}
            .settings-group-header{padding:.75rem 1rem;background:#111827;font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#6b7280;}
            .settings-row{display:flex;align-items:center;justify-content:space-between;padding:.75rem 1rem;border-bottom:1px solid #1f2937;gap:1rem;}
            .settings-row:last-child{border-bottom:none;}
            .settings-label{font-size:.85rem;color:#e5e7eb;font-weight:500;min-width:180px;}
            .settings-desc{font-size:.75rem;color:#6b7280;margin-top:.1rem;}
            .cms-editor-wrap{border:1px solid #374151;border-radius:.5rem;overflow:hidden;}
            .cms-editor-toolbar{background:#111827;padding:.5rem .75rem;display:flex;gap:.5rem;flex-wrap:wrap;border-bottom:1px solid #374151;}
            .editor-btn{background:#374151;color:#d1d5db;border:none;border-radius:.35rem;padding:.25rem .55rem;font-size:.78rem;cursor:pointer;}
            .editor-btn:hover{background:#4b5563;color:white;}
        </style>

        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-6">
            <div>
                <h2 class="text-2xl font-bold text-white flex items-center gap-2">
                    <i class="fas fa-layer-group text-purple-400"></i> Content Management
                </h2>
                <p class="text-sm text-gray-500 mt-0.5">Manage blog, courses, signals, webinars &amp; site settings</p>
            </div>
        </div>

        <div class="flex gap-1 mb-6 p-1 rounded-xl bg-gray-800/60 border border-gray-700 w-fit flex-wrap">
            ${tabs.map(t=>`<button class="cms-tab${t.id===this._activeTab?' active':''}" data-tab="${t.id}">
                <i class="fas ${t.icon} mr-1.5"></i>${t.label}
            </button>`).join('')}
        </div>

        ${tabs.map(t=>`<div id="cms-pane-${t.id}" class="cms-pane${t.id===this._activeTab?' visible':''}"></div>`).join('')}`;
    },

    _setupTabs(){
        document.querySelectorAll('.cms-tab').forEach(btn=>{
            btn.addEventListener('click', async ()=>{
                document.querySelectorAll('.cms-tab').forEach(b=>b.classList.remove('active'));
                document.querySelectorAll('.cms-pane').forEach(p=>p.classList.remove('visible'));
                btn.classList.add('active');
                this._activeTab = btn.dataset.tab;
                document.getElementById(`cms-pane-${btn.dataset.tab}`)?.classList.add('visible');
                await this._loadTab(btn.dataset.tab);
            });
        });
    },

    async _loadTab(tab){
        switch(tab){
            case 'blog':     await this._renderBlog();     break;
            case 'courses':  await this._renderCourses();  break;
            case 'signals':  await this._renderSignals();  break;
            case 'webinars': await this._renderWebinars(); break;
            case 'settings': await this._renderSettings(); break;
        }
    },

    // ══════════════════════════════════════════════════════════════════════════
    // BLOG
    // ══════════════════════════════════════════════════════════════════════════
    async _renderBlog(editData=null){
        const pane = document.getElementById('cms-pane-blog');
        if(!pane) return;

        // Load posts list
        let posts = [];
        try{ posts = await API.cms.listPosts(); } catch(_){}

        pane.innerHTML = `
        <div class="cms-section-header">
            <h3 class="text-white font-semibold flex items-center gap-2">
                <i class="fas fa-newspaper text-blue-400"></i> Blog Posts
                <span style="background:#374151;color:#9ca3af;padding:.1rem .55rem;border-radius:9999px;font-size:.72rem;">${posts.length}</span>
            </h3>
            <button class="cms-btn cms-btn-purple" onclick="CMSPage._openBlogForm()">
                <i class="fas fa-plus"></i> New Post
            </button>
        </div>

        <div id="cms-blog-form" style="display:none;" class="cms-card mb-4"></div>

        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="cms-table">
                    <thead><tr>
                        <th>Title</th><th>Category</th><th>Status</th>
                        <th>Views</th><th>Created</th><th class="text-right">Actions</th>
                    </tr></thead>
                    <tbody id="cms-blog-tbody">
                        ${posts.length
                            ? posts.map(p=>`
                            <tr>
                                <td>
                                    <div class="text-white font-medium text-sm">${this._esc(p.title)}</div>
                                    <div class="text-gray-600 text-xs font-mono">/${this._esc(p.slug)}</div>
                                </td>
                                <td class="text-gray-400">${this._esc(p.category||'General')}</td>
                                <td>${this._badge(p.is_published)}</td>
                                <td class="text-gray-400">${p.views||0}</td>
                                <td class="text-gray-500">${this._date(p.created_at)}</td>
                                <td class="text-right">
                                    <div style="display:flex;gap:.35rem;justify-content:flex-end;">
                                        <button class="cms-btn cms-btn-gray" onclick="CMSPage._openBlogForm(${p.id})">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="cms-btn ${p.is_published?'cms-btn-gray':'cms-btn-green'}"
                                                onclick="CMSPage._toggleBlogPost(${p.id},this)">
                                            ${p.is_published?'Unpublish':'Publish'}
                                        </button>
                                        <button class="cms-btn cms-btn-red" onclick="CMSPage._deleteBlogPost(${p.id})">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>`).join('')
                            : '<tr><td colspan="6" class="text-center py-8 text-gray-500 text-sm"><i class="fas fa-newspaper text-2xl block mb-2 opacity-30"></i>No posts yet. Create your first one.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>`;
    },

    async _openBlogForm(id=null){
        this._editingId = id;
        let data = { title:'', slug:'', excerpt:'', content:'', category:'General', tags:'', featured_image:'', is_published:false };
        if(id){ try{ data = await API.cms.getPost(id); data.tags = (data.tags||[]).join(', '); } catch(_){} }

        const formDiv = document.getElementById('cms-blog-form');
        if(!formDiv) return;
        formDiv.style.display = 'block';
        formDiv.innerHTML = `
            <div class="cms-section-header">
                <h4 class="text-white font-semibold">${id?'Edit Post':'New Post'}</h4>
                <button class="cms-btn cms-btn-gray" onclick="CMSPage._closeBlogForm()">
                    <i class="fas fa-times"></i> Cancel
                </button>
            </div>
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">Title *</label>
                    <input class="cms-input" id="bf-title" value="${this._esc(data.title)}" placeholder="Post title"></div>
                <div><label class="cms-label">Slug *</label>
                    <input class="cms-input" id="bf-slug" value="${this._esc(data.slug)}" placeholder="url-friendly-slug"></div>
            </div>
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">Category</label>
                    <select class="cms-select" id="bf-category">
                        ${['General','Strategy','Analysis','Psychology','Risk Management','SMC','Forex','Crypto','Indices']
                            .map(c=>`<option value="${c}" ${data.category===c?'selected':''}>${c}</option>`).join('')}
                    </select></div>
                <div><label class="cms-label">Tags (comma separated)</label>
                    <input class="cms-input" id="bf-tags" value="${this._esc(Array.isArray(data.tags)?data.tags.join(', '):data.tags)}" placeholder="forex, strategy, smc"></div>
            </div>
            <div class="cms-form-row">
                <div><label class="cms-label">Excerpt</label>
                    <input class="cms-input" id="bf-excerpt" value="${this._esc(data.excerpt)}" placeholder="Short description for listings"></div>
            </div>
            <div class="cms-form-row">
                <div><label class="cms-label">Featured Image URL</label>
                    <input class="cms-input" id="bf-img" value="${this._esc(data.featured_image)}" placeholder="https://..."></div>
            </div>
            <div class="cms-form-row">
                <div>
                    <label class="cms-label">Content (Markdown supported)</label>
                    <div class="cms-editor-wrap">
                        <div class="cms-editor-toolbar">
                            ${[['bold','B'],['italic','I'],['h2','H2'],['h3','H3'],['link','🔗'],['ul','• List'],['blockquote','❝']].map(([cmd,label])=>
                                `<button type="button" class="editor-btn" onclick="CMSPage._fmt('${cmd}')">${label}</button>`).join('')}
                        </div>
                        <textarea class="cms-textarea" id="bf-content" style="border-radius:0;border:none;">${this._esc(data.content)}</textarea>
                    </div>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:1.5rem;margin-top:.5rem;">
                <label class="cms-toggle" onclick="CMSPage._toggleCheck('bf-published')">
                    <div class="toggle-track${data.is_published?' on':''}"><div class="toggle-thumb"></div></div>
                    <span class="text-sm text-gray-300">Published</span>
                    <input type="hidden" id="bf-published" value="${data.is_published?'1':'0'}">
                </label>
                <button class="cms-btn cms-btn-purple" onclick="CMSPage._saveBlogPost()">
                    <i class="fas fa-save"></i> ${id?'Update Post':'Create Post'}
                </button>
            </div>`;

        formDiv.scrollIntoView({ behavior:'smooth', block:'start' });

        // Auto-generate slug from title
        document.getElementById('bf-title').addEventListener('input', e=>{
            if(!id){
                document.getElementById('bf-slug').value = e.target.value
                    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g,'').replace(/\s+/g,'-').replace(/-+/g,'-');
            }
        });
    },

    _closeBlogForm(){
        const f = document.getElementById('cms-blog-form');
        if(f){ f.style.display='none'; f.innerHTML=''; }
        this._editingId = null;
    },

    async _saveBlogPost(){
        const title    = document.getElementById('bf-title')?.value.trim();
        const slug     = document.getElementById('bf-slug')?.value.trim();
        const content  = document.getElementById('bf-content')?.value.trim();
        if(!title||!slug||!content){ this._toast('Title, slug and content are required','error'); return; }
        const payload = {
            title, slug,
            excerpt:       document.getElementById('bf-excerpt')?.value||'',
            content,
            category:      document.getElementById('bf-category')?.value||'General',
            tags:          (document.getElementById('bf-tags')?.value||'').split(',').map(t=>t.trim()).filter(Boolean),
            featured_image:document.getElementById('bf-img')?.value||'',
            is_published:  document.getElementById('bf-published')?.value==='1',
        };
        try{
            if(this._editingId){ await API.cms.updatePost(this._editingId, payload); this._toast('Post updated'); }
            else               { await API.cms.createPost(payload);                  this._toast('Post created'); }
            this._closeBlogForm();
            await this._renderBlog();
        } catch(e){ this._toast(e.message,'error'); }
    },

    async _toggleBlogPost(id, btn){
        try{
            const r = await API.cms.togglePost(id);
            this._toast(r.message);
            await this._renderBlog();
        } catch(e){ this._toast(e.message,'error'); }
    },

    async _deleteBlogPost(id){
        if(!this._confirm('Delete this post? This cannot be undone.')) return;
        try{ await API.cms.deletePost(id); this._toast('Post deleted'); await this._renderBlog(); }
        catch(e){ this._toast(e.message,'error'); }
    },

    // Text editor helpers
    _fmt(cmd){
        const ta = document.getElementById('bf-content');
        if(!ta) return;
        const s = ta.selectionStart, e = ta.selectionEnd, sel = ta.value.slice(s,e);
        const wrap = { bold:`**${sel}**`, italic:`_${sel}_`, link:`[${sel}](url)`,
                       h2:`## ${sel}`, h3:`### ${sel}`, ul:`- ${sel}`, blockquote:`> ${sel}` };
        const rep = wrap[cmd] || sel;
        ta.value = ta.value.slice(0,s) + rep + ta.value.slice(e);
        ta.focus();
    },

    // ══════════════════════════════════════════════════════════════════════════
    // COURSES / LMS
    // ══════════════════════════════════════════════════════════════════════════
    async _renderCourses(){
        const pane = document.getElementById('cms-pane-courses');
        if(!pane) return;
        let courses = [];
        try{ courses = await API.cms.listCourses(); } catch(_){}

        pane.innerHTML = `
        <div class="cms-section-header">
            <h3 class="text-white font-semibold flex items-center gap-2">
                <i class="fas fa-graduation-cap text-blue-400"></i> Courses
                <span style="background:#374151;color:#9ca3af;padding:.1rem .55rem;border-radius:9999px;font-size:.72rem;">${courses.length}</span>
            </h3>
            <button class="cms-btn cms-btn-purple" onclick="CMSPage._openCourseForm()">
                <i class="fas fa-plus"></i> New Course
            </button>
        </div>

        <div id="cms-course-form" style="display:none;" class="cms-card mb-4"></div>
        <div id="cms-lesson-editor" style="display:none;" class="cms-card mb-4"></div>

        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="cms-table">
                    <thead><tr><th>Title</th><th>Level</th><th>Lessons</th><th>Price</th><th>Status</th><th>Created</th><th class="text-right">Actions</th></tr></thead>
                    <tbody>
                        ${courses.length
                            ? courses.map(c=>`
                            <tr>
                                <td>
                                    <div class="text-white font-medium text-sm">${this._esc(c.title)}</div>
                                    <div class="text-gray-600 text-xs">${this._esc(c.description||'').slice(0,60)}${(c.description||'').length>60?'…':''}</div>
                                </td>
                                <td><span style="color:#a78bfa;font-size:.75rem;font-weight:600;">${c.level||'Beginner'}</span></td>
                                <td class="text-gray-300">${c.lesson_count||0}</td>
                                <td class="text-gray-300">${c.price>0?'$'+Number(c.price).toFixed(2):'Free'}</td>
                                <td>${this._badge(c.is_published)}</td>
                                <td class="text-gray-500">${this._date(c.created_at)}</td>
                                <td class="text-right">
                                    <div style="display:flex;gap:.35rem;justify-content:flex-end;">
                                        <button class="cms-btn cms-btn-gray" onclick="CMSPage._openLessonEditor(${c.id},'${this._esc(c.title)}')">
                                            <i class="fas fa-list"></i> Lessons
                                        </button>
                                        <button class="cms-btn cms-btn-gray" onclick="CMSPage._openCourseForm(${c.id})">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="cms-btn ${c.is_published?'cms-btn-gray':'cms-btn-green'}" onclick="CMSPage._toggleCourse(${c.id})">
                                            ${c.is_published?'Unpublish':'Publish'}
                                        </button>
                                        <button class="cms-btn cms-btn-red" onclick="CMSPage._deleteCourse(${c.id})">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>`).join('')
                            : '<tr><td colspan="7" class="text-center py-8 text-gray-500 text-sm"><i class="fas fa-graduation-cap text-2xl block mb-2 opacity-30"></i>No courses yet.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>`;
    },

    _openCourseForm(id=null){
        this._editingId = id;
        const formDiv = document.getElementById('cms-course-form');
        if(!formDiv) return;
        formDiv.style.display='block';
        formDiv.innerHTML=`
            <div class="cms-section-header">
                <h4 class="text-white font-semibold">${id?'Edit Course':'New Course'}</h4>
                <button class="cms-btn cms-btn-gray" onclick="CMSPage._closeCourseForm()"><i class="fas fa-times"></i> Cancel</button>
            </div>
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">Title *</label><input class="cms-input" id="cf-title" placeholder="Course title"></div>
                <div><label class="cms-label">Level</label>
                    <select class="cms-select" id="cf-level">
                        ${['Beginner','Intermediate','Advanced'].map(l=>`<option value="${l}">${l}</option>`).join('')}
                    </select></div>
            </div>
            <div class="cms-form-row">
                <div><label class="cms-label">Description</label><textarea class="cms-textarea" id="cf-desc" style="min-height:80px;"></textarea></div>
            </div>
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">Price (0 = Free)</label><input type="number" class="cms-input" id="cf-price" step="0.01" min="0" placeholder="0.00"></div>
                <div><label class="cms-label">Thumbnail URL</label><input class="cms-input" id="cf-thumb" placeholder="https://..."></div>
            </div>
            <div style="display:flex;align-items:center;gap:1.5rem;margin-top:.5rem;">
                <label class="cms-toggle" onclick="CMSPage._toggleCheck('cf-published')">
                    <div class="toggle-track"><div class="toggle-thumb"></div></div>
                    <span class="text-sm text-gray-300">Published</span>
                    <input type="hidden" id="cf-published" value="0">
                </label>
                <button class="cms-btn cms-btn-purple" onclick="CMSPage._saveCourse()">
                    <i class="fas fa-save"></i> ${id?'Update Course':'Create Course'}
                </button>
            </div>`;

        if(id){
            API.cms.listCourses().then(list=>{
                const c = list.find(x=>x.id===id);
                if(!c) return;
                document.getElementById('cf-title').value  = c.title||'';
                document.getElementById('cf-desc').value   = c.description||'';
                document.getElementById('cf-level').value  = c.level||'Beginner';
                document.getElementById('cf-price').value  = c.price||0;
                document.getElementById('cf-thumb').value  = c.thumbnail||'';
                const track = document.querySelector('#cms-course-form .toggle-track');
                const hid   = document.getElementById('cf-published');
                if(c.is_published){ track.classList.add('on'); hid.value='1'; }
            }).catch(()=>{});
        }
        formDiv.scrollIntoView({behavior:'smooth',block:'start'});
    },

    _closeCourseForm(){
        const f=document.getElementById('cms-course-form');
        if(f){f.style.display='none';f.innerHTML='';}
        this._editingId=null;
    },

    async _saveCourse(){
        const title=document.getElementById('cf-title')?.value.trim();
        if(!title){this._toast('Title is required','error');return;}
        const payload={
            title,
            description: document.getElementById('cf-desc')?.value||'',
            level:       document.getElementById('cf-level')?.value||'Beginner',
            price:       parseFloat(document.getElementById('cf-price')?.value)||0,
            thumbnail:   document.getElementById('cf-thumb')?.value||'',
            is_published:document.getElementById('cf-published')?.value==='1',
        };
        try{
            if(this._editingId){ await API.cms.updateCourse(this._editingId,payload); this._toast('Course updated'); }
            else               { await API.cms.createCourse(payload);                 this._toast('Course created'); }
            this._closeCourseForm();
            await this._renderCourses();
        }catch(e){this._toast(e.message,'error');}
    },

    async _toggleCourse(id){
        try{ const r=await API.cms.toggleCourse(id); this._toast(r.message); await this._renderCourses(); }
        catch(e){this._toast(e.message,'error');}
    },

    async _deleteCourse(id){
        if(!this._confirm('Delete this course and ALL its lessons?')) return;
        try{ await API.cms.deleteCourse(id); this._toast('Course deleted'); await this._renderCourses(); }
        catch(e){this._toast(e.message,'error');}
    },

    async _openLessonEditor(courseId, courseTitle){
        this._lessonCourseId = courseId;
        const div = document.getElementById('cms-lesson-editor');
        if(!div) return;
        div.style.display='block';
        div.innerHTML=`<div class="text-gray-400 text-sm"><i class="fas fa-spinner fa-spin mr-2"></i>Loading lessons…</div>`;
        div.scrollIntoView({behavior:'smooth',block:'start'});

        let lessons=[];
        try{ lessons=await API.cms.listLessons(courseId); }catch(_){}

        div.innerHTML=`
        <div class="cms-section-header">
            <h4 class="text-white font-semibold"><i class="fas fa-list text-purple-400 mr-2"></i>Lessons — ${this._esc(courseTitle)}</h4>
            <button class="cms-btn cms-btn-gray" onclick="document.getElementById('cms-lesson-editor').style.display='none';">
                <i class="fas fa-times"></i> Close
            </button>
        </div>

        <div id="cms-lesson-form" class="mb-4">
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">Lesson Title *</label><input class="cms-input" id="lf-title" placeholder="Lesson title"></div>
                <div><label class="cms-label">Video URL</label><input class="cms-input" id="lf-video" placeholder="https://youtube.com/..."></div>
            </div>
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">Duration (minutes)</label><input type="number" class="cms-input" id="lf-dur" min="0" placeholder="15"></div>
                <div><label class="cms-label">Order</label><input type="number" class="cms-input" id="lf-ord" min="0" placeholder="1"></div>
            </div>
            <div class="cms-form-row">
                <div><label class="cms-label">Content</label><textarea class="cms-textarea" id="lf-content" style="min-height:80px;" placeholder="Lesson content…"></textarea></div>
            </div>
            <div style="display:flex;gap:.75rem;">
                <button class="cms-btn cms-btn-purple" onclick="CMSPage._saveLesson()"><i class="fas fa-plus"></i> Add Lesson</button>
                <button class="cms-btn cms-btn-gray" onclick="CMSPage._clearLessonForm()">Clear</button>
            </div>
        </div>

        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <table class="cms-table">
                <thead><tr><th>#</th><th>Title</th><th>Duration</th><th>Video</th><th class="text-right">Actions</th></tr></thead>
                <tbody id="cms-lesson-tbody">
                    ${lessons.length
                        ? lessons.map((l,i)=>`<tr>
                            <td class="text-gray-600 font-mono">${String(l.order_index||i+1).padStart(2,'0')}</td>
                            <td class="text-white">${this._esc(l.title)}</td>
                            <td class="text-gray-400">${l.duration_minutes||0}m</td>
                            <td>${l.video_url?`<a href="${this._esc(l.video_url)}" target="_blank" class="text-purple-400 hover:underline text-xs">▶ Watch</a>`:'<span class="text-gray-600">—</span>'}</td>
                            <td class="text-right">
                                <div style="display:flex;gap:.35rem;justify-content:flex-end;">
                                    <button class="cms-btn cms-btn-gray" onclick="CMSPage._editLesson(${JSON.stringify(l).replace(/"/g,'&quot;')})"><i class="fas fa-edit"></i></button>
                                    <button class="cms-btn cms-btn-red" onclick="CMSPage._deleteLesson(${l.id})"><i class="fas fa-trash"></i></button>
                                </div>
                            </td>
                        </tr>`).join('')
                        : '<tr><td colspan="5" class="text-center py-6 text-gray-500 text-sm">No lessons yet. Add the first one above.</td></tr>'}
                </tbody>
            </table>
        </div>`;
    },

    _editLesson(lesson){
        document.getElementById('lf-title').value   = lesson.title||'';
        document.getElementById('lf-video').value   = lesson.video_url||'';
        document.getElementById('lf-dur').value     = lesson.duration_minutes||0;
        document.getElementById('lf-ord').value     = lesson.order_index||0;
        document.getElementById('lf-content').value = lesson.content||'';
        this._editingId = lesson.id;
        document.getElementById('lf-title').focus();
    },

    _clearLessonForm(){
        ['lf-title','lf-video','lf-dur','lf-ord','lf-content'].forEach(id=>{
            const el=document.getElementById(id);
            if(el) el.value='';
        });
        this._editingId=null;
    },

    async _saveLesson(){
        const title=document.getElementById('lf-title')?.value.trim();
        if(!title){this._toast('Lesson title required','error');return;}
        const payload={
            course_id:        this._lessonCourseId,
            title,
            content:          document.getElementById('lf-content')?.value||'',
            video_url:        document.getElementById('lf-video')?.value||'',
            duration_minutes: parseInt(document.getElementById('lf-dur')?.value)||0,
            order_index:      parseInt(document.getElementById('lf-ord')?.value)||0,
        };
        try{
            if(this._editingId){ await API.cms.updateLesson(this._editingId,payload); this._toast('Lesson updated'); }
            else               { await API.cms.createLesson(payload);                  this._toast('Lesson added'); }
            this._clearLessonForm();
            await this._openLessonEditor(this._lessonCourseId,'');
        }catch(e){this._toast(e.message,'error');}
    },

    async _deleteLesson(id){
        if(!this._confirm('Delete this lesson?')) return;
        try{ await API.cms.deleteLesson(id); this._toast('Lesson deleted'); await this._openLessonEditor(this._lessonCourseId,''); }
        catch(e){this._toast(e.message,'error');}
    },

    // ══════════════════════════════════════════════════════════════════════════
    // SIGNALS
    // ══════════════════════════════════════════════════════════════════════════
    async _renderSignals(){
        const pane=document.getElementById('cms-pane-signals');
        if(!pane) return;
        let signals=[];
        try{ signals=await API.cms.listSignals(); }catch(_){}

        pane.innerHTML=`
        <div class="cms-section-header">
            <h3 class="text-white font-semibold flex items-center gap-2">
                <i class="fas fa-satellite-dish text-purple-400"></i> Trading Signals
                <span style="background:#374151;color:#9ca3af;padding:.1rem .55rem;border-radius:9999px;font-size:.72rem;">${signals.length}</span>
            </h3>
            <button class="cms-btn cms-btn-purple" onclick="CMSPage._openSignalForm()">
                <i class="fas fa-plus"></i> New Signal
            </button>
        </div>

        <div id="cms-signal-form" style="display:none;" class="cms-card mb-4"></div>

        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="cms-table">
                    <thead><tr><th>Symbol</th><th>Dir</th><th>Entry</th><th>SL</th><th>TP</th><th>TF</th><th>Status</th><th>Created</th><th class="text-right">Actions</th></tr></thead>
                    <tbody>
                        ${signals.length
                            ? signals.map(s=>`<tr>
                                <td class="font-bold text-white">${this._esc(s.symbol)}</td>
                                <td>${this._dirBadge(s.direction)}</td>
                                <td class="font-mono text-gray-300">${s.entry_price}</td>
                                <td class="font-mono text-red-400">${s.stop_loss}</td>
                                <td class="font-mono text-green-400">${s.take_profit}</td>
                                <td class="text-gray-500">${s.timeframe||'—'}</td>
                                <td>${this._statusBadge(s.status)}</td>
                                <td class="text-gray-500">${this._date(s.created_at)}</td>
                                <td class="text-right">
                                    <div style="display:flex;gap:.35rem;justify-content:flex-end;">
                                        <button class="cms-btn cms-btn-gray" onclick="CMSPage._openSignalForm(${JSON.stringify(s).replace(/"/g,'&quot;')})"><i class="fas fa-edit"></i></button>
                                        ${s.status==='active'?`<button class="cms-btn cms-btn-gray" onclick="CMSPage._closeSignal(${s.id})">Close</button>`:''}
                                        <button class="cms-btn cms-btn-red" onclick="CMSPage._deleteSignal(${s.id})"><i class="fas fa-trash"></i></button>
                                    </div>
                                </td>
                            </tr>`).join('')
                            : '<tr><td colspan="9" class="text-center py-8 text-gray-500 text-sm"><i class="fas fa-satellite-dish text-2xl block mb-2 opacity-30"></i>No signals yet.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>`;
    },

    _openSignalForm(data=null){
        const isEdit = data && data.id;
        this._editingId = isEdit ? data.id : null;
        const d = data || { symbol:'',direction:'BUY',entry_price:'',stop_loss:'',take_profit:'',timeframe:'1H',analysis:'',ai_confidence:'',status:'active' };
        const formDiv=document.getElementById('cms-signal-form');
        if(!formDiv) return;
        formDiv.style.display='block';
        formDiv.innerHTML=`
            <div class="cms-section-header">
                <h4 class="text-white font-semibold">${isEdit?'Edit Signal':'New Signal'}</h4>
                <button class="cms-btn cms-btn-gray" onclick="CMSPage._closeSignalForm()"><i class="fas fa-times"></i> Cancel</button>
            </div>
            <div class="cms-form-row cols-3">
                <div><label class="cms-label">Symbol *</label><input class="cms-input" id="sf-symbol" value="${this._esc(d.symbol)}" placeholder="EURUSD"></div>
                <div><label class="cms-label">Direction *</label>
                    <select class="cms-select" id="sf-dir">
                        <option value="BUY" ${d.direction==='BUY'?'selected':''}>BUY</option>
                        <option value="SELL" ${d.direction==='SELL'?'selected':''}>SELL</option>
                    </select></div>
                <div><label class="cms-label">Timeframe</label>
                    <select class="cms-select" id="sf-tf">
                        ${['1M','5M','15M','1H','4H','1D','1W'].map(t=>`<option value="${t}" ${d.timeframe===t?'selected':''}>${t}</option>`).join('')}
                    </select></div>
            </div>
            <div class="cms-form-row cols-3">
                <div><label class="cms-label">Entry Price *</label><input type="number" step="0.00001" class="cms-input" id="sf-entry" value="${d.entry_price}"></div>
                <div><label class="cms-label">Stop Loss *</label><input type="number" step="0.00001" class="cms-input" id="sf-sl" value="${d.stop_loss}"></div>
                <div><label class="cms-label">Take Profit *</label><input type="number" step="0.00001" class="cms-input" id="sf-tp" value="${d.take_profit}"></div>
            </div>
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">AI Confidence (0-1)</label><input type="number" step="0.01" min="0" max="1" class="cms-input" id="sf-conf" value="${d.ai_confidence||''}"></div>
                <div><label class="cms-label">Status</label>
                    <select class="cms-select" id="sf-status">
                        ${['active','closed','cancelled'].map(s=>`<option value="${s}" ${d.status===s?'selected':''}>${s}</option>`).join('')}
                    </select></div>
            </div>
            <div class="cms-form-row">
                <div><label class="cms-label">Analysis Notes</label><textarea class="cms-textarea" id="sf-analysis" style="min-height:80px;">${this._esc(d.analysis||'')}</textarea></div>
            </div>
            <button class="cms-btn cms-btn-purple" onclick="CMSPage._saveSignal()"><i class="fas fa-save"></i> ${isEdit?'Update':'Create'} Signal</button>`;
        formDiv.scrollIntoView({behavior:'smooth',block:'start'});
    },

    _closeSignalForm(){
        const f=document.getElementById('cms-signal-form');
        if(f){f.style.display='none';f.innerHTML='';}
        this._editingId=null;
    },

    async _saveSignal(){
        const symbol=document.getElementById('sf-symbol')?.value.trim().toUpperCase();
        const entry =parseFloat(document.getElementById('sf-entry')?.value);
        const sl    =parseFloat(document.getElementById('sf-sl')?.value);
        const tp    =parseFloat(document.getElementById('sf-tp')?.value);
        if(!symbol||isNaN(entry)||isNaN(sl)||isNaN(tp)){this._toast('Symbol, entry, SL and TP are required','error');return;}
        const confRaw=document.getElementById('sf-conf')?.value;
        const payload={
            symbol, direction:document.getElementById('sf-dir')?.value||'BUY',
            entry_price:entry, stop_loss:sl, take_profit:tp,
            timeframe:document.getElementById('sf-tf')?.value||'1H',
            analysis:document.getElementById('sf-analysis')?.value||'',
            ai_confidence:confRaw?parseFloat(confRaw):null,
            status:document.getElementById('sf-status')?.value||'active',
        };
        try{
            if(this._editingId){ await API.cms.updateSignal(this._editingId,payload); this._toast('Signal updated'); }
            else               { await API.cms.createSignal(payload);                  this._toast('Signal created'); }
            this._closeSignalForm();
            await this._renderSignals();
        }catch(e){this._toast(e.message,'error');}
    },

    async _closeSignal(id){
        const outcome=prompt('Outcome (win / loss / breakeven):','win');
        if(outcome===null) return;
        try{ await API.cms.closeSignal(id,outcome); this._toast('Signal closed'); await this._renderSignals(); }
        catch(e){this._toast(e.message,'error');}
    },

    async _deleteSignal(id){
        if(!this._confirm('Delete this signal?')) return;
        try{ await API.cms.deleteSignal(id); this._toast('Signal deleted'); await this._renderSignals(); }
        catch(e){this._toast(e.message,'error');}
    },

    // ══════════════════════════════════════════════════════════════════════════
    // WEBINARS
    // ══════════════════════════════════════════════════════════════════════════
    async _renderWebinars(){
        const pane=document.getElementById('cms-pane-webinars');
        if(!pane) return;
        let webinars=[];
        try{ webinars=await API.cms.listWebinars(); }catch(_){}

        pane.innerHTML=`
        <div class="cms-section-header">
            <h3 class="text-white font-semibold flex items-center gap-2">
                <i class="fas fa-video text-pink-400"></i> Webinars
                <span style="background:#374151;color:#9ca3af;padding:.1rem .55rem;border-radius:9999px;font-size:.72rem;">${webinars.length}</span>
            </h3>
            <button class="cms-btn cms-btn-purple" onclick="CMSPage._openWebinarForm()">
                <i class="fas fa-plus"></i> New Webinar
            </button>
        </div>

        <div id="cms-webinar-form" style="display:none;" class="cms-card mb-4"></div>

        <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="cms-table">
                    <thead><tr><th>Title</th><th>Presenter</th><th>Date</th><th>Duration</th><th>Status</th><th>Attendees</th><th class="text-right">Actions</th></tr></thead>
                    <tbody>
                        ${webinars.length
                            ? webinars.map(w=>`<tr>
                                <td>
                                    <div class="text-white font-medium text-sm">${this._esc(w.title)}</div>
                                    ${w.meeting_link?`<a href="${this._esc(w.meeting_link)}" target="_blank" class="text-purple-400 text-xs hover:underline">🔗 Join link</a>`:''}
                                </td>
                                <td class="text-gray-400">${this._esc(w.presenter||'—')}</td>
                                <td class="text-gray-300">${this._date(w.scheduled_at)}</td>
                                <td class="text-gray-400">${w.duration_minutes||60}m</td>
                                <td>${this._badge(w.is_published)}</td>
                                <td class="text-gray-400">${w.max_attendees||100}</td>
                                <td class="text-right">
                                    <div style="display:flex;gap:.35rem;justify-content:flex-end;">
                                        <button class="cms-btn cms-btn-gray" onclick="CMSPage._openWebinarForm(${JSON.stringify(w).replace(/"/g,'&quot;')})"><i class="fas fa-edit"></i></button>
                                        <button class="cms-btn ${w.is_published?'cms-btn-gray':'cms-btn-green'}" onclick="CMSPage._toggleWebinar(${w.id})">${w.is_published?'Unpublish':'Publish'}</button>
                                        <button class="cms-btn cms-btn-red" onclick="CMSPage._deleteWebinar(${w.id})"><i class="fas fa-trash"></i></button>
                                    </div>
                                </td>
                            </tr>`).join('')
                            : '<tr><td colspan="7" class="text-center py-8 text-gray-500 text-sm"><i class="fas fa-video text-2xl block mb-2 opacity-30"></i>No webinars yet.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>`;
    },

    _openWebinarForm(data=null){
        const isEdit=data&&data.id;
        this._editingId=isEdit?data.id:null;
        const d=data||{title:'',description:'',presenter:'',scheduled_at:'',duration_minutes:60,meeting_link:'',max_attendees:100,is_published:false};
        const formDiv=document.getElementById('cms-webinar-form');
        if(!formDiv) return;
        formDiv.style.display='block';
        formDiv.innerHTML=`
            <div class="cms-section-header">
                <h4 class="text-white font-semibold">${isEdit?'Edit Webinar':'New Webinar'}</h4>
                <button class="cms-btn cms-btn-gray" onclick="CMSPage._closeWebinarForm()"><i class="fas fa-times"></i> Cancel</button>
            </div>
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">Title *</label><input class="cms-input" id="wf-title" value="${this._esc(d.title)}" placeholder="Webinar title"></div>
                <div><label class="cms-label">Presenter</label><input class="cms-input" id="wf-presenter" value="${this._esc(d.presenter||'')}" placeholder="Presenter name"></div>
            </div>
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">Date &amp; Time *</label><input type="datetime-local" class="cms-input" id="wf-date" value="${this._dt(d.scheduled_at)}"></div>
                <div><label class="cms-label">Duration (minutes)</label><input type="number" class="cms-input" id="wf-dur" value="${d.duration_minutes||60}" min="1"></div>
            </div>
            <div class="cms-form-row cols-2">
                <div><label class="cms-label">Meeting Link</label><input class="cms-input" id="wf-link" value="${this._esc(d.meeting_link||'')}" placeholder="https://zoom.us/..."></div>
                <div><label class="cms-label">Max Attendees</label><input type="number" class="cms-input" id="wf-max" value="${d.max_attendees||100}" min="1"></div>
            </div>
            <div class="cms-form-row">
                <div><label class="cms-label">Description</label><textarea class="cms-textarea" id="wf-desc" style="min-height:80px;">${this._esc(d.description||'')}</textarea></div>
            </div>
            <div style="display:flex;align-items:center;gap:1.5rem;margin-top:.5rem;">
                <label class="cms-toggle" onclick="CMSPage._toggleCheck('wf-published')">
                    <div class="toggle-track${d.is_published?' on':''}"><div class="toggle-thumb"></div></div>
                    <span class="text-sm text-gray-300">Published</span>
                    <input type="hidden" id="wf-published" value="${d.is_published?'1':'0'}">
                </label>
                <button class="cms-btn cms-btn-purple" onclick="CMSPage._saveWebinar()"><i class="fas fa-save"></i> ${isEdit?'Update':'Create'} Webinar</button>
            </div>`;
        formDiv.scrollIntoView({behavior:'smooth',block:'start'});
    },

    _closeWebinarForm(){
        const f=document.getElementById('cms-webinar-form');
        if(f){f.style.display='none';f.innerHTML='';}
        this._editingId=null;
    },

    async _saveWebinar(){
        const title=document.getElementById('wf-title')?.value.trim();
        const sched=document.getElementById('wf-date')?.value;
        if(!title||!sched){this._toast('Title and date are required','error');return;}
        const payload={
            title, description:document.getElementById('wf-desc')?.value||'',
            presenter:document.getElementById('wf-presenter')?.value||'',
            scheduled_at:sched,
            duration_minutes:parseInt(document.getElementById('wf-dur')?.value)||60,
            meeting_link:document.getElementById('wf-link')?.value||'',
            max_attendees:parseInt(document.getElementById('wf-max')?.value)||100,
            is_published:document.getElementById('wf-published')?.value==='1',
        };
        try{
            if(this._editingId){ await API.cms.updateWebinar(this._editingId,payload); this._toast('Webinar updated'); }
            else               { await API.cms.createWebinar(payload);                  this._toast('Webinar created'); }
            this._closeWebinarForm();
            await this._renderWebinars();
        }catch(e){this._toast(e.message,'error');}
    },

    async _toggleWebinar(id){
        try{ const r=await API.cms.toggleWebinar(id); this._toast(r.message); await this._renderWebinars(); }
        catch(e){this._toast(e.message,'error');}
    },

    async _deleteWebinar(id){
        if(!this._confirm('Delete this webinar?')) return;
        try{ await API.cms.deleteWebinar(id); this._toast('Webinar deleted'); await this._renderWebinars(); }
        catch(e){this._toast(e.message,'error');}
    },

    // ══════════════════════════════════════════════════════════════════════════
    // SITE SETTINGS
    // ══════════════════════════════════════════════════════════════════════════
    async _renderSettings(){
        const pane=document.getElementById('cms-pane-settings');
        if(!pane) return;
        pane.innerHTML=`<div class="text-gray-400 text-sm text-center py-8"><i class="fas fa-spinner fa-spin mr-2"></i>Loading settings…</div>`;

        let settings={};
        try{ settings=await API.cms.getSettings(); }catch(_){}

        const g=(k,fallback='')=>this._esc(settings[k]!=null?settings[k]:fallback);

        pane.innerHTML=`
        <div class="cms-section-header">
            <h3 class="text-white font-semibold flex items-center gap-2"><i class="fas fa-cog text-yellow-400"></i> Site Settings</h3>
            <button class="cms-btn cms-btn-purple" onclick="CMSPage._saveSettings()"><i class="fas fa-save"></i> Save All Changes</button>
        </div>

        <!-- General -->
        <div class="settings-group">
            <div class="settings-group-header"><i class="fas fa-globe mr-2"></i>General</div>
            <div class="settings-row"><div><div class="settings-label">Site Name</div></div><input class="cms-input" style="max-width:280px;" id="s-site_name" value="${g('site_name','Pipways')}"></div>
            <div class="settings-row"><div><div class="settings-label">Tagline</div></div><input class="cms-input" style="max-width:280px;" id="s-site_tagline" value="${g('site_tagline','Professional Trading Platform')}"></div>
            <div class="settings-row"><div><div class="settings-label">Footer Text</div></div><input class="cms-input" style="max-width:360px;" id="s-footer_text" value="${g('footer_text','© 2025 Pipways. All rights reserved.')}"></div>
            <div class="settings-row"><div><div class="settings-label">Currency</div></div>
                <select class="cms-select" style="max-width:120px;" id="s-currency">
                    ${['USD','EUR','GBP','NGN','ZAR','AED'].map(c=>`<option value="${c}" ${settings.currency===c?'selected':''}>${c}</option>`).join('')}
                </select></div>
            <div class="settings-row"><div><div class="settings-label">Timezone</div></div>
                <select class="cms-select" style="max-width:200px;" id="s-timezone">
                    ${['UTC','America/New_York','America/Los_Angeles','Europe/London','Europe/Berlin','Asia/Dubai','Africa/Lagos'].map(t=>`<option value="${t}" ${settings.timezone===t?'selected':''}>${t}</option>`).join('')}
                </select></div>
        </div>

        <!-- Contact & Email -->
        <div class="settings-group">
            <div class="settings-group-header"><i class="fas fa-envelope mr-2"></i>Contact &amp; Email</div>
            <div class="settings-row"><div><div class="settings-label">Contact Email</div></div><input class="cms-input" style="max-width:280px;" id="s-contact_email" value="${g('contact_email')}"></div>
            <div class="settings-row"><div><div class="settings-label">Support Email</div></div><input class="cms-input" style="max-width:280px;" id="s-support_email" value="${g('support_email')}"></div>
            <div class="settings-row"><div><div class="settings-label">SMTP Host</div></div><input class="cms-input" style="max-width:280px;" id="s-smtp_host" value="${g('smtp_host')}"></div>
            <div class="settings-row"><div><div class="settings-label">SMTP Port</div></div><input type="number" class="cms-input" style="max-width:100px;" id="s-smtp_port" value="${g('smtp_port','587')}"></div>
            <div class="settings-row"><div><div class="settings-label">SMTP Username</div></div><input class="cms-input" style="max-width:280px;" id="s-smtp_user" value="${g('smtp_user')}"></div>
        </div>

        <!-- Branding -->
        <div class="settings-group">
            <div class="settings-group-header"><i class="fas fa-palette mr-2"></i>Branding</div>
            <div class="settings-row"><div><div class="settings-label">Logo URL</div><div class="settings-desc">Full URL to your logo image</div></div><input class="cms-input" style="max-width:360px;" id="s-logo_url" value="${g('logo_url')}"></div>
            <div class="settings-row"><div><div class="settings-label">Favicon URL</div></div><input class="cms-input" style="max-width:360px;" id="s-favicon_url" value="${g('favicon_url')}"></div>
            <div class="settings-row"><div><div class="settings-label">Analytics ID</div><div class="settings-desc">Google Analytics GA4 measurement ID</div></div><input class="cms-input" style="max-width:200px;" id="s-analytics_id" value="${g('analytics_id')}" placeholder="G-XXXXXXXXXX"></div>
        </div>

        <!-- Social Media -->
        <div class="settings-group">
            <div class="settings-group-header"><i class="fas fa-share-alt mr-2"></i>Social Media</div>
            ${[['twitter_url','fab fa-twitter','Twitter/X URL'],['instagram_url','fab fa-instagram','Instagram URL'],['telegram_url','fab fa-telegram','Telegram URL'],['youtube_url','fab fa-youtube','YouTube URL'],['discord_url','fab fa-discord','Discord URL']].map(([key,icon,label])=>`
            <div class="settings-row">
                <div><div class="settings-label"><i class="${icon} mr-1.5"></i>${label}</div></div>
                <input class="cms-input" style="max-width:320px;" id="s-${key}" value="${g(key)}" placeholder="https://...">
            </div>`).join('')}
        </div>

        <!-- Platform Controls -->
        <div class="settings-group">
            <div class="settings-group-header"><i class="fas fa-sliders-h mr-2"></i>Platform Controls</div>
            <div class="settings-row">
                <div><div class="settings-label">Maintenance Mode</div><div class="settings-desc">Redirects all visitors to a maintenance page</div></div>
                <label class="cms-toggle" onclick="CMSPage._toggleCheck('s-maintenance_mode','true','false')">
                    <div class="toggle-track${settings.maintenance_mode==='true'?' on':''}"><div class="toggle-thumb"></div></div>
                    <input type="hidden" id="s-maintenance_mode" value="${g('maintenance_mode','false')}">
                </label>
            </div>
            <div class="settings-row">
                <div><div class="settings-label">Allow Registration</div><div class="settings-desc">New users can sign up</div></div>
                <label class="cms-toggle" onclick="CMSPage._toggleCheck('s-allow_registration','true','false')">
                    <div class="toggle-track${settings.allow_registration!=='false'?' on':''}"><div class="toggle-thumb"></div></div>
                    <input type="hidden" id="s-allow_registration" value="${g('allow_registration','true')}">
                </label>
            </div>
            <div class="settings-row">
                <div><div class="settings-label">Free Signals Limit</div><div class="settings-desc">Max signals visible to free-tier users</div></div>
                <input type="number" class="cms-input" style="max-width:80px;" id="s-free_signals_limit" value="${g('free_signals_limit','3')}" min="0">
            </div>
        </div>

        <div style="display:flex;justify-content:flex-end;margin-top:1rem;">
            <button class="cms-btn cms-btn-purple" style="padding:.6rem 1.5rem;font-size:.9rem;" onclick="CMSPage._saveSettings()">
                <i class="fas fa-save mr-2"></i> Save All Changes
            </button>
        </div>`;
    },

    async _saveSettings(){
        // Collect all setting inputs
        const updates={};
        document.querySelectorAll('[id^="s-"]').forEach(el=>{
            const key=el.id.slice(2);
            updates[key]=el.value;
        });
        try{
            await API.cms.saveSettings(updates);
            this._toast('Settings saved successfully');
        }catch(e){ this._toast(e.message,'error'); }
    },

    // Reusable toggle helper
    _toggleCheck(id, onVal='1', offVal='0'){
        const input=document.getElementById(id);
        if(!input) return;
        const track=input.previousElementSibling;
        const isOn=input.value===onVal;
        input.value=isOn?offVal:onVal;
        if(track && track.classList.contains('toggle-track')){
            track.classList.toggle('on',!isOn);
        }
    },
};
