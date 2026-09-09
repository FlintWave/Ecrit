use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type")]
pub enum Element {
    TitlePage { pairs: Vec<TitlePagePair> },
    SceneHeading { text: String, scene_number: Option<String>, forced: bool },
    Action { text: String, centered: bool, forced: bool },
    Character { name: String, extension: Option<String>, dual: bool, forced: bool },
    Dialogue { text: String },
    Parenthetical { text: String },
    Transition { text: String, forced: bool },
    Lyric { text: String },
    Section { level: u8, text: String },
    Synopsis { text: String },
    Note { text: String },
    Boneyard { text: String },
    PageBreak,
    BlankLine,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TitlePagePair {
    pub key: String,
    pub value: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FountainDocument {
    pub elements: Vec<Element>,
    pub title_page: Option<TitlePage>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TitlePage {
    pub title: Option<String>,
    pub credit: Option<String>,
    pub author: Option<String>,
    pub source: Option<String>,
    pub draft_date: Option<String>,
    pub contact: Option<String>,
    pub copyright: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SceneInfo {
    pub index: usize,
    pub number: Option<String>,
    pub heading: String,
    pub page: u32,
    pub word_count: u32,
    pub character_names: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CharacterInfo {
    pub name: String,
    pub line_count: u32,
    pub word_count: u32,
    pub scenes: Vec<usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScriptStats {
    pub page_count: u32,
    pub word_count: u32,
    pub scene_count: u32,
    pub character_count: u32,
    pub dialogue_percentage: f32,
    pub action_percentage: f32,
    pub characters: Vec<CharacterInfo>,
    pub scenes: Vec<SceneInfo>,
}
