use std::fs;
use std::path::{Path, PathBuf};
use serde_json;
use uuid::Uuid;
use chrono::Utc;

use super::types::*;
use crate::fountain::dialect::PaperSize;

pub struct ProjectManager;

impl ProjectManager {
    pub fn create_project(
        folder: &str,
        title: &str,
        author: &str,
        format_id: &str,
        paper: PaperSize,
        kind: ProjectKind,
    ) -> Result<ProjectMeta, String> {
        let id = Uuid::new_v4().to_string();
        let safe_title = title
            .chars()
            .filter(|c| c.is_alphanumeric() || *c == ' ' || *c == '-' || *c == '_')
            .collect::<String>();
        let project_dir = PathBuf::from(folder).join(&safe_title);

        fs::create_dir_all(&project_dir).map_err(|e| e.to_string())?;
        fs::create_dir_all(project_dir.join("plan")).map_err(|e| e.to_string())?;

        let sample_heading = match format_id {
            "fountain+comic-full" | "fountain+comic-plot" | "fountain+comic-lean" | "fountain+comic-gn" => {
                format!("Title: {}\nCredit: Written by\nAuthor: {}\n\n# PAGE ONE\n\n.PANEL 1\n\nEstablishing shot.\n", title, author)
            }
            _ => {
                format!("Title: {}\nCredit: Written by\nAuthor: {}\n\nINT. LOCATION — DAY\n\nAction goes here.\n", title, author)
            }
        };

        fs::write(project_dir.join("script.fountain"), &sample_heading).map_err(|e| e.to_string())?;

        let logline_content = String::new();
        fs::write(project_dir.join("plan").join("logline.md"), &logline_content).map_err(|e| e.to_string())?;
        fs::write(project_dir.join("plan").join("synopsis.md"), "").map_err(|e| e.to_string())?;
        fs::write(project_dir.join("plan").join("pitch.md"), "").map_err(|e| e.to_string())?;
        fs::write(project_dir.join("plan").join("treatment.md"), "").map_err(|e| e.to_string())?;

        let characters: Vec<CharacterData> = Vec::new();
        fs::write(
            project_dir.join("characters.json"),
            serde_json::to_string_pretty(&characters).unwrap(),
        ).map_err(|e| e.to_string())?;

        let graph_nodes: Vec<GraphNode> = Vec::new();
        fs::write(
            project_dir.join("graph.json"),
            serde_json::to_string_pretty(&graph_nodes).unwrap(),
        ).map_err(|e| e.to_string())?;

        let cover = CoverData {
            title: title.to_string(),
            byline: format!("Written by\n{}", author),
            based_on: None,
            draft: Some("First Draft".into()),
            contact: None,
            copyright: None,
            show_cover: true,
        };
        fs::write(
            project_dir.join("cover.json"),
            serde_json::to_string_pretty(&cover).unwrap(),
        ).map_err(|e| e.to_string())?;

        let now = Utc::now().to_rfc3339();
        let meta = ProjectMeta {
            id,
            title: title.to_string(),
            author: author.to_string(),
            format_id: format_id.to_string(),
            paper,
            created_at: now.clone(),
            modified_at: now,
            path: project_dir.to_string_lossy().to_string(),
            kind,
        };

        fs::write(
            project_dir.join("project.json"),
            serde_json::to_string_pretty(&meta).unwrap(),
        ).map_err(|e| e.to_string())?;

        Ok(meta)
    }

    pub fn open_project(path: &str) -> Result<ProjectData, String> {
        let dir = Path::new(path);
        if !dir.exists() {
            return Err("Project directory not found".into());
        }

        let meta_path = dir.join("project.json");
        let meta: ProjectMeta = if meta_path.exists() {
            let data = fs::read_to_string(&meta_path).map_err(|e| e.to_string())?;
            serde_json::from_str(&data).map_err(|e| e.to_string())?
        } else {
            return Err("No project.json found".into());
        };

        let script = fs::read_to_string(dir.join("script.fountain")).unwrap_or_default();

        let characters: Vec<CharacterData> = fs::read_to_string(dir.join("characters.json"))
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default();

        let graph_nodes: Vec<GraphNode> = fs::read_to_string(dir.join("graph.json"))
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default();

        let cover: CoverData = fs::read_to_string(dir.join("cover.json"))
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_else(|| CoverData {
                title: meta.title.clone(),
                byline: format!("Written by\n{}", meta.author),
                based_on: None,
                draft: None,
                contact: None,
                copyright: None,
                show_cover: true,
            });

        let plan_dir = dir.join("plan");
        let mut plan_documents = Vec::new();
        let plan_files = [
            ("logline", "Logline"),
            ("synopsis", "Synopsis"),
            ("pitch", "One-page pitch"),
            ("treatment", "Treatment"),
        ];
        for (file, title) in &plan_files {
            let content = fs::read_to_string(plan_dir.join(format!("{}.md", file))).unwrap_or_default();
            let wc = content.split_whitespace().count() as u32;
            plan_documents.push(PlanDocument {
                id: file.to_string(),
                title: title.to_string(),
                content,
                word_count: wc,
            });
        }

        Ok(ProjectData {
            meta,
            script,
            plan_documents,
            characters,
            graph_nodes,
            cover,
        })
    }

    pub fn save_script(path: &str, content: &str) -> Result<(), String> {
        let dir = Path::new(path);
        fs::write(dir.join("script.fountain"), content).map_err(|e| e.to_string())?;

        let meta_path = dir.join("project.json");
        if let Ok(data) = fs::read_to_string(&meta_path) {
            if let Ok(mut meta) = serde_json::from_str::<ProjectMeta>(&data) {
                meta.modified_at = Utc::now().to_rfc3339();
                let _ = fs::write(&meta_path, serde_json::to_string_pretty(&meta).unwrap());
            }
        }
        Ok(())
    }

    pub fn list_projects(folder: &str) -> Result<Vec<ProjectMeta>, String> {
        let dir = Path::new(folder);
        if !dir.exists() {
            return Ok(Vec::new());
        }

        let mut projects = Vec::new();
        let entries = fs::read_dir(dir).map_err(|e| e.to_string())?;
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                let meta_path = path.join("project.json");
                if let Ok(data) = fs::read_to_string(&meta_path) {
                    if let Ok(meta) = serde_json::from_str::<ProjectMeta>(&data) {
                        projects.push(meta);
                    }
                }
            }
        }

        projects.sort_by(|a, b| b.modified_at.cmp(&a.modified_at));
        Ok(projects)
    }

    pub fn save_characters(path: &str, characters: &[CharacterData]) -> Result<(), String> {
        let dir = Path::new(path);
        fs::write(
            dir.join("characters.json"),
            serde_json::to_string_pretty(characters).unwrap(),
        ).map_err(|e| e.to_string())
    }

    pub fn save_graph(path: &str, nodes: &[GraphNode]) -> Result<(), String> {
        let dir = Path::new(path);
        fs::write(
            dir.join("graph.json"),
            serde_json::to_string_pretty(nodes).unwrap(),
        ).map_err(|e| e.to_string())
    }

    pub fn save_cover(path: &str, cover: &CoverData) -> Result<(), String> {
        let dir = Path::new(path);
        fs::write(
            dir.join("cover.json"),
            serde_json::to_string_pretty(cover).unwrap(),
        ).map_err(|e| e.to_string())
    }

    pub fn save_plan_document(path: &str, doc_id: &str, content: &str) -> Result<(), String> {
        let dir = Path::new(path).join("plan");
        fs::write(dir.join(format!("{}.md", doc_id)), content).map_err(|e| e.to_string())
    }
}
