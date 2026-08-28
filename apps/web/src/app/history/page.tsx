"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Card from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import Button from "@/components/ui/button";

interface InterviewSummary {
  id: string; status: string; current_round: number; max_rounds: number;
  total_score: number | null; created_at: string;
}

interface AssessmentResult {
  total_score: number; tech_score: number; communication_score: number;
  highlights: string[]; weaknesses: string[]; suggested_review: string[];
}

interface ChatMessage { role: "interviewer" | "user"; content: string; }

interface InterviewDetail {
  id: string; status: string; messages: ChatMessage[]; current_round: number;
  max_rounds: number; assessment: AssessmentResult | null; created_at: string;
}

export default function HistoryPage() {
  const [interviews, setInterviews] = useState<InterviewSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<InterviewDetail | null>(null);

  useEffect(() => { api.listInterviews().then(setInterviews).catch(() => {}).finally(() => setLoading(false)); }, []);

  const openDetail = async (id: string) => {
    try { setSelected(await api.getInterview(id) as InterviewDetail); }
    catch { alert("加载面试详情失败"); }
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  const statusLabel = (s: string) => s === "active" ? "进行中" : "已结束";

  /* ==================== DETAIL ==================== */
  if (selected) {
    const a = selected.assessment;
    return (
      <div>
        <button className="text-sm text-ink-muted hover:text-ink mb-6 flex items-center gap-1 transition-colors"
          onClick={() => setSelected(null)}>← 返回列表</button>

        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-ink mb-2">面试详情</h1>
          <p className="text-xs text-ink-faint">
            {formatDate(selected.created_at)} · {selected.current_round}/{selected.max_rounds} 轮 · {statusLabel(selected.status)}
          </p>
        </div>

        {a && (
          <Card className="mb-8">
            <div className="grid grid-cols-3 gap-6 mb-8 pb-8 border-b border-border-light">
              {[
                { label: "总评分", value: a.total_score },
                { label: "技术能力", value: a.tech_score },
                { label: "沟通表达", value: a.communication_score },
              ].map((s, idx) => (
                <div key={s.label} className="text-center">
                  <div className={`text-4xl font-bold mb-1 font-mono ${
                    idx === 0 ? "text-accent" : idx === 1 ? "text-ink" : "text-success"
                  }`}>{s.value}</div>
                  <div className="text-xs text-ink-faint">{s.label}</div>
                </div>
              ))}
            </div>
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-success mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-success" /> 表现亮点
              </h3>
              <ul className="space-y-2">
                {a.highlights.map((h, i) => (
                  <li key={i} className="text-sm text-ink-muted pl-5 relative before:absolute before:left-0 before:top-2 before:w-1 before:h-1 before:rounded-full before:bg-success/60">{h}</li>
                ))}
              </ul>
            </div>
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-danger mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-danger" /> 薄弱项
              </h3>
              <ul className="space-y-2">
                {a.weaknesses.map((w, i) => (
                  <li key={i} className="text-sm text-ink-muted pl-5 relative before:absolute before:left-0 before:top-2 before:w-1 before:h-1 before:rounded-full before:bg-danger/60">{w}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-ink mb-3">建议复习</h3>
              <div className="flex flex-wrap gap-2">
                {a.suggested_review.map((r, i) => <Badge key={i} tone="warning">{r}</Badge>)}
              </div>
            </div>
          </Card>
        )}

        <h2 className="text-sm font-semibold text-ink-faint mb-4">对话记录</h2>
        <div className="space-y-3">
          {selected.messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm ${
                m.role === "user" ? "bg-accent text-white rounded-br-md" : "bg-surface border border-border text-ink rounded-bl-md"
              }`}>{m.content}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  /* ==================== LIST ==================== */
  if (loading) return <p className="text-sm text-ink-faint text-center py-16">加载中...</p>;

  if (interviews.length === 0) {
    return (
      <div className="text-center py-16">
        <h1 className="text-2xl font-bold text-ink mb-2">面试历史</h1>
        <p className="text-sm text-ink-faint">暂无面试记录，去<a href="/interview" className="text-accent hover:underline mx-1">开始模拟面试</a></p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-ink mb-2">面试历史</h1>
        <p className="text-sm text-ink-muted">{interviews.length} 场面试记录</p>
      </div>

      <div className="space-y-2.5 stagger">
        {interviews.map((iv) => (
          <Card key={iv.id} hover onClick={() => openDetail(iv.id)} className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-ink">{formatDate(iv.created_at)}</span>
                <Badge tone={iv.status === "active" ? "success" : "neutral"}>{statusLabel(iv.status)}</Badge>
              </div>
              <div className="flex items-center gap-5 text-xs text-ink-muted">
                <span>{iv.current_round}/{iv.max_rounds} 轮</span>
                {iv.total_score != null && <span className="font-mono font-semibold text-ink text-sm">{iv.total_score} 分</span>}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-ink-faint">
                  <polyline points="9,5 16,12 9,19" />
                </svg>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
