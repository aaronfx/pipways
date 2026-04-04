// CMS Module: SIGNALS
// Extracted from cms.js for maintainability

Object.assign(CMSPage, {
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
},_closeSigForm(){ const f=document.getElementById('cms-sig-form'); if(f){f.style.display='none';f.innerHTML='';} this._editingId=null; },async _saveSig(){
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
},async _closeSignal(id){ const o=prompt('Outcome (win/loss/breakeven):','win'); if(!o)return; try{await API.cms.closeSignal(id,o);this._toast('Signal closed');await this._signals();}catch(e){this._toast(e.message,'error');} },async _deleteSignal(id){ if(!confirm('Delete signal?'))return; try{await API.cms.deleteSignal(id);this._toast('Deleted');await this._signals();}catch(e){this._toast(e.message,'error');} },
});
