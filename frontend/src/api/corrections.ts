import {request} from './client';import {Correction,RevisionHistory,CorrectionItem} from '../types/domain';
export const getCorrections=()=>request<Correction[]>('/followups/corrections');
export const submitCorrection=(reason:string,items:CorrectionItem[])=>request<Correction>('/followups/corrections',{method:'POST',body:JSON.stringify({reason,items})});
export const getRevisions=(code:string)=>request<RevisionHistory>(`/specimens/${encodeURIComponent(code)}/revisions`);
