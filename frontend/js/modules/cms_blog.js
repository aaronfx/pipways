// CMS Module: BLOG
// Extracted from cms.js for maintainability

Object.assign(CMSPage, {
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
},_restoreDraft(btn){
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
},async _deletePost(id){ if(!confirm('Delete this post permanently?'))return; try{await API.cms.deletePost(id);this._toast('Post deleted');await this._blog();}catch(e){this._toast(e.message,'error');} },
async _togglePost(id){ try{const r=await API.cms.togglePost(id);this._toast(r.message);await this._blog();}catch(e){this._toast(e.message,'error');} },
});
