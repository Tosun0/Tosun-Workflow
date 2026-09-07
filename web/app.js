const state = { files: [], projects: [] };
const stageOrder = ["analysis", "prompts", "thumbnail", "video", "infographic", "publish"];
const stageLabels = {
  analysis: "스토리보드 해석",
  prompts: "프롬프트 제작",
  thumbnail: "썸네일",
  video: "Higgsfield 영상",
  infographic: "Remotion 인포그래픽",
  publish: "최종 공개"
};

const $ = (selector) => document.querySelector(selector);
const toast = (message, error = false) => {
  const node = $("#toast");
  node.textContent = message;
  node.style.background = error ? "#ff8d8d" : "#edf3f8";
  node.classList.add("show");
  window.setTimeout(() => node.classList.remove("show"), 2600);
};

$("#help-button").addEventListener("click", () => $("#help-dialog").showModal());
$("#close-help").addEventListener("click", () => $("#help-dialog").close());

async function request(url, options = {}) {
  const response = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "요청 실패");
  return data;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function renderFiles() {
  const node = $("#file-list");
  if (!state.files.length) {
    node.innerHTML = '<div class="empty">inbox에 지원 파일을 넣으면 여기에 표시됩니다.</div>';
    return;
  }
  node.innerHTML = state.files.map((file, index) => `
    <label class="file-row">
      <input type="checkbox" data-file-index="${index}" ${file.is_input ? "" : "disabled"}>
      <div class="file-meta">
        <div class="file-name">${escapeHtml(file.name)}</div>
        <div class="file-detail">${escapeHtml(file.path)} · ${formatBytes(file.size)}</div>
      </div>
      <span class="badge">${escapeHtml(file.role)}</span>
    </label>`).join("");
}

function renderProjects() {
  const node = $("#project-list");
  if (!state.projects.length) {
    node.innerHTML = '<div class="empty">프로젝트를 만들면 진행 상태가 표시됩니다.</div>';
    return;
  }
  node.innerHTML = state.projects.map(project => {
    const stages = project.stages || {};
    const current = project.current_stage;
    const currentState = stages[current]?.status || "blocked";
    const canRun = ["ready", "waiting_external"].includes(currentState);
    const canApprove = ["waiting_approval", "waiting_external", "completed"].includes(currentState);
    return `<article class="project-card">
      <div class="project-title">${escapeHtml(project.title)}</div>
      <div class="project-id">${escapeHtml(project.project_id)} · 현재 단계: ${escapeHtml(stageLabels[current] || current)}</div>
      <div class="timeline">${stageOrder.map(stage => {
        const status = stages[stage]?.status || "blocked";
        return `<div class="stage ${status}"><span class="stage-name">${stageLabels[stage]}</span><span class="stage-status">${status}</span></div>`;
      }).join("")}</div>
      <div class="actions">
        <button class="run" data-action="run" data-project="${project.project_id}" data-stage="${current}" ${canRun ? "" : "disabled"}>현재 단계 실행</button>
        <button class="approve" data-action="approve" data-project="${project.project_id}" data-stage="${current}" ${canApprove ? "" : "disabled"}>승인하고 다음 단계</button>
        <button class="ghost" data-action="backup" data-project="${project.project_id}">백업</button>
      </div>
      <div class="project-note">마지막 갱신: ${escapeHtml(project.updated_at || "-")} · 공개 파일: ${(project.public_files || []).length}개</div>
    </article>`;
  }).join("");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

async function refresh() {
  const [health, files, projects] = await Promise.all([
    request("/api/health"), request("/api/files"), request("/api/projects")
  ]);
  $("#health").textContent = health.ok ? "로컬 엔진 연결됨" : "엔진 확인 필요";
  state.files = files.files;
  state.projects = projects.projects;
  renderFiles();
  renderProjects();
}

$("#refresh-files").addEventListener("click", () => refresh().catch(error => toast(error.message, true)));
$("#refresh-projects").addEventListener("click", () => refresh().catch(error => toast(error.message, true)));
$("#create-project").addEventListener("click", async () => {
  const title = $("#project-title").value.trim();
  const inputPaths = [...document.querySelectorAll("input[data-file-index]:checked")].map(node => state.files[Number(node.dataset.fileIndex)].path);
  if (!title || !inputPaths.length) return toast("프로젝트 이름과 입력 파일을 선택하세요.", true);
  try {
    await request("/api/projects", { method: "POST", body: JSON.stringify({ title, input_paths: inputPaths }) });
    $("#project-title").value = "";
    toast("프로젝트를 만들었습니다.");
    await refresh();
  } catch (error) { toast(error.message, true); }
});

$("#project-list").addEventListener("click", async event => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const project = button.dataset.project;
  try {
    if (button.dataset.action === "run") {
      await request(`/api/projects/${project}/run`, { method: "POST", body: JSON.stringify({ stage: button.dataset.stage }) });
      toast("단계를 실행했습니다.");
    }
    if (button.dataset.action === "approve") {
      const note = window.prompt("승인 메모를 입력하세요.", "승인") || "승인";
      await request(`/api/projects/${project}/approve`, { method: "POST", body: JSON.stringify({ stage: button.dataset.stage, note }) });
      toast("승인했습니다. 다음 단계가 열렸습니다.");
    }
    if (button.dataset.action === "backup") {
      await request(`/api/projects/${project}/backup`, { method: "POST", body: JSON.stringify({ reason: "manual-gui" }) });
      toast("백업을 만들었습니다.");
    }
    await refresh();
  } catch (error) { toast(error.message, true); }
});

refresh().catch(error => { $("#health").textContent = "연결 실패"; toast(error.message, true); });
