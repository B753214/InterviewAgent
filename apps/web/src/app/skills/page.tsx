"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Button from "@/components/ui/button";
import Badge from "@/components/ui/badge";
import Card from "@/components/ui/card";

interface Memory {
  id: string; topic: string; category: string; mastery_score: number;
  exposure_count: number; weakness_count: number;
  last_tested_at: string | null; next_review_at: string | null;
  source_interview_ids?: string[];
}

interface InterviewSummary {
  id: string; status: string; current_round: number; max_rounds: number;
  total_score: number | null; created_at: string;
  assessment_status: "pending" | "success" | "failed";
  assessment_error: string; memory_update_count: number;
}

const masteryLevel = (score: number) => {
  if (score >= 0.8) return { label: "精通", tone: "success" as const };
  if (score >= 0.6) return { label: "熟练", tone: "accent" as const };
  if (score >= 0.4) return { label: "了解", tone: "warning" as const };
  return { label: "薄弱", tone: "danger" as const };
};

const masteryBarColor = (score: number) => {
  if (score >= 0.8) return "bg-success";
  if (score >= 0.6) return "bg-accent";
  if (score >= 0.4) return "bg-warning";
  return "bg-danger";
};

export default function SkillsPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [interviews, setInterviews] = useState<InterviewSummary[]>([]);
  const [sortBy, setSortBy] = useState("mastery_score");
  const [rebuilding, setRebuilding] = useState(false);
  const [rebuildResult, setRebuildResult] = useState("");
  const [rebuildError, setRebuildError] = useState(false);
  const [assessingId, setAssessingId] = useState("");

  const load = async (nextSortBy = sortBy) => {
    const [memoryData, interviewData] = await Promise.all([api.listMemories(nextSortBy), api.listInterviews()]);
    setMemories(memoryData as Memory[]);
    setInterviews(interviewData as InterviewSummary[]);
  };

  useEffect(() => {
    Promise.all([api.listMemories(sortBy).catch(() => []), api.listInterviews().catch(() => [])]).then(([memoryData, interviewData]) => {
      setMemories(memoryData as Memory[]);
      setInterviews(interviewData as InterviewSummary[]);
    });
  }, [sortBy]);

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });

  const rebuild = async () => {
    setRebuilding(true); setRebuildResult(""); setRebuildError(false);
    try {
      const result = await api.rebuildMemories();
      if (result.interview_count === 0) { setRebuildResult("没有可用于重建的成功评估面试"); setRebuildError(true); }
      else { setRebuildResult(`已重建 ${result.interview_count} 场面试记忆，成功 ${result.success_count} 场，共 ${result.memory_count} 条知识点`); }
      await load();
    } catch (err) { setRebuildResult(err instanceof Error ? err.message : "重建失败"); setRebuildError(true); }
    finally { setRebuilding(false); }
  };

  const assessInterview = async (id: string) => {
    setAssessingId(id); setRebuildResult("");
    try { await api.assessInterview(id); await load(); }
    catch (err) { setRebuildResult(err instanceof Error ? err.message : "评估失败"); setRebuildError(true); await load(); }
    finally { setAssessingId(""); }
  };

  const SORT_OPTIONS = [
    { key: "mastery_score", label: "掌握度" },
    { key: "exposure_count", label: "考察次数" },
    { key: "weakness_count", label: "薄弱次数" },
    { key: "last_tested_at", label: "最近考察" },
  ];

  return (
    <div>
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-ink mb-2">能力图谱</h1>
        <p className="text-sm text-ink-muted">追踪面试中的知识点掌握情况，发现能力短板</p>
      </div>

      <div className="flex items-center justify-between gap-4 mb-6">
        <div className="flex gap-2">
          {SORT_OPTIONS.map((opt) => (
            <button key={opt.key}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                sortBy === opt.key ? "bg-accent text-white shadow-sm" : "bg-surface border border-border text-ink-muted hover:border-accent-muted"
              }`}
              onClick={() => setSortBy(opt.key)}>{opt.label}</button>
          ))}
        </div>
        <Button variant="secondary" size="sm" loading={rebuilding} onClick={rebuild}>从历史重建</Button>
      </div>

      {rebuildResult && (
        <div className={`mb-6 rounded-xl border px-4 py-3 text-sm ${
          rebuildError ? "border-danger/20 bg-danger-soft text-danger" : "border-success/20 bg-success-soft text-success"
        }`}>{rebuildResult}</div>
      )}

      {/* Knowledge table */}
      <div className="rounded-xl border border-border bg-surface overflow-hidden mb-10">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left bg-surface-raised/50">
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">知识点</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">分类</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">掌握度</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">考察/薄弱</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">来源</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">下次复习</th>
              </tr>
            </thead>
            <tbody>
              {memories.map((m) => {
                const lvl = masteryLevel(m.mastery_score);
                const barColor = masteryBarColor(m.mastery_score);
                return (
                  <tr key={m.id} className="border-b border-border-light/50 last:border-0 hover:bg-surface-hover/50 transition-colors">
                    <td className="px-4 py-3 font-medium text-ink">{m.topic}</td>
                    <td className="px-4 py-3 text-ink-muted text-xs">{m.category || "—"}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-20 h-1.5 rounded-full bg-surface-raised overflow-hidden">
                          <div className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                            style={{ width: `${Math.round(m.mastery_score * 100)}%` }} />
                        </div>
                        <span className="font-mono text-xs font-semibold text-ink">{Math.round(m.mastery_score * 100)}%</span>
                        <Badge tone={lvl.tone}>{lvl.label}</Badge>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-ink-muted text-xs">{m.exposure_count} / {m.weakness_count}</td>
                    <td className="px-4 py-3 text-ink-muted text-xs">{m.source_interview_ids?.length ?? 0}</td>
                    <td className="px-4 py-3 text-ink-faint text-xs">{m.next_review_at ? m.next_review_at.slice(0, 10) : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {memories.length === 0 && (
          <div className="text-center py-16">
            <div className="w-10 h-10 mx-auto mb-3 rounded-full bg-surface-raised flex items-center justify-center text-ink-faint">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5" />
              </svg>
            </div>
            <p className="text-sm text-ink-faint">暂无知识点数据 — 完成一次面试评估后自动生成</p>
          </div>
        )}
      </div>

      {/* Interview assessment table */}
      <div className="flex items-center justify-between gap-4 mb-4">
        <h2 className="text-lg font-bold text-ink">面试评估状态</h2>
        <span className="text-xs text-ink-faint">{interviews.length} 场</span>
      </div>

      <div className="rounded-xl border border-border bg-surface overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left bg-surface-raised/50">
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">时间</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">轮次</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">评估状态</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">评分</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">记忆更新</th>
                <th className="px-4 py-3 font-medium text-ink-faint text-xs">操作</th>
              </tr>
            </thead>
            <tbody>
              {interviews.map((iv) => (
                <tr key={iv.id} className="border-b border-border-light/50 last:border-0 hover:bg-surface-hover/50 transition-colors">
                  <td className="px-4 py-3 text-ink-muted text-xs">{formatDate(iv.created_at)}</td>
                  <td className="px-4 py-3 text-ink-muted text-xs">{iv.current_round}/{iv.max_rounds}</td>
                  <td className="px-4 py-3">
                    <Badge tone={iv.assessment_status === "success" ? "success" : iv.assessment_status === "failed" ? "danger" : "warning"}>
                      {iv.assessment_status === "success" ? "已评估" : iv.assessment_status === "failed" ? "评估失败" : "未评估"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-ink-muted text-xs">{iv.total_score ?? "—"}</td>
                  <td className="px-4 py-3 text-ink-muted text-xs">{iv.memory_update_count}</td>
                  <td className="px-4 py-3">
                    {iv.assessment_status !== "success" ? (
                      <Button size="sm" loading={assessingId === iv.id} onClick={() => assessInterview(iv.id)}>评估</Button>
                    ) : <span className="text-xs text-ink-faint">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {interviews.length === 0 && (
          <p className="text-sm text-ink-faint py-12 text-center">暂无面试历史</p>
        )}
      </div>
    </div>
  );
}
