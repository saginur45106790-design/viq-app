// Component-render smoke tests: no browser, network, or production credentials.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const noop=()=>{}, el={addEventListener:noop,classList:{add:noop,remove:noop,toggle:noop},setAttribute:noop,querySelector:()=>el,innerHTML:'',textContent:''};
const ctx=vm.createContext({console,URLSearchParams,Date,setTimeout:noop,clearTimeout:noop,document:{querySelector:()=>el,querySelectorAll:()=>[],addEventListener:noop},window:{addEventListener:noop},localStorage:{getItem:()=>null,setItem:noop},location:{search:'',hash:'#home'},navigator:{onLine:true},fetch:async()=>({ok:true,json:async()=>({})})});
for(const file of ['v2-ui.js','v3-ui.js','app.js']){let code=fs.readFileSync('static/'+file,'utf8');if(file==='app.js')code=code.slice(0,code.indexOf('(async()=>{try{config='));vm.runInContext(code,ctx)}
vm.runInContext(`
user={id:2,name:'Worker',role:'admin'};
config={categories:['social','create-video','survey','daily','voice','live','team','agency'].map(slug=>({slug,name:slug,enabled:true})),settings:{survey_daily_limit:'5',video_claim_hours:'24',agency_fee:'1000',signup_member:'10',signup_referrer:'5',agency_signup_member:'30',agency_signup_referrer:'50',agency_commission_percent:'5',live_rate:'1',live_daily_minutes:'60',live_enabled:'true'}};
api=async path=>path.startsWith('/tasks?')?{tasks:[{id:1,title:'<img src=x onerror=alert(1)>',category:path.split('=')[1],description:'Read this script',proof_type:path.includes('voice')?'audio':'text',reward:100,active:true,submission:{id:1,status:'started'}}]}:path==='/modules/progress'?{survey_used:2,survey_limit:5,reset_at:2000000000}:path==='/team'?{code:'AAAC',commission:500,agency_approved:false,members:[],referral_url:'https://example.com/?ref=AAAC'}:path==='/wallet'?{tickets:[]}:path==='/rooms'?{rooms:[]}:path==='/live/history'?{items:[]}:path.startsWith('/admin/tasks')?{items:[]}:path==='/admin/live-reviews'?{items:[]}:{};
`,ctx);
(async()=>{
 for(const slug of ['social','create-video','survey','daily','voice','live','team','agency']){const html=await vm.runInContext(`categoryPage('${slug}')`,ctx);assert.ok(html.length>200,slug);assert.ok(!html.includes('<img src=x'),slug+' must escape user data')}
 for(const section of ['tasks','module-settings','live-reviews']){const html=await vm.runInContext(`adminPage('${section}')`,ctx);assert.ok(html.includes('VIQ Control Center'))}
 const textForm=vm.runInContext("window.viqProofForm({id:1,proof_type:'text',submission:{id:2}})",ctx);assert.ok(textForm.includes('name="proof"'));assert.ok(!textForm.includes('type="file"'));
 const audioForm=vm.runInContext("window.viqProofForm({id:1,proof_type:'audio',category:'voice',description:'script',submission:{id:2}})",ctx);assert.ok(audioForm.includes('record-preview'));assert.ok(audioForm.includes('audio/*'));
 console.log('13 frontend component checks passed (8 module pages, 3 admin pages, 2 proof forms).');
})().catch(e=>{console.error(e);process.exitCode=1});
