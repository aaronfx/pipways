// CMS Module: SETTINGS
// Extracted from cms.js for maintainability

Object.assign(CMSPage, {
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
},async _settings(){
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
},_togCheck(id, onVal='1', offVal='0'){
    const el=document.getElementById(id); if(!el) return;
    const isOn=el.value===onVal;
    el.value=isOn?offVal:onVal;
    const track=el.closest('label')?.querySelector('.ttrack')||el.closest('[class*="ctog"]')?.querySelector('.ttrack');
    if(track) track.classList.toggle('on',!isOn);
},
});
