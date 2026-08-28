"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Tabs from "@/components/ui/tabs";
import Button from "@/components/ui/button";
import Badge from "@/components/ui/badge";
import { Input, Textarea } from "@/components/ui/input";
import Card from "@/components/ui/card";

/* ---------- types ---------- */

interface Resume {
  id: string; name: string; raw_text: string; created_at: string;
  summary_json?: { summary?: string };
  skills_json?: Record<string, string[]>;
  project_highlights?: string[];
  potential_questions_json?: string[];
}

interface Job {
  id: string; name: string; company: string; raw_text: string; created_at: string;
  summary_json?: { summary?: string };
  must_have_skills_json?: string[];
  domain?: string;
  level?: string;
}

interface Material {
  id: string; name: string; type: string; raw_text: string; enabled: boolean; created_at: string;
  chunk_count: number; embedding_status: string;
  source_file_path?: string; processing_error?: string;
}

/* ---------- expandable list ---------- */

function ExpandableList<T extends { id: string; name: string; created_at: string }>({
  items,
  emptyText,
  renderSummary,
  renderDetail,
  expanded,
  detail,
  onToggle,
}: {
  items: T[];
  emptyText: string;
  renderSummary: (item: T) => React.ReactNode;
  renderDetail: (item: T, detail: any) => React.ReactNode;
  expanded: string | null;
  detail: any;
  onToggle: (id: string) => void;
}) {
  if (items.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-10 h-10 mx-auto mb-3 rounded-full bg-surface-raised flex items-center justify-center text-ink-faint">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="3" />
            <line x1="12" y1="8" x2="12" y2="16" />
            <line x1="8" y1="12" x2="16" y2="12" />
          </svg>
        </div>
        <p className="text-sm text-ink-faint">{emptyText}</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item) => {
        const isOpen = expanded === item.id;
        return (
          <div key={item.id} className="rounded-xl border border-border bg-surface overflow-hidden">
            <button
              className="w-full text-left px-4 py-3.5 flex justify-between items-center hover:bg-surface-hover transition-colors"
              onClick={() => onToggle(item.id)}
            >
              <div className="flex items-center gap-3 min-w-0">
                {renderSummary(item)}
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs text-ink-faint">{item.created_at?.slice(0, 10)}</span>
                <svg
                  width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  className={`text-ink-faint transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
                >
                  <polyline points="6,9 12,15 18,9" />
                </svg>
              </div>
            </button>
            {isOpen && detail && (
              <div className="px-4 pb-4 border-t border-border-light pt-3 animate-fade-in">
                {renderDetail(item, detail)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ---------- page ---------- */

const TABS = [
  { key: "resumes", label: "简历画像" },
  { key: "jobs", label: "岗位画像" },
  { key: "materials", label: "面试资料" },
];

export default function ProfilePage() {
  const [tab, setTab] = useState("resumes");

  const [resumes, setResumes] = useState<Resume[]>([]);
  const [resumeName, setResumeName] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [resumeLoading, setResumeLoading] = useState(false);

  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobName, setJobName] = useState("");
  const [jobCompany, setJobCompany] = useState("");
  const [jobText, setJobText] = useState("");
  const [jobLoading, setJobLoading] = useState(false);

  const [materials, setMaterials] = useState<Material[]>([]);
  const [matName, setMatName] = useState("");
  const [matText, setMatText] = useState("");
  const [matLoading, setMatLoading] = useState(false);
  const [pdfName, setPdfName] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfUploading, setPdfUploading] = useState(false);
  const [matError, setMatError] = useState("");

  const [expanded, setExpanded] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);

  useEffect(() => {
    api.listResumes().then((d) => setResumes(d as Resume[])).catch(() => {});
    api.listJobs().then((d) => setJobs(d as Job[])).catch(() => {});
    api.listMaterials().then((d) => setMaterials(d as Material[])).catch((e) => setMatError((e as Error).message));
  }, []);

  const reload = async (t: string) => {
    if (t === "resumes") setResumes((await api.listResumes()) as Resume[]);
    else if (t === "jobs") setJobs((await api.listJobs()) as Job[]);
    else {
      try { setMaterials((await api.listMaterials()) as Material[]); setMatError(""); }
      catch (e) { setMatError((e as Error).message); }
    }
  };

  const toggle = async (id: string) => {
    if (expanded === id) { setExpanded(null); setDetail(null); return; }
    setExpanded(id);
    if (tab === "resumes") setDetail(await api.getResume(id));
    else if (tab === "jobs") setDetail(await api.getJob(id));
    else setDetail(await api.getMaterial(id));
  };

  const createResume = async () => {
    if (!resumeName || !resumeText) return;
    setResumeLoading(true);
    await api.createResume({ name: resumeName, raw_text: resumeText });
    setResumeName(""); setResumeText(""); setResumeLoading(false);
    await reload("resumes");
  };

  const createJob = async () => {
    if (!jobName || !jobText) return;
    setJobLoading(true);
    await api.createJob({ name: jobName, company: jobCompany, raw_text: jobText });
    setJobName(""); setJobCompany(""); setJobText(""); setJobLoading(false);
    await reload("jobs");
  };

  const createMaterial = async () => {
    if (!matName || !matText) return;
    setMatLoading(true);
    try { await api.createMaterial({ name: matName, raw_text: matText }); setMatName(""); setMatText(""); await reload("materials"); }
    catch (e) { setMatError((e as Error).message); }
    setMatLoading(false);
  };

  const uploadPdf = async () => {
    if (!pdfFile) return;
    setPdfUploading(true);
    setMatError("");
    try {
      const result = await api.uploadMaterialPdf({
        name: pdfName || pdfFile.name.replace(/\.pdf$/i, ""),
        file: pdfFile,
      });
      setPdfName("");
      setPdfFile(null);
      await reload("materials");
      if (result.embedding_status === "failed") {
        setMatError(result.processing_error || "PDF 处理失败（可能是扫描件，无法提取文本）");
      }
    } catch (e) {
      setMatError((e as Error).message);
    }
    setPdfUploading(false);
  };

  const embeddingTone = (s: string) => {
    if (s === "ready") return "success" as const;
    if (s === "failed") return "danger" as const;
    return "warning" as const;
  };

  return (
    <div>
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-ink mb-1">我的档案</h1>
        <p className="text-sm text-ink-muted">统一管理简历画像、岗位画像与面试参考资料</p>
      </div>

      <Tabs tabs={TABS} active={tab} onChange={(k) => { setTab(k); setExpanded(null); setDetail(null); }} className="mb-6" />

      {/* ==================== RESUMES ==================== */}
      {tab === "resumes" && (
        <div className="animate-fade-in space-y-6">
          <Card>
            <Input label="画像名称" placeholder="如：张三-后端工程师" value={resumeName}
              onChange={(e) => setResumeName(e.target.value)} className="mb-4" />
            <Textarea label="简历文本" placeholder="粘贴简历全文..." rows={5} value={resumeText}
              onChange={(e) => setResumeText(e.target.value)} className="mb-4" />
            <Button loading={resumeLoading} disabled={!resumeName || !resumeText} onClick={createResume}>
              创建简历画像
            </Button>
          </Card>

          <ExpandableList items={resumes} emptyText="暂无简历画像，在上方创建第一个"
            expanded={expanded} detail={detail} onToggle={toggle}
            renderSummary={(r) => <span className="font-medium text-sm">{r.name}</span>}
            renderDetail={(_, d: Resume) => (
              <div className="space-y-4">
                <div>
                  <h3 className="text-xs font-semibold text-ink-faint mb-1">摘要</h3>
                  <p className="text-sm text-ink-muted">{d.summary_json?.summary || "暂无摘要"}</p>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-ink-faint mb-2">技能矩阵</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(d.skills_json || {}).flatMap(([group, skills]) =>
                      skills.map((skill) => <Badge key={`${group}-${skill}`}>{group}: {skill}</Badge>)
                    )}
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-ink-faint mb-2">潜在追问</h3>
                  <ul className="space-y-1 text-sm text-ink-muted">
                    {(d.potential_questions_json || []).map((q, i) => (
                      <li key={i} className="flex gap-2"><span className="text-accent-muted shrink-0">—</span> {q}</li>
                    ))}
                  </ul>
                </div>
                <details>
                  <summary className="text-xs text-ink-faint cursor-pointer hover:text-ink-muted">原始文本</summary>
                  <pre className="mt-2 text-xs text-ink-muted whitespace-pre-wrap font-mono bg-surface-raised rounded-lg p-3 max-h-48 overflow-y-auto">{d.raw_text}</pre>
                </details>
              </div>
            )}
          />
        </div>
      )}

      {/* ==================== JOBS ==================== */}
      {tab === "jobs" && (
        <div className="animate-fade-in space-y-6">
          <Card>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <Input label="岗位名称" placeholder="如：高级后端工程师" value={jobName} onChange={(e) => setJobName(e.target.value)} />
              <Input label="公司名称" placeholder="可选" value={jobCompany} onChange={(e) => setJobCompany(e.target.value)} />
            </div>
            <Textarea label="JD 文本" placeholder="粘贴职位描述全文..." rows={5} value={jobText}
              onChange={(e) => setJobText(e.target.value)} className="mb-4" />
            <Button loading={jobLoading} disabled={!jobName || !jobText} onClick={createJob}>
              创建岗位画像
            </Button>
          </Card>

          <ExpandableList items={jobs} emptyText="暂无岗位画像，在上方创建第一个"
            expanded={expanded} detail={detail} onToggle={toggle}
            renderSummary={(j) => (
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">{j.name}</span>
                {j.company && <Badge>{j.company}</Badge>}
              </div>
            )}
            renderDetail={(_, d: Job) => (
              <div className="space-y-4">
                <div className="flex gap-2">
                  {d.domain && <Badge tone="accent">{d.domain}</Badge>}
                  {d.level && <Badge>{d.level}</Badge>}
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-ink-faint mb-1">摘要</h3>
                  <p className="text-sm text-ink-muted">{d.summary_json?.summary || "暂无摘要"}</p>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-ink-faint mb-2">核心要求</h3>
                  <ul className="space-y-1 text-sm text-ink-muted">
                    {(d.must_have_skills_json || []).map((skill, i) => (
                      <li key={i} className="flex gap-2"><span className="text-accent shrink-0">—</span> {skill}</li>
                    ))}
                  </ul>
                </div>
                <details>
                  <summary className="text-xs text-ink-faint cursor-pointer hover:text-ink-muted">原始文本</summary>
                  <pre className="mt-2 text-xs text-ink-muted whitespace-pre-wrap font-mono bg-surface-raised rounded-lg p-3 max-h-48 overflow-y-auto">{d.raw_text}</pre>
                </details>
              </div>
            )}
          />
        </div>
      )}

      {/* ==================== MATERIALS ==================== */}
      {tab === "materials" && (
        <div className="animate-fade-in space-y-6">
          {matError && (
            <div className="rounded-xl border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
              {matError}
            </div>
          )}

          <Card>
            <h3 className="text-sm font-semibold text-ink mb-4">上传 PDF 资料</h3>
            <Input
              label="资料名称"
              placeholder="可留空，默认使用文件名"
              value={pdfName}
              onChange={(e) => setPdfName(e.target.value)}
              className="mb-3"
            />
            <label className="block text-xs font-medium text-ink-muted mb-1.5">PDF 文件</label>
            <input
              className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm text-ink-muted file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-accent file:text-white cursor-pointer mb-4"
              type="file"
              accept="application/pdf,.pdf"
              onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
            />
            {pdfFile && (
              <p className="text-xs text-ink-faint mb-3">已选择：{pdfFile.name}</p>
            )}
            <Button variant="secondary" loading={pdfUploading} disabled={!pdfFile} onClick={uploadPdf}>
              上传 PDF
            </Button>
          </Card>

          <Card>
            <h3 className="text-sm font-semibold text-ink mb-4">创建 Markdown 资料</h3>
            <Input label="资料名称" placeholder="如：Redis 面试题集" value={matName}
              onChange={(e) => setMatName(e.target.value)} className="mb-4" />
            <Textarea label="Markdown 内容" placeholder="粘贴 Markdown 格式的参考资料..." rows={6} value={matText}
              onChange={(e) => setMatText(e.target.value)} className="mb-4" />
            <Button loading={matLoading} disabled={!matName || !matText} onClick={createMaterial}>
              创建资料
            </Button>
          </Card>

          <ExpandableList items={materials} emptyText="暂无面试资料，在上方创建第一个"
            expanded={expanded} detail={detail} onToggle={toggle}
            renderSummary={(m) => (
              <div className="flex items-center gap-2 flex-wrap min-w-0">
                <span className="font-medium text-sm">{m.name}</span>
                <Badge>{m.type}</Badge>
                <Badge>{m.chunk_count} chunks</Badge>
                <Badge tone={embeddingTone(m.embedding_status)}>{m.embedding_status}</Badge>
              </div>
            )}
            renderDetail={(_, d: Material) => (
              <div>
                <div className="flex flex-wrap gap-3 text-xs text-ink-faint mb-3">
                  <span>Chunks: {d.chunk_count}</span>
                  {d.source_file_path && <span>Source: {d.source_file_path}</span>}
                </div>
                {d.processing_error && (
                  <div className="mb-3 rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
                    {d.processing_error}
                  </div>
                )}
                <details>
                  <summary className="text-xs text-ink-faint cursor-pointer hover:text-ink-muted">原始文本</summary>
                  <pre className="mt-2 text-xs text-ink-muted whitespace-pre-wrap font-mono bg-surface-raised rounded-lg p-3 max-h-64 overflow-y-auto">{d.raw_text}</pre>
                </details>
              </div>
            )}
          />
        </div>
      )}
    </div>
  );
}
