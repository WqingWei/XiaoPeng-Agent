"use client";

import { Ban, BrainCircuit, ListChecks, ShieldAlert, Wrench } from "lucide-react";

import { ForbiddenCard } from "@/components/ForbiddenCard";
import { IntentCard } from "@/components/IntentCard";
import { SafetyAlertCard } from "@/components/SafetyAlertCard";
import { ServicePlanCard } from "@/components/ServicePlanCard";
import { ToolCallCard } from "@/components/ToolCallCard";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatStore } from "@/stores";

export function AgentPanel() {
  const response = useChatStore((state) => state.selectedResponse);

  return (
    <aside id="agent-panel" className="flex min-h-[520px] min-w-0 flex-col border-t border-white/10 bg-card/70 lg:min-h-0 lg:border-t-0 lg:border-l">
      <div className="border-b border-white/8 px-4 py-4">
        <p className="text-[10px] font-semibold tracking-[0.2em] text-xpeng-green">AGENT INSIGHTS</p>
        <div className="mt-1 flex items-center justify-between gap-2">
          <h2 className="text-base font-semibold">决策详情</h2>
          {response ? <span className="text-[10px] text-muted-foreground">Turn {response.turn_id}</span> : null}
        </div>
      </div>

      <ScrollArea className="min-h-0 flex-1">
        {response ? (
          <Accordion className="px-3 py-2" defaultValue={["intent", "plan"]} multiple>
            <DetailSection icon={BrainCircuit} label="意图分析" value="intent">
              <IntentCard reasoning={response.reasoning} />
            </DetailSection>
            <DetailSection count={response.service_plan.steps.length} icon={ListChecks} label="服务计划" value="plan">
              <ServicePlanCard plan={response.service_plan} />
            </DetailSection>
            <DetailSection count={response.service_plan.steps.length} icon={Wrench} label="工具调用" value="tools">
              <div className="space-y-2.5">
                {response.service_plan.steps.length ? response.service_plan.steps.map((step) => (
                  <ToolCallCard
                    key={step.step_id}
                    reason={response.reasoning.tool_selection_reasons.find((item) => item.tool === step.tool)}
                    result={response.tool_results.find((item) => item.step_id === step.step_id)}
                    step={step}
                  />
                )) : <EmptyDetail text="本轮没有工具调用" />}
              </div>
            </DetailSection>
            <DetailSection count={response.safety_alerts.length} icon={ShieldAlert} label="安全警告" value="safety">
              <div className="space-y-2.5">
                {response.safety_alerts.length ? response.safety_alerts.map((alert, index) => <SafetyAlertCard key={`${alert.rule_id}-${index}`} alert={alert} />) : <EmptyDetail text="本轮未触发安全告警" />}
              </div>
            </DetailSection>
            <DetailSection count={response.forbidden_actions.length} icon={Ban} label="禁止动作" value="forbidden">
              <div className="space-y-2.5">
                {response.forbidden_actions.length ? response.forbidden_actions.map((forbidden, index) => <ForbiddenCard key={`${forbidden.rule_id}-${index}`} forbidden={forbidden} />) : <EmptyDetail text="本轮没有禁止动作" />}
              </div>
            </DetailSection>
          </Accordion>
        ) : (
          <div className="grid min-h-80 place-items-center px-8 text-center">
            <div>
              <span className="mx-auto grid size-11 place-items-center rounded-2xl border border-white/10 bg-white/[0.03] text-muted-foreground"><BrainCircuit className="size-5" /></span>
              <p className="mt-3 text-sm font-medium">等待 Agent 响应</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">完成一次对话后，这里将展示意图、计划、安全规则与工具调用</p>
            </div>
          </div>
        )}
      </ScrollArea>
    </aside>
  );
}

function DetailSection({ value, label, icon: Icon, count, children }: { value: string; label: string; icon: typeof BrainCircuit; count?: number; children: React.ReactNode }) {
  return (
    <AccordionItem className="border-white/8" value={value}>
      <AccordionTrigger className="px-1 hover:no-underline">
        <span className="flex items-center gap-2"><Icon className="size-4 text-xpeng-green" />{label}{count !== undefined ? <span className="rounded-full bg-white/6 px-1.5 py-0.5 text-[9px] text-muted-foreground">{count}</span> : null}</span>
      </AccordionTrigger>
      <AccordionContent>{children}</AccordionContent>
    </AccordionItem>
  );
}

function EmptyDetail({ text }: { text: string }) {
  return <p className="rounded-xl border border-dashed border-white/10 p-3 text-center text-xs text-muted-foreground">{text}</p>;
}
