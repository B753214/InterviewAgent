"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { api } from "@/lib/api";
import { streamAnswer } from "@/lib/sse";
import Button from "@/components/ui/button";
import Badge from "@/components/ui/badge";
import Card from "@/components/ui/card";

interface Option {
  id: string; name: string; chunk_count?: number; embedding_status?: string;
}

interface ChatMessage {
  role: "interviewer" | "user";
  content: string;
}

type Phase = "setup" | "active" | "ended";

export default function InterviewPage() {
  const [resumes, setResumes] = useState<Option[]>([]);
  const [jobs, setJobs] = useState<Option[]>([]);
  const [materials, setMaterials] = useState<Option[]>([]);
  const [selResume, setSelResume] = useState("");
  const [selJob, setSelJob] = useState("");
  const [selMaterials, setSelMaterials] = useState<string[]>([]);
  const [materialMode, setMaterialMode] = useState<"none" | "partial" | "all">("partial");
  const [maxRounds, setMaxRounds] = useState(6);

  const [phase, setPhase] = useState<Phase>("setup");
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [answer, setAnswer] = useState("");
  const [streaming, setStreaming] = useState("");
  const [loading, setLoading] = useState(false);
  const [round, setRound] = useState(0);
  const [assessment, setAssessment] = useState<{
    total_score: number; tech_score: number; communication_score: number;
    highlights: string[]; weaknesses: string[]; suggested_review: string[];
  } | null>(null);

  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.listResumes().then(setResumes).catch(() => {});
    api.listJobs().then(setJobs).catch(() => {});
    api.listMaterials().then(setMaterials).catch(() => {});
  }, []);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  const toggleMaterial = (id: string) =>
    setSelMaterials((prev) => prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]);

  const startInterview = async () => {
    setLoading(true);
    try {
      const data = await api.createInterview({
        resume_profile_id: selResume || null, job_profile_id: selJob || null,
        material_ids: selMaterials, use_all_materials: materialMode === "all", max_rounds: maxRounds,
      });
      setSessionId(data.session_id);
      setMessages([{ role: "interviewer", content: data.first_question }]);
      setRound(1); setPhase("active");
    } catch (e) { alert("创建面试失败: " + (e as Error).message); }
    setLoading(false);
  };

  const submitAnswer = useCallback(async () => {
    if (!answer.trim() || loading) return;
    const userMsg = answer; setAnswer("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setStreaming(""); setLoading(true);
    try {
      await streamAnswer(sessionId, userMsg, {
        onToken: (token) => setStreaming((prev) => prev + token),
        onMessageEnd: (fullText) => {
          setStreaming("");
          setMessages((prev) => [...prev, { role: "interviewer", content: fullText }]);
          setRound((r) => r + 1);
        },
        onAssessment: (data) => { setStreaming(""); setAssessment(data as typeof assessment); setPhase("ended"); },
        onError: async () => {
          try {
            const res = await api.submitAnswer(sessionId, userMsg);
            if (res.event === "assessment") { setAssessment(res.data as typeof assessment); setPhase("ended"); }
            else if (res.event === "message_end") { setMessages((prev) => [...prev, { role: "interviewer", content: res.data as string }]); setRound((r) => r + 1); }
          } catch (e) { alert("提交失败: " + (e as Error).message); }
        },
      });
    } catch {
      try {
        const res = await api.submitAnswer(sessionId, userMsg);
        if (res.event === "assessment") { setAssessment(res.data as typeof assessment); setPhase("ended"); }
        else if (res.event === "message_end") { setMessages((prev) => [...prev, { role: "interviewer", content: res.data as string }]); setRound((r) => r + 1); }
      } catch (e) { alert("提交失败: " + (e as Error).message); }
    }
    setLoading(false);
  }, [answer, loading, sessionId]);

  const endInterview = async () => {
    setLoading(true);
    try {
      const res = await api.finishInterview(sessionId);
      if (res.event === "assessment") { setAssessment(res.data as typeof assessment); setPhase("ended"); }
    } catch (e) { alert("结束失败: " + (e as Error).message); }
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submitAnswer(); }
  };

  const pillClass = (active: boolean, disabled = false) =>
    `px-3 py-1.5 rounded-lg text-xs font-medium border transition-all duration-150 ${
      disabled ? "bg-surface-raised border-border text-ink-faint/50 cursor-not-allowed" :
      active ? "bg-accent text-white border-accent shadow-sm" :
      "bg-surface border-border text-ink-muted hover:border-accent-muted hover:text-ink"
    }`;

  /* ==================== SETUP ==================== */
  if (phase === "setup") {
    return (
      <div>
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-ink mb-2">模拟面试</h1>
          <p className="text-sm text-ink-muted">选择画像与资料，配置面试参数</p>
        </div>

        <div className="space-y-6">
          <Card>
            <label className="text-sm font-semibold text-ink mb-3 block">简历画像</label>
            {resumes.length === 0 && <p className="text-xs text-ink-faint mb-3">暂无可选简历，请先到「我的档案」创建</p>}
            <div className="flex flex-wrap gap-2">
              {resumes.map((r) => (
                <button key={r.id} className={pillClass(selResume === r.id)}
                  onClick={() => setSelResume(selResume === r.id ? "" : r.id)}>{r.name}</button>
              ))}
            </div>
          </Card>

          <Card>
            <label className="text-sm font-semibold text-ink mb-3 block">岗位画像</label>
            {jobs.length === 0 && <p className="text-xs text-ink-faint mb-3">暂无可选岗位，请先到「我的档案」创建</p>}
            <div className="flex flex-wrap gap-2">
              {jobs.map((j) => (
                <button key={j.id} className={pillClass(selJob === j.id)}
                  onClick={() => setSelJob(selJob === j.id ? "" : j.id)}>{j.name}</button>
              ))}
            </div>
          </Card>

          <Card>
            <label className="text-sm font-semibold text-ink mb-3 block">资料策略</label>
            <div className="flex gap-2 mb-4">
              {[
                { key: "none", label: "不使用资料" },
                { key: "partial", label: "部分资料" },
                { key: "all", label: "全部资料" },
              ].map((mode) => (
                <button key={mode.key} className={pillClass(materialMode === mode.key)}
                  onClick={() => setMaterialMode(mode.key as typeof materialMode)}>{mode.label}</button>
              ))}
            </div>
            {materials.length === 0 && <p className="text-xs text-ink-faint mb-2">暂无可选资料</p>}
            <div className={`flex flex-wrap gap-2 ${materialMode !== "partial" ? "opacity-40 pointer-events-none" : ""}`}>
              {materials.map((m) => {
                const ready = !m.embedding_status || m.embedding_status === "ready";
                return (
                  <button key={m.id} disabled={!ready} className={pillClass(selMaterials.includes(m.id), !ready)}
                    onClick={() => ready && toggleMaterial(m.id)}>
                    {m.name}
                    {m.chunk_count != null && <span className="ml-1 text-[10px] opacity-60">{m.chunk_count}</span>}
                    {!ready && <span className="ml-1 text-[10px] opacity-60">{m.embedding_status}</span>}
                  </button>
                );
              })}
            </div>
          </Card>

          <Card>
            <label className="text-sm font-semibold text-ink mb-3 block">
              最大轮次: <span className="font-mono text-accent">{maxRounds}</span>
            </label>
            <input type="range" min={2} max={15} value={maxRounds}
              onChange={(e) => setMaxRounds(Number(e.target.value))} className="w-full" />
            <div className="flex justify-between text-[10px] text-ink-faint mt-1">
              <span>2</span><span>15</span>
            </div>
          </Card>

          <Button className="w-full" size="md" loading={loading} onClick={startInterview}>
            开始面试
          </Button>
        </div>
      </div>
    );
  }

  /* ==================== ACTIVE ==================== */
  if (phase === "active") {
    return (
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        <div className="flex items-center justify-between mb-4 shrink-0">
          <div>
            <h1 className="text-lg font-bold text-ink">模拟面试</h1>
            <p className="text-xs text-ink-muted">
              轮次 <span className="font-mono text-accent font-semibold">{round}</span> / {maxRounds}
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={endInterview} disabled={loading}>结束面试</Button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-accent text-white rounded-br-md"
                  : "bg-surface border border-border text-ink rounded-bl-md shadow-sm"
              }`}>{m.content}</div>
            </div>
          ))}
          {streaming && (
            <div className="flex justify-start">
              <div className="max-w-[85%] rounded-xl rounded-bl-md px-4 py-3 text-sm bg-surface border border-accent-muted text-ink shadow-sm">
                {streaming}
                <span className="inline-block w-1.5 h-4 bg-accent ml-0.5 animate-pulse align-middle rounded-sm" />
              </div>
            </div>
          )}
          <div ref={chatEnd} />
        </div>

        <div className="flex gap-2 items-end shrink-0">
          <textarea
            className="flex-1 border border-border rounded-xl px-4 py-3 text-sm resize-none bg-surface placeholder:text-ink-faint focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 transition-colors"
            rows={2} placeholder="输入你的回答... (Enter 发送，Shift+Enter 换行)"
            value={answer} onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={handleKeyDown} disabled={loading} />
          <Button onClick={submitAnswer} disabled={loading || !answer.trim()} loading={loading}>发送</Button>
        </div>
      </div>
    );
  }

  /* ==================== ASSESSMENT ==================== */
  return (
    <div>
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-ink mb-2">面试评估报告</h1>
        <p className="text-sm text-ink-muted">轮次 {round}/{maxRounds}</p>
      </div>

      <Card className="mb-8">
        <div className="grid grid-cols-3 gap-6 mb-8 pb-8 border-b border-border-light">
          {[
            { label: "总评分", value: assessment?.total_score },
            { label: "技术能力", value: assessment?.tech_score },
            { label: "沟通表达", value: assessment?.communication_score },
          ].map((s, idx) => (
            <div key={s.label} className="text-center">
              <div className={`text-4xl font-bold mb-1 font-mono ${
                idx === 0 ? "text-accent" : idx === 1 ? "text-ink" : "text-success"
              }`}>{s.value ?? "-"}</div>
              <div className="text-xs text-ink-faint">{s.label}</div>
            </div>
          ))}
        </div>

        {assessment && (
          <>
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-success mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-success" /> 表现亮点
              </h3>
              <ul className="space-y-2">
                {assessment.highlights.map((h, i) => (
                  <li key={i} className="text-sm text-ink-muted pl-5 relative before:absolute before:left-0 before:top-2 before:w-1 before:h-1 before:rounded-full before:bg-success/60">{h}</li>
                ))}
              </ul>
            </div>
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-danger mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-danger" /> 薄弱项
              </h3>
              <ul className="space-y-2">
                {assessment.weaknesses.map((w, i) => (
                  <li key={i} className="text-sm text-ink-muted pl-5 relative before:absolute before:left-0 before:top-2 before:w-1 before:h-1 before:rounded-full before:bg-danger/60">{w}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-ink mb-3">建议复习</h3>
              <div className="flex flex-wrap gap-2">
                {assessment.suggested_review.map((r, i) => <Badge key={i} tone="warning">{r}</Badge>)}
              </div>
            </div>
          </>
        )}
      </Card>

      <h2 className="text-sm font-semibold text-ink-faint mb-4">对话记录</h2>
      <div className="space-y-3 mb-8">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm ${
              m.role === "user"
                ? "bg-accent text-white rounded-br-md"
                : "bg-surface border border-border text-ink rounded-bl-md"
            }`}>{m.content}</div>
          </div>
        ))}
      </div>

      <Button onClick={() => { setPhase("setup"); setSessionId(""); setMessages([]); setAssessment(null); setRound(0); }}>
        开始新面试
      </Button>
    </div>
  );
}
