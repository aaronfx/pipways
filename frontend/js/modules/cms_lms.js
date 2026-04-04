// CMS Module: LMS
// Extracted from cms.js for maintainability

Object.assign(CMSPage, {
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
async _lmsTogglePub(id){ try{const r=await API.cms.toggleCourse(id);this._toast(r.message);await this._lmsRefreshTree();}catch(e){this._toast(e.message,'error');} },async _lmsDeleteCourse(id){ if(!confirm('Delete course and ALL its modules, lessons and quizzes?'))return; try{await API.cms.deleteCourse(id);this._toast('Course deleted');this._lmsCloseOverlay();await this._lmsRefreshTree();}catch(e){this._toast(e.message,'error');} },
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
async _lmsCreateQuiz(mid){ const t=document.getElementById('qz-title')?.value.trim(); if(!t){this._toast('Quiz title required','error');return;} try{await API.cms.createQuiz({module_id:mid,title:t,pass_percentage:parseInt(document.getElementById('qz-pass')?.value)||70,max_attempts:parseInt(document.getElementById('qz-attempts')?.value)||3});this._toast('Quiz created');await this._lmsShowQuizPanel(mid);}catch(e){this._toast(e.message,'error');} },async _lmsUpdateQuiz(qid,mid){ const t=document.getElementById('qz-title')?.value.trim(); try{await API.cms.updateQuiz(qid,{module_id:mid,title:t,pass_percentage:parseInt(document.getElementById('qz-pass')?.value)||70,max_attempts:parseInt(document.getElementById('qz-attempts')?.value)||3});this._toast('Quiz settings saved');}catch(e){this._toast(e.message,'error');} },async _lmsDeleteQuiz(qid,mid){ if(!confirm('Delete quiz and all questions?'))return; try{await API.cms.deleteQuiz(qid);this._toast('Quiz deleted');await this._lmsShowQuizPanel(mid);}catch(e){this._toast(e.message,'error');} },
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
});
