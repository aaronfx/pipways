/**
 * Pipways Trading Academy Frontend Module v4.1 (Production Stable)
 * Fixes:
 * - Invalid token crash
 * - Safe API initialization
 * - TradingView stability
 * - SVG diagram rendering
 * - Markdown fallback stability
 * - Quiz system stability (5 questions)
 */

(function waitForAPI() {
    if (!window.API) {
        console.warn("API not ready. Retrying academy init...");
        setTimeout(waitForAPI, 100);
        return;
    }
    initAcademy();
})();

function initAcademy() {

const A = window.API;
if (A._academyReady) return;
A._academyReady = true;

/* ─────────────────────────────────────────────
   LMS API
───────────────────────────────────────────── */

A.lms = {
    getLevels: () => A.request('/learning/levels'),
    getModules: (lid) => A.request(`/learning/modules/${lid}`),
    getLessons: (mid) => A.request(`/learning/lessons/${mid}`),
    getLesson: (lid) => A.request(`/learning/lesson/${lid}`),
    getQuiz: (lid) => A.request(`/learning/quiz/${lid}`),
    getProgress: (uid) => A.request(`/learning/progress/${uid}`),
    getBadges: (uid) => A.request(`/learning/badges/${uid}`),
    checkBadges: () => A.request('/learning/badges/check',{method:'POST'}),
    submitQuiz:(lid,answers)=>A.request('/learning/quiz/submit',{
        method:'POST',
        body:JSON.stringify({lesson_id:lid,answers})
    }),
    completeLesson:(lid,score)=>A.request('/learning/lesson/complete',{
        method:'POST',
        body:JSON.stringify({lesson_id:lid,quiz_score:score||0})
    })
};

/* ─────────────────────────────────────────────
   MARKED.JS LOADER
───────────────────────────────────────────── */

(function loadMarked(){
    if(window.marked) return;
    const s=document.createElement('script');
    s.src="https://cdn.jsdelivr.net/npm/marked/marked.min.js";
    s.async=true;
    document.head.appendChild(s);
})();

/* ─────────────────────────────────────────────
   MAIN CONTROLLER
───────────────────────────────────────────── */

const AcademyPage = {

_level:null,
_module:null,
_lesson:null,
_quiz:null,
_uid:null,

async render(){

    const wrap=document.getElementById('academy-container');
    if(!wrap) return;

    this._uid=this._getUser()?.id||null;

    wrap.innerHTML=`
        <div id="ac-breadcrumb" class="pw-breadcrumb mb-4" style="display:none"></div>
        <div id="ac-main"></div>
    `;

    await this._showLevelSelector();
},

/* ─────────────────────────────────────────────
   LEVEL SELECTOR
───────────────────────────────────────────── */

async _showLevelSelector(){

const main=document.getElementById('ac-main');
main.innerHTML=this._loading("Loading curriculum...");

try{

const levels=await API.lms.getLevels();

if(!levels||!levels.length){
main.innerHTML=this._empty("Academy not initialized");
return;
}

main.innerHTML=`
<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
${levels.map(l=>`

<div class="pw-card cursor-pointer"
onclick="AcademyPage._selectLevel(${l.id},'${_es(l.name)}')">

<div class="pw-card-body">

<h3 class="text-white font-bold">${_es(l.name)}</h3>

<p class="text-gray-500 text-sm">
${_es(l.description||"")}
</p>

</div>
</div>

`).join('')}
</div>
`;

}catch(e){

main.innerHTML=this._error("Failed loading levels",e.message);

}

},

/* ─────────────────────────────────────────────
   MODULES
───────────────────────────────────────────── */

async _selectLevel(id,name){

this._level={id,name};

const main=document.getElementById('ac-main');
main.innerHTML=this._loading("Loading modules...");

try{

const modules=await API.lms.getModules(id);

main.innerHTML=`
<div class="grid md:grid-cols-2 gap-4">

${modules.map(m=>`

<div class="pw-card cursor-pointer"
onclick="AcademyPage._selectModule(${m.id},'${_es(m.title)}')">

<div class="pw-card-body">

<h3 class="text-white">${_es(m.title)}</h3>

<p class="text-gray-500 text-sm">
${_es(m.description||"")}
</p>

</div>

</div>

`).join('')}

</div>
`;

}catch(e){

main.innerHTML=this._error("Failed loading modules",e.message);

}

},

/* ─────────────────────────────────────────────
   LESSONS
───────────────────────────────────────────── */

async _selectModule(id,title){

this._module={id,title};

const main=document.getElementById('ac-main');
main.innerHTML=this._loading("Loading lessons...");

try{

const lessons=await API.lms.getLessons(id);

main.innerHTML=`

<div class="space-y-2">

${lessons.map((l,i)=>`

<div class="pw-card cursor-pointer"

onclick="AcademyPage._openLesson(${l.id},'${_es(l.title)}')">

<div class="pw-card-body">

<span class="text-white">

Lesson ${i+1}: ${_es(l.title)}

</span>

</div>

</div>

`).join('')}

</div>

`;

}catch(e){

main.innerHTML=this._error("Failed loading lessons",e.message);

}

},

/* ─────────────────────────────────────────────
   LESSON VIEW
───────────────────────────────────────────── */

async _openLesson(id,title){

this._lesson={id,title};

const main=document.getElementById('ac-main');
main.innerHTML=this._loading("Loading lesson...");

try{

const lesson=await API.lms.getLesson(id);

const content=this._processLessonContent(lesson.content);

main.innerHTML=`

<div class="max-w-3xl">

<div class="pw-card">

<div class="pw-card-hdr">

<h2 class="text-white">${_es(lesson.title)}</h2>

</div>

<div class="pw-card-body">

<div class="ac-lesson-text">

${content}

</div>

</div>

</div>

<button class="btn btn-primary mt-4"

onclick="AcademyPage._startQuiz(${id})">

Take Quiz

</button>

</div>

`;

setTimeout(()=>this.initTradingViewWidgets(),100);

}catch(e){

main.innerHTML=this._error("Lesson failed",e.message);

}

},

/* ─────────────────────────────────────────────
   MARKDOWN PARSER
───────────────────────────────────────────── */

_processLessonContent(content){

if(!content) return "";

if(window.marked){

return marked.parse(content);

}

return content
.replace(/\n/g,"<br>")
.replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>");

},

/* ─────────────────────────────────────────────
   TRADINGVIEW
───────────────────────────────────────────── */

initTradingViewWidgets(){

const widgets=document.querySelectorAll(".ac-tradingview-widget");

widgets.forEach(el=>{

const symbol=el.dataset.symbol||"FX:EURUSD";

if(!window.TradingView){

const s=document.createElement("script");
s.src="https://s3.tradingview.com/tv.js";

s.onload=()=>this.initTradingViewWidgets();

document.head.appendChild(s);

return;

}

new TradingView.widget({

container_id:el.id,
symbol,
interval:"60",
theme:"dark",
style:"1",
locale:"en",
autosize:true

});

});

},

/* ─────────────────────────────────────────────
   QUIZ SYSTEM
───────────────────────────────────────────── */

async _startQuiz(id){

const main=document.getElementById("ac-main");
main.innerHTML=this._loading("Loading quiz...");

try{

const data=await API.lms.getQuiz(id);

this._quiz={
lessonId:id,
questions:data.questions.slice(0,5),
index:0,
answers:[]
};

this._renderQuestion();

}catch(e){

main.innerHTML=this._error("Quiz failed",e.message);

}

},

_renderQuestion(){

const q=this._quiz.questions[this._quiz.index];

const main=document.getElementById("ac-main");

main.innerHTML=`

<div class="pw-card">

<div class="pw-card-body">

<h3 class="text-white mb-4">${_es(q.question)}</h3>

${["a","b","c","d"].map(o=>`

<button class="quiz-btn"

onclick="AcademyPage._pick('${o}')">

${_es(q["option_"+o]||"")}

</button>

`).join("")}

</div>

</div>

`;

},

_pick(opt){

const q=this._quiz.questions[this._quiz.index];

this._quiz.answers.push({

question_id:q.id,
selected_answer:opt

});

this._quiz.index++;

if(this._quiz.index<this._quiz.questions.length){

this._renderQuestion();

}else{

this._submitQuiz();

}

},

async _submitQuiz(){

const main=document.getElementById("ac-main");
main.innerHTML=this._loading("Grading quiz...");

try{

const res=await API.lms.submitQuiz(
this._quiz.lessonId,
this._quiz.answers
);

main.innerHTML=`

<div class="pw-card">

<div class="pw-card-body text-center">

<h2 class="text-white">${res.score}%</h2>

<p class="text-gray-400">

${res.correct} / ${res.total}

</p>

<button class="btn btn-primary mt-4"

onclick="AcademyPage._showLevelSelector()">

Back to Academy

</button>

</div>

</div>

`;

}catch(e){

main.innerHTML=this._error("Quiz submit failed",e.message);

}

},

/* ─────────────────────────────────────────────
   HELPERS
───────────────────────────────────────────── */

_getUser(){

try{

return JSON.parse(localStorage.getItem("pipways_user")||"{}");

}catch{

return {};

}

},

_loading:m=>`

<div class="loading">

<div class="spinner"></div>

<p class="text-gray-500 text-sm">${m}</p>

</div>

`,

_error:(t,d)=>`

<div class="alert alert-error">

<strong>${_es(t)}</strong> ${_es(d||"")}

</div>

`,

_empty:t=>`

<div class="pw-empty">

${_es(t)}

</div>

`

};

window.AcademyPage=AcademyPage;

}

/* ─────────────────────────────────────────────
   ESCAPE HELPER
───────────────────────────────────────────── */

function _es(str){

if(str==null) return "";

return String(str)
.replace(/&/g,"&amp;")
.replace(/</g,"&lt;")
.replace(/>/g,"&gt;")
.replace(/"/g,"&quot;")
.replace(/'/g,"&#39;");

}
