use serde::{Deserialize, Serialize};
use crate::fountain::dialect::PaperSize;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectMeta {
    pub id: String,
    pub title: String,
    pub author: String,
    pub format_id: String,
    pub paper: PaperSize,
    pub created_at: String,
    pub modified_at: String,
    pub path: String,
    pub kind: ProjectKind,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ProjectKind {
    Single,
    Series,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectData {
    pub meta: ProjectMeta,
    pub script: String,
    pub plan_documents: Vec<PlanDocument>,
    pub characters: Vec<CharacterData>,
    pub graph_nodes: Vec<GraphNode>,
    pub cover: CoverData,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlanDocument {
    pub id: String,
    pub title: String,
    pub content: String,
    pub word_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CharacterData {
    pub id: String,
    pub name: String,
    pub age: Option<String>,
    pub pronouns: Option<String>,
    pub occupation: Option<String>,
    pub wants: Option<String>,
    pub needs: Option<String>,
    pub voice_notes: Option<String>,
    pub arc: Option<String>,
    pub relationships: Option<String>,
    pub notes: Option<String>,
    pub role: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphNode {
    pub id: String,
    pub kind: NodeKind,
    pub x: f64,
    pub y: f64,
    pub label: String,
    pub synopsis: Option<String>,
    pub thread: Option<String>,
    pub connections: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum NodeKind {
    ActBreak,
    Scene,
    Transition,
    Note,
    Section,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoverData {
    pub title: String,
    pub byline: String,
    pub based_on: Option<String>,
    pub draft: Option<String>,
    pub contact: Option<String>,
    pub copyright: Option<String>,
    pub show_cover: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub theme: Theme,
    pub language: String,
    pub default_project_folder: String,
    pub reopen_last_project: bool,
    pub auto_snapshot_minutes: u32,
    pub show_daily_target: bool,
    pub daily_target_words: u32,
    pub author_name: String,
    pub author_email: String,
    pub author_contact: String,
    pub script_font: String,
    pub editing_size: f32,
    pub fountain_markup: MarkupMode,
    pub typewriter_scrolling: bool,
    pub autocomplete_names: bool,
    pub smart_quotes: bool,
    pub focus_mode: bool,
    pub show_page_breaks: bool,
    pub rail_side: RailSide,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Theme {
    Light,
    Dark,
    System,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum MarkupMode {
    Shown,
    LiveStyled,
    Hidden,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RailSide {
    Left,
    Right,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            theme: Theme::Dark,
            language: "en".into(),
            default_project_folder: String::new(),
            reopen_last_project: true,
            auto_snapshot_minutes: 5,
            show_daily_target: true,
            daily_target_words: 2500,
            author_name: String::new(),
            author_email: String::new(),
            author_contact: String::new(),
            script_font: "Courier Prime".into(),
            editing_size: 15.0,
            fountain_markup: MarkupMode::LiveStyled,
            typewriter_scrolling: true,
            autocomplete_names: true,
            smart_quotes: true,
            focus_mode: false,
            show_page_breaks: true,
            rail_side: RailSide::Left,
        }
    }
}
