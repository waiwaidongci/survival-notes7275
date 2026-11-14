<script setup lang="ts">import {computed,reactive,ref} from 'vue';import {useResearch} from '../stores/research';import {useAuth} from '../stores/auth';import {useAction} from '../hooks/useAction';import {submitCorrection,getRevisions} from '../api/corrections';import {CorrectionItem,RevisionHistory} from '../types/domain';import {CorrectionStatus,RevisionSource} from '../constants/enums';import {time} from '../utils/format';import Notice from './common/Notice.vue';import DataTable from './common/DataTable.vue';
const s=useResearch(),auth=useAuth(),a=useAction();
const emit=defineEmits<{applied:[]}>();
interface Row{specimen_code:string;expected_revision:number;duration_hours:string;event_observed:string}
const empty=():Row=>({specimen_code:'',expected_revision:1,duration_hours:'',event_observed:''});
const rows=reactive<Row[]>([empty()]);
const reason=ref('');
function addRow(){rows.push(empty())}
function removeRow(i:number){if(rows.length>1)rows.splice(i,1)}
const payload=computed<CorrectionItem[]>(()=>rows.filter(r=>r.specimen_code.trim()).map(r=>({specimen_code:r.specimen_code.trim(),expected_revision:r.expected_revision,duration_hours:r.duration_hours===''?null:Number(r.duration_hours),event_observed:r.event_observed===''?null:r.event_observed==='true'})));
const canSubmit=computed(()=>reason.value.trim().length>=8&&payload.value.length>0&&payload.value.every(r=>r.duration_hours!==null||r.event_observed!==null));
function submit(){a.execute(async()=>{await submitCorrection(reason.value.trim(),payload.value);reason.value='';rows.splice(0,rows.length,...[empty()]);await s.refresh();emit('applied')})}
const history=ref<RevisionHistory|null>(null);
async function openHistory(code:string){try{history.value=await getRevisions(code)}catch(e){a.error.value=(e as Error).message}}
const ledger=computed(()=>s.corrections.slice(0,12));
defineExpose({openHistory});
</script>
<template><section class="correction-panel">
  <div class="section-heading"><h2>终态随访整批更正</h2><span>按试件修订号提交 · 同号异值整批拒绝</span></div>
  <Notice :message="a.error.value" @retry="a.error.value=''"/>
  <p class="caption">终态时长或失效状态误记时在此整批更正，不再只补备注。每条须填写试件编号与该试件<b>当前修订号</b>（见下表），系统按修订号识别乱序与重复；更正生效后仅受影响研究自动重算，获批导出暂停直至重新确认。</p>
  <form v-if="auth.user?.role!=='viewer'" @submit.prevent="submit">
    <label class="reason-label">更正理由（随台账永久留痕，至少8字）<textarea aria-label="更正理由" v-model="reason" minlength="8" maxlength="1000" required placeholder="例如：现场复核发现ZH-A-0007截止仍工作却误记为失效，按复核记录整批更正。"/></label>
    <DataTable :head="['试件编号','当前修订号','更正后时长 / h（留空不改）','更正后状态（留空不改）','操作']">
      <tr v-for="(r,i) in rows" :key="i">
        <td><input aria-label="试件编号" v-model="r.specimen_code" required placeholder="如 ZH-A-0007" style="min-width:150px"/></td>
        <td><input aria-label="当前修订号" v-model.number="r.expected_revision" type="number" min="1" required style="min-width:90px"/></td>
        <td><input aria-label="更正后时长" v-model="r.duration_hours" type="number" step="25" min="1" max="1000000" placeholder="留空表示不修改" style="min-width:170px"/></td>
        <td><select aria-label="更正后状态" v-model="r.event_observed" style="min-width:140px"><option value="">留空表示不修改</option><option value="true">失效事件</option><option value="false">右删失</option></select></td>
        <td><button type="button" class="text-link" @click="removeRow(i)">移除</button></td>
      </tr>
    </DataTable>
    <div class="correction-actions"><button type="button" class="outline" @click="addRow">添加一行试件</button><button class="primary" :disabled="a.busy.value||!canSubmit">提交整批更正</button></div>
  </form>
  <p v-else class="role-note">阅读者只能查看更正台账与修订历史；整批更正需要研究员或负责人权限。</p>
  <div class="section-heading"><h2>更正台账（最近12批）</h2><span>生效与拒绝都留痕</span></div>
  <DataTable :head="['批次','时间','执行者','状态','更正试件数','受影响研究','拒绝原因 / 生效修订']">
    <tr v-for="c in ledger" :key="c.id" :class="['ledger-row',c.status]">
      <td class="mono">#{{c.id}}</td><td>{{time(c.created_at)}}</td><td>{{c.owner}}</td>
      <td><span :class="['review-badge',c.status]">{{CorrectionStatus[c.status as keyof typeof CorrectionStatus]}}</span></td>
      <td>{{c.items.length}}</td>
      <td class="mono">{{c.affected_run_ids.length?c.affected_run_ids.map(x=>'#'+x).join(' '):'—'}}</td>
      <td class="reject-cell">{{c.status==='rejected'?c.reject_reason:'生效为全局数据修订 '+c.applied_revision}}</td>
    </tr>
  </DataTable>
  <div v-if="history" class="history-drawer" role="dialog" aria-label="修订历史">
    <div class="history-head"><b>{{history.specimen_code}} 的随访修订历史</b><button class="text-link" @click="history=null">关闭</button></div>
    <DataTable :head="['修订号','来源','时长 / h','状态','备注','记录时间','执行者']">
      <tr v-for="v in history.revisions" :key="v.id">
        <td class="mono">rev {{v.revision_no}}</td>
        <td>{{RevisionSource[v.source as keyof typeof RevisionSource]||v.source}}</td>
        <td>{{v.duration_hours}}</td>
        <td><span :class="['event-tag',v.event_observed?'event':'censored']">{{v.event_observed?'失效事件':'右删失'}}</span></td>
        <td class="note-cell">{{v.note}}</td><td>{{time(v.created_at)}}</td><td>{{v.owner}}</td>
      </tr>
    </DataTable>
  </div>
</section></template>
