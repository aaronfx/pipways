// CMS Module: USERS
// Extracted from cms.js for maintainability

Object.assign(CMSPage, {
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
async _setRole(id,role){ try{await API.cms.setUserRole(id,role);this._toast(`Role set to ${role}`);}catch(e){this._toast(e.message,'error');} },async _setSub(id,tier){ try{await API.cms.setUserSub(id,tier);this._toast(`Subscription set to ${tier}`);}catch(e){this._toast(e.message,'error');} },async _toggleUserStatus(id){ try{const r=await API.cms.toggleUser(id);this._toast(r.message);await this._loadUsersTable(this._usersPage,this._usersSearch);}catch(e){this._toast(e.message,'error');} },
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
},async _toggleAnn(id){ try{await API.cms.toggleAnnouncement(id);await this._loadAnnouncements();}catch(e){this._toast(e.message,'error');} },async _deleteAnn(id){ if(!confirm('Delete?'))return; try{await API.cms.deleteAnnouncement(id);await this._loadAnnouncements();}catch(e){this._toast(e.message,'error');} },
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
},async _toggleCoupon(id){ try{await API.cms.toggleCoupon(id);await this._loadCoupons();}catch(e){this._toast(e.message,'error');} },async _deleteCoupon(id){ if(!confirm('Delete coupon?'))return; try{await API.cms.deleteCoupon(id);await this._loadCoupons();}catch(e){this._toast(e.message,'error');} },
});
