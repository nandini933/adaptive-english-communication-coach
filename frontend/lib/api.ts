const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api/v1";
export async function api<T=unknown>(path:string,options:RequestInit={}):Promise<T>{
  const token=typeof window!=="undefined"?localStorage.getItem("token"):null;
  let res:Response;
  try { res=await fetch(`${API}${path}`,{...options,headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`}:{}) ,...options.headers}}); }
  catch { throw new Error("We could not reach the learning service. Check your connection and try again."); }
  if(!res.ok){const body=await res.json().catch(()=>({detail:"Request failed"})); throw new Error(typeof body.detail==="string"?body.detail:"The request could not be completed.");}
  if(res.status===204)return undefined as T;
  return res.json();
}
