// CMS Module: MEDIA
// Extracted from cms.js for maintainability

Object.assign(CMSPage, {
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
},_cancelMediaPick(){ document.getElementById('media-picker-overlay')?.remove(); this._mediaCallback=null; },
});
