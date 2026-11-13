// Component-render smoke tests: no browser, network, or production credentials.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const noop=()=>{}, el={addEventListener:noop,classList:{add:noop,remove:noop,toggle:noop},setAttribute:noop,insertAdjacentHTML:noop,dataset:{},querySelector:()=>el,innerHTML:'',textContent:''};
const ctx=vm.createContext({console,URLSearchParams,Date,setTimeout:noop,clearTimeout:noop,setInterval:noop,clearInterval:noop,document:{body:el,querySelector:()=>el,querySelectorAll:()=>[],addEventListener:noop},window:{addEventListener:noop},localStorage:{getItem:()=>null,setItem:noop},location:{search:'',hash:'#home'},navigator:{onLine:true},fetch:async()=>({ok:true,json:async()=>({})})});
for(const file of ['v2-ui.js','v3-ui.js','v4-ui.js','v5-ui.js','app.js']){let code=fs.readFileSync('static/'+file,'utf8');if(file==='app.js')code=code.slice(0,code.indexOf('(async()=>{try{config='));vm.runInContext(code,ctx)}
vm.runInContext(`
user={id:2,name:'Worker',role:'admin',balance:100000};
config={categories:['social','create-video','survey','daily','voice','live','team','agency'].map(slug=>({slug,name:slug,enabled:true})),settings:{survey_daily_limit:'5',video_claim_hours:'24',agency_fee:'1000',signup_member:'10',signup_referrer:'5',agency_signup_member:'30',agency_signup_referrer:'50',agency_commission_percent:'5',live_rate:'1',live_daily_minutes:'60',live_enabled:'true'}};
api=async path=>path.startsWith('/tasks?')?{tasks:[{id:1,title:'<img src=x onerror=alert(1)>',category:path.split('=')[1],description:'Read this script',proof_type:path.includes('voice')?'audio':'text',reward:100,active:true,submission:{id:1,status:'started'}}]}:path==='/modules/progress'?{survey_used:2,survey_limit:5,reset_at:2000000000}:path==='/team'?{code:'AAAC',commission:500,agency_approved:false,members:[],referral_url:'https://example.com/?ref=AAAC'}:path==='/wallet'?{tickets:[],ledger:[]}:path==='/community/rooms'?{items:[]}:path==='/rooms'?{rooms:[]}:path==='/live/history'?{items:[]}:path.startsWith('/admin/tasks')?{items:[]}:path==='/admin/live-reviews'?{items:[]}:{};
`,ctx);
(async()=>{
 for(const slug of ['social','create-video','survey','daily','voice','live','team','agency']){const html=await vm.runInContext(`categoryPage('${slug}')`,ctx);assert.ok(html.length>200,slug);assert.ok(!html.includes('<img src=x'),slug+' must escape user data')}
 for(const section of ['tasks','module-settings','live-reviews']){const html=await vm.runInContext(`adminPage('${section}')`,ctx);assert.ok(html.includes('VIQ Control Center'))}
 const textForm=vm.runInContext("window.viqProofForm({id:1,proof_type:'text',submission:{id:2}})",ctx);assert.ok(textForm.includes('name="proof"'));assert.ok(!textForm.includes('type="file"'));
 const audioForm=vm.runInContext("window.viqProofForm({id:1,proof_type:'audio',category:'voice',description:'script',submission:{id:2}})",ctx);assert.ok(audioForm.includes('record-preview'));assert.ok(audioForm.includes('audio/*'));
 vm.runInContext(`
 config.categories.push(...['recharge','exchange','watch-video','pages','groups','gmail'].map(slug=>({slug,name:slug,enabled:true})));
 user.balance=100000;
 const priorApi=api;
 api=async path=>path==='/fx'?{currencies:[{code:'USD',flag:'🇺🇸',symbol:'$',name:'US Dollar',rate:12000,enabled:true}],holdings:[],trades:[]}:path.startsWith('/market/')?{items:[]}:path==='/clips'?{items:[],batch_progress:0}:path==='/deals'?{items:[]}:path==='/deals/1'?{deal:{id:1,title:'Page deal',category:'pages',status:'pending',amount:10000,buyer_id:2,seller_id:3},buyer:'Buyer',seller:'Seller',admin_profile:'Pages Admin',messages:[{sender:3,name:'Seller',body:'<script>alert(1)</script>',created:1}]}:path==='/community/profile'?{profile:{name:'Live name',bio:'Bio'},coins:10000,ledger:[]}:path==='/admin/clips'?{items:[]}:path==='/admin/market-profiles'?{items:['pages','groups','gmail'].map(slug=>({slug,name:slug,held:0,counts:{}}))}:priorApi(path);
 `,ctx);
 for(const slug of ['recharge','exchange','watch-video','pages','groups','gmail']){const html=await vm.runInContext(`categoryPage('${slug}')`,ctx);assert.ok(html.length>400,slug);if(process.argv.includes('--preview')&&slug==='recharge')fs.writeFileSync('static/qa-recharge.html','<!doctype html><html lang="bn"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/static/style.css"><link rel="stylesheet" href="/static/v4.css"><title>VIQ recharge — QA fixture</title><body><main style="max-width:1000px;margin:40px auto;padding:16px">'+html+'</main></body></html>')}
 for(const page of ['deals','deal','community-profile']){const html=await vm.runInContext(`window.viqExtendedPage('${page}',['${page}','1'])`,ctx);assert.ok(html.length>100,page);assert.ok(!html.includes('<script>alert(1)'),page)}
 for(const section of ['clips','fx','market-profiles'])assert.ok((await vm.runInContext(`adminPage('${section}')`,ctx)).includes('VIQ Studio'));
 console.log('12 additional v4 component checks passed (6 modules, 3 community/deal pages, 3 admin pages).');
 console.log('13 frontend component checks passed (8 module pages, 3 admin pages, 2 proof forms).');
})().catch(e=>{console.error(e);process.exitCode=1});
