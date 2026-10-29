"use client";
import {useState} from "react";
import {useRouter} from "next/navigation";
import Link from "next/link";
import {api} from "../../lib/api";

export default function Onboarding(){
  const [goals,setGoals]=useState<string[]>([]),[practice,setPractice]=useState(10),[challenge,setChallenge]=useState("clear and concise writing"),[level,setLevel]=useState("intermediate"),[sample,setSample]=useState("");
  const [busy,setBusy]=useState(false),[error,setError]=useState(""); const router=useRouter();
  const options=["Write clear emails and updates","Speak up in meetings","Explain technical work","Present results to stakeholders"];
  function toggle(value:string){setGoals(g=>g.includes(value)?g.filter(x=>x!==value):[...g,value]);}
  async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError("");try{
    await api("/profile",{method:"PUT",body:JSON.stringify({goals,practice_minutes:practice,challenges:[challenge],self_assessed_proficiency:level})});
    if(sample.trim()) await api("/assessment",{method:"POST",body:JSON.stringify({answers:{workplace_sample:sample.trim()}})});
    router.push("/dashboard");
  }catch(e){setError(e instanceof Error?e.message:"We could not save your setup. Retry when connected.")}finally{setBusy(false)}}
  return <main className="min-h-screen bg-mist px-4 py-10"><form onSubmit={submit} className="card mx-auto max-w-2xl"><Link href="/" className="text-sm text-teal-700">CommunicateIQ</Link><p className="mt-5 text-sm font-semibold text-teal-700">FIRST, MAKE IT YOURS</p><h1 className="mt-1 text-3xl font-bold">What would you like to communicate better?</h1><p className="mt-2 text-slate-600">This profile is for your coaching. Your answers are not shared with a manager.</p>
    <fieldset className="mt-7"><legend className="font-semibold">Choose your goals</legend><div className="mt-3 grid gap-2 sm:grid-cols-2">{options.map(o=><label key={o} className="flex items-start gap-3 rounded-xl border p-3"><input type="checkbox" className="mt-1 accent-teal-700" checked={goals.includes(o)} onChange={()=>toggle(o)}/><span className="text-sm">{o}</span></label>)}</div></fieldset>
    <div className="mt-6 grid gap-4 sm:grid-cols-2"><label className="text-sm font-semibold">Practice time each day<select className="mt-2 w-full rounded-lg border p-2 font-normal" value={practice} onChange={e=>setPractice(Number(e.target.value))}>{[5,10,15,20,30,45,60].map(n=><option key={n} value={n}>{n} minutes</option>)}</select></label><label className="text-sm font-semibold">Your current self-assessment<select className="mt-2 w-full rounded-lg border p-2 font-normal" value={level} onChange={e=>setLevel(e.target.value)}>{["beginner","elementary","intermediate","advanced"].map(n=><option key={n}>{n}</option>)}</select><span className="mt-1 block font-normal text-slate-500">Used to tailor explanations, not treated as a verified score.</span></label></div>
    <label className="mt-6 block text-sm font-semibold">What feels hardest at work?<select className="mt-2 w-full rounded-lg border p-2 font-normal" value={challenge} onChange={e=>setChallenge(e.target.value)}>{["clear and concise writing","grammar in the moment","finding the right vocabulary","organizing a spoken update","explaining technical work","speaking up in meetings"].map(n=><option key={n}>{n}</option>)}</select></label>
    <label className="mt-6 block text-sm font-semibold">Optional baseline: write a short update about a current or fictional work task<textarea className="mt-2 min-h-32 w-full rounded-lg border p-3 font-normal" maxLength={3000} value={sample} onChange={e=>setSample(e.target.value)} placeholder="What is the outcome, what have you done, and what happens next?"/><span className="mt-1 block font-normal text-slate-500">Text-only checks assess a small writing sample. Speaking and accent are not evaluated here.</span></label>
    {error&&<p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}<button disabled={busy} className="btn mt-6 w-full disabled:opacity-60">{busy?"Saving your profile…":"Save and open my dashboard"}</button></form></main>
}
